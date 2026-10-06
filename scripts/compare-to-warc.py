"""
Internal Media Cloud evaluation utility tool.

This code generates a before/after comparison data for qualitative review of metadata extraction
changes (particularly `text_content` after a trafilatura upgrade) against a previously-processed
Media Cloud generated WARC file.

For each story in the WARC file, this pulls out the metadata that was recorded when the WARC was
generated (the "old" result) and re-runs the current `mcmetadata` code against the same HTML (the
"new" result). A word-level diff and similarity score between old and new `text_content` is
computed here (via difflib) and written out alongside the metadata, so the browser only has to
render precomputed data - no diffing happens client-side.

This writes a self-contained static site into the output directory: per-doc JSON files under
data/, a data/docs.json manifest, a data/meta.json with the source WARC filename, and a copy of
the index.html + compare.js template from scripts/comparison_template/.

Usage:
    python scripts/compare-to-warc.py <warc_path> <max_records> [--output-dir DIR]

By default the output directory is named after the input WARC file, eg.
comparison-results-2026_07_15_mc-20260715030208-9297-293ea08c3985 (use 0 for max_records to
process every record in the file).

Then serve the output directory over HTTP (fetch() won't work from a file:// URL) and open it in a
browser, eg.:
    cd comparison-results && python -m http.server 8000
"""

import argparse
import difflib
import gzip
import json
import logging
import os
import re
import shutil
import tempfile
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from warcio.archiveiterator import ArchiveIterator

import mcmetadata
from mcmetadata.urls import unique_url_hash

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "comparison_template"
)
TOKEN_RE = re.compile(r"(\s+)")

# above this many combined word-tokens, a full opcode-level diff isn't worth the cost (or the
# scroll), so fall back to a fast approximate similarity ratio and let the UI show raw text instead
DIFF_TOKEN_LIMIT = 20000

# fields that differ because of library/pipeline versioning, not extraction quality - excluded
# from the per-field success/error summary and the field-error filter, same as the UI's yellow
# "warning" highlighting
WARNING_KEYS = {"parsed_date", "unique_url_hash", "version"}
SUMMARY_SKIP_KEYS = WARNING_KEYS | {"text_content", "error"}


def _field_diffs(old_metadata: Dict, new_metadata: Dict) -> List[str]:
    """Regular (non-warning, non-text) fields where old and new metadata disagree."""
    fields = (set(old_metadata) | set(new_metadata)) - SUMMARY_SKIP_KEYS
    return sorted(f for f in fields if old_metadata.get(f) != new_metadata.get(f))


def _similarity_bucket(similarity: float) -> int:
    return min(9, int(similarity * 100) // 10)


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return str(value)
    raise TypeError(f"Object of type {type(value)} is not JSON serializable")


def _write_json(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=_json_default)


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t for t in TOKEN_RE.split(text) if t]


def _text_comparison(old_text: str, new_text: str) -> Dict:
    old_tokens = _tokenize(old_text)
    new_tokens = _tokenize(new_text)

    if len(old_tokens) + len(new_tokens) > DIFF_TOKEN_LIMIT:
        matcher = difflib.SequenceMatcher(None, old_text, new_text, autojunk=False)
        return {"similarity": matcher.quick_ratio(), "truncated": True, "diff": None}

    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
    diff = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            diff.append({"type": "equal", "text": "".join(old_tokens[i1:i2])})
        elif tag == "delete":
            diff.append({"type": "delete", "text": "".join(old_tokens[i1:i2])})
        elif tag == "insert":
            diff.append({"type": "insert", "text": "".join(new_tokens[j1:j2])})
        elif tag == "replace":
            diff.append({"type": "delete", "text": "".join(old_tokens[i1:i2])})
            diff.append({"type": "insert", "text": "".join(new_tokens[j1:j2])})
    return {"similarity": matcher.ratio(), "truncated": False, "diff": diff}


def _new_metadata_for(url: str, html: str) -> Dict:
    new_metadata = mcmetadata.extract(url, html)
    # guess_publication_date() legitimately returns None when no date could be found
    pub_date = new_metadata["publication_date"]
    new_metadata["publication_date"] = str(pub_date.date()) if pub_date else None
    return new_metadata


def _default_output_dir(warc_path: str) -> str:
    base = os.path.basename(warc_path)
    base = re.sub(r"\.warc(\.gz)?$", "", base)
    return f"comparison-results-{base}"


def process(
    warc_file_path: str,
    output_dir: str,
    max_records: Optional[int] = None,
    source_warc_name: Optional[str] = None,
) -> None:
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    docs: List[Dict] = []
    field_stats: Dict[str, Dict[str, int]] = {}
    similarity_buckets = [0] * 10
    error_docs = 0
    logger.info("Processing WARC file: %s", warc_file_path)
    with open(warc_file_path, "rb") as stream:
        url = None
        record_id = None
        html_content = None
        records_processed = 0
        for record in ArchiveIterator(stream):
            if record.rec_type == "response" and record_id is None:
                url = record.rec_headers.get_header("WARC-Target-URI")
                record_id = record.rec_headers.get_header("WARC-Record-ID")
                html_content = (
                    record.content_stream().read().decode("utf-8", errors="replace")
                )
            elif record.rec_type == "metadata" and record_id is not None:
                if record.rec_headers.get_header("WARC-Refers-To") == record_id:
                    metadata_content = (
                        record.content_stream().read().decode("utf-8", errors="replace")
                    )
                    old_metadata = json.loads(metadata_content)["content_metadata"]
                    # stable, content-derived id (rather than the WARC record's own transient
                    # UUID) so links to a given story stay valid across separate runs of this script
                    doc_id = unique_url_hash(url)

                    error = None
                    text_comparison = None
                    field_errors: List[str] = []
                    try:
                        new_metadata = _new_metadata_for(url, html_content)
                        text_comparison = _text_comparison(
                            old_metadata.get("text_content", ""),
                            new_metadata.get("text_content", ""),
                        )
                        field_errors = _field_diffs(old_metadata, new_metadata)
                        field_error_set = set(field_errors)
                        for field in (
                            set(old_metadata) | set(new_metadata)
                        ) - SUMMARY_SKIP_KEYS:
                            stats = field_stats.setdefault(
                                field, {"success": 0, "error": 0}
                            )
                            stats[
                                "error" if field in field_error_set else "success"
                            ] += 1
                        similarity_buckets[
                            _similarity_bucket(text_comparison["similarity"])
                        ] += 1
                    except Exception as e:
                        logger.error(f"{doc_id}: extraction failed: {e}")
                        error = str(e)
                        new_metadata = {"error": error}
                        error_docs += 1

                    _write_json(
                        os.path.join(data_dir, f"{doc_id}.json"),
                        {
                            "id": doc_id,
                            "url": url,
                            "old": old_metadata,
                            "new": new_metadata,
                            "text_comparison": text_comparison,
                        },
                    )

                    docs.append(
                        {
                            "id": doc_id,
                            "url": url,
                            "title": old_metadata.get("article_title"),
                            "canonical_domain": old_metadata.get("canonical_domain"),
                            "language": old_metadata.get("language"),
                            "error": error,
                            "similarity": (
                                text_comparison["similarity"]
                                if text_comparison
                                else None
                            ),
                            "field_errors": field_errors,
                        }
                    )

                    records_processed += 1
                    if records_processed % 100 == 0:
                        print(".", end="", flush=True)
                    url = None
                    record_id = None
                    html_content = None
                    if max_records and records_processed >= max_records:
                        logger.info(f"stopping at {max_records} records")
                        break

    print()
    _write_json(os.path.join(data_dir, "docs.json"), docs)
    _write_json(
        os.path.join(data_dir, "meta.json"),
        {"source_warc": source_warc_name or os.path.basename(warc_file_path)},
    )
    _write_json(
        os.path.join(data_dir, "summary.json"),
        {
            "total_docs": len(docs),
            "error_docs": error_docs,
            "field_stats": field_stats,
            "similarity_histogram": [
                {"bucket": f"{i * 10}-{i * 10 + 10}%", "count": similarity_buckets[i]}
                for i in range(10)
            ],
        },
    )
    _write_static_assets(output_dir)
    logger.info(f"Wrote comparison data for {len(docs)} stories to {output_dir}")


def _write_static_assets(output_dir: str) -> None:
    shutil.copyfile(
        os.path.join(TEMPLATE_DIR, "index.html"), os.path.join(output_dir, "index.html")
    )
    shutil.copyfile(
        os.path.join(TEMPLATE_DIR, "compare.js"), os.path.join(output_dir, "compare.js")
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # these libraries log expected fallback/failure conditions at ERROR/WARNING level even
    # though mcmetadata handles them internally (falls back to the next extractor) - silence
    # them so real per-doc failures (logged via our own `logger`) aren't lost in the noise
    mcmetadata.ignore_loggers()
    for _noisy_logger in (
        "readability.readability",
        "trafilatura.core",
        "trafilatura.metadata",
        "trafilatura.utils",
        "htmldate.utils",
    ):
        logging.getLogger(_noisy_logger).setLevel(logging.CRITICAL)

    parser = argparse.ArgumentParser(
        description="Generate an old-vs-new metadata comparison site from a WARC file.",
    )
    parser.add_argument(
        "warc_path",
        help="Path to the WARC file (handles .warc.gz or .warc)",
    )
    parser.add_argument(
        "max_records",
        help="A number indicating how many records to check at most",
        default=None,
        type=int,
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write the comparison site + data into "
        "(default: comparison-results-<warc filename>)",
    )
    args = parser.parse_args()

    warc_path = args.warc_path
    source_warc_name = os.path.basename(warc_path)
    output_dir = args.output_dir or _default_output_dir(warc_path)

    if warc_path.endswith(".gz"):
        with tempfile.NamedTemporaryFile(suffix=".warc", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with gzip.open(warc_path, "rb") as gz_in, open(tmp_path, "wb") as tmp_out:
                shutil.copyfileobj(gz_in, tmp_out)
            process(tmp_path, output_dir, args.max_records, source_warc_name)
        finally:
            os.unlink(tmp_path)
    else:
        process(warc_path, output_dir, args.max_records, source_warc_name)
