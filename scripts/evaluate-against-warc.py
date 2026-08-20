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


def compare(record_id: str, url: str, html: str, old_metadata: dict):
    new_metadata = mcmetadata.extract(url, html)
    new_metadata["publication_date"] = str(new_metadata["publication_date"].date())
    for key, value in old_metadata.items():
        if key == "parsed_date":
            continue
        if key not in new_metadata:
            raise Exception(f"{record_id}: '{key}' not in metadata")
        if new_metadata[key] != value:
            raise Exception(f"{record_id}: '{key}' {value} != {new_metadata[key]}")


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
                        logger.error(f"{record_id}: fail {e}")
                        fail_count += 1
                    logger.info(f"{record_id}: pass")
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
        description="Evaluate metadata extraction against a WARC file."
    )
    parser.add_argument(
        "warc_path", help="Path to the WARC file (handles .warc.gz or .warc)"
    )
    args = parser.parse_args()

    warc_path = args.warc_path
    if warc_path.endswith(".gz"):
        with tempfile.NamedTemporaryFile(suffix=".warc", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with gzip.open(warc_path, "rb") as gz_in, open(tmp_path, "wb") as tmp_out:
                shutil.copyfileobj(gz_in, tmp_out)
            evaluate(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        evaluate(warc_path)
