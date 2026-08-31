import hashlib
import logging
import os
from typing import Tuple

import requests
import requests_mock

import mcmetadata.webpages as webpages

test_dir = os.path.dirname(os.path.realpath(__file__))
fixtures_dir = os.path.join(test_dir, "fixtures")

# mcmetadata.webpages.DEFAULT_TIMEOUT_SECS = 500  # reset to a longer timeout for tests
logger = logging.getLogger(__name__)


def mock_fetch(url: str, headers: dict = None) -> Tuple[str, requests.Response]:
    """
    Loads the cached HTML for `url` from disk and mocks the HTTP request so that
    `webpages.fetch(url)` returns it, exercising the real fetch code path. Falls back to a
    live request on a cache miss.
    """
    if headers is None:
        headers = {}
    cached_file_path = os.path.join(fixtures_dir, cached_url_file_name(url))
    if not os.path.exists(cached_file_path):
        logger.error(f"Cache miss on URL: loading live fetch {url}")
        html_text, response = webpages.fetch(url)
        return html_text
    with open(cached_file_path) as f:
        html_text = f.read()
    with requests_mock.Mocker() as m:
        m.get(url, text=html_text, headers=headers)
        html_text, response = webpages.fetch(url)
    return html_text, response


def cached_url_file_name(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest() + ".html"
