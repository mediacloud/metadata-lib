import hashlib
import logging
import os

import mcmetadata.webpages as webpages

test_dir = os.path.dirname(os.path.realpath(__file__))
fixtures_dir = os.path.join(test_dir, "fixtures")

# mcmetadata.webpages.DEFAULT_TIMEOUT_SECS = 500  # reset to a longer timeout for tests
logger = logging.getLogger(__name__)


def read_fixture(url: str) -> str:
    """
    This wll either load the cached HTML from disk, or run a live request and return HTML
    """
    try:
        cached_file_name = cached_url_file_name(url)
        with open(os.path.join(fixtures_dir, cached_file_name)) as f:
            html_text = f.read()
        return html_text
    except FileNotFoundError:
        logger.error(f"Cache miss on URL: loading live fetch {url}")
        html_text, response = webpages.fetch(url)
        return html_text


def cached_url_file_name(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest() + ".html"
