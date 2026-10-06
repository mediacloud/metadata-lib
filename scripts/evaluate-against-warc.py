"""
Internal Media Cloud evaluation utility tool.

This code walks a Media Cloud generated WARC file to compare changes from prior versions of
metadata extraction to new code. It is most helpful for quick reviews and spot checks. The
`compare-to-warc` script is more comprehensive, but this script is maintained here to help with
quick pokes.
"""

import argparse
import gzip
import json
import logging
import os
import shutil
import tempfile

from warcio.archiveiterator import ArchiveIterator

import mcmetadata

logger = logging.getLogger(__name__)

CONTENT_LENGTH_CONCERN_THRESHOLD = 0.2


def _concerning_content_diff(old_content, new_content):
    return abs(len(old_content) - len(new_content)) > (
        len(new_content) * CONTENT_LENGTH_CONCERN_THRESHOLD
    )


def compare(record_id: str, url: str, html: str, old_metadata: dict):
    new_metadata = mcmetadata.extract(url, html)
    # guess_publication_date() legitimately returns None when no date could be found
    pub_date = new_metadata["publication_date"]
    new_metadata["publication_date"] = str(pub_date.date()) if pub_date else None
    for key, value in old_metadata.items():
        # not a concern if now trafilatura works (over readability) prior, unless content is too different
        if key == "text_extraction_method":
            if new_metadata[key] != value:
                # logger.info(f"Old content length = {len(value)}; new length = {len(new_metadata[key])}")
                if _concerning_content_diff(value, new_metadata[key]):
                    raise Exception(
                        f"{record_id}: '{key}' {value} != {new_metadata[key]}"
                    )
            else:
                continue
        # the parsed_date isn't content that is static
        elif key == "parsed_date":
            continue
        # is there some data missing in the new extraction results?
        elif key not in new_metadata:
            raise Exception(f"{record_id}: '{key}' not in metadata")
        # check the test within a reasonable threshold
        elif key == "text_content":
            # logger.info(f"{record_id}: was {len(value)} now {len(new_metadata[key])}")
            if _concerning_content_diff(value, new_metadata[key]):
                if new_metadata["language"] == "en":
                    continue
                raise Exception(
                    f"{record_id}: '{key}' {len(value)} != {len(new_metadata[key])}"
                )
        # just check if the value has changed from what we got before
        else:
            # logger.info(f" {key}: {value} -> {new_metadata[key]}")
            if new_metadata[key] != value:
                raise Exception(
                    f"{record_id}: '{key}' was {value} != now {new_metadata[key]}"
                )


def evaluate(warc_file_path: str, max_records: int = None) -> None:
    logger.info("Evaluating WARC file: %s", warc_file_path)
    fail_count = 0
    pass_count = 0
    with open(warc_file_path, "rb") as stream:
        url = None
        record_id = None
        html_content = None
        records_compared = 0
        for record in ArchiveIterator(stream):
            if record.rec_type == "response" and record_id is None:
                url = record.rec_headers.get_header("WARC-Target-URI")
                record_id = record.rec_headers.get_header("WARC-Record-ID")
                html_content = (
                    record.content_stream().read().decode("utf-8", errors="replace")
                )
            elif record.rec_type == "metadata" and record_id is not None:
                if record.rec_headers.get_header("WARC-Refers-To") == record_id:
                    metadata_record = record
                    # logger.info(f"found match for {record_id}")
                    metadata_content = (
                        metadata_record.content_stream()
                        .read()
                        .decode("utf-8", errors="replace")
                    )
                    metadata = json.loads(metadata_content)
                    try:
                        compare(
                            record_id, url, html_content, metadata["content_metadata"]
                        )
                        pass_count += 1
                    except Exception as e:
                        logger.error(f"fail {e}")
                        fail_count += 1
                    # logger.info(f"{record_id}: pass")
                    records_compared += 1
                    url = None
                    record_id = None
                    html_content = None
                    if max_records and (records_compared >= max_records):
                        logger.info(f"stopping at {max_records} records")
                        return
    logger.info(
        f"Done with {fail_count} fails and {pass_count} passes ({fail_count + pass_count} total stories)"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Evaluate metadata extraction against a WARC file.",
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
    args = parser.parse_args()

    warc_path = args.warc_path
    if warc_path.endswith(".gz"):
        with tempfile.NamedTemporaryFile(suffix=".warc", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with gzip.open(warc_path, "rb") as gz_in, open(tmp_path, "wb") as tmp_out:
                shutil.copyfileobj(gz_in, tmp_out)
            evaluate(tmp_path, args.max_records)
        finally:
            os.unlink(tmp_path)
    else:
        evaluate(warc_path, args.max_records)
