import time
import unittest

import pytest
import requests

from .. import webpages
from ..exceptions import BadContentError
from . import mock_fetch


class TestFetch(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def slow_down_tests(self):
        yield
        time.sleep(0.5)

    def test_regular_fetch(self):
        url = "https://bostonglobe.com"
        html, response = webpages.fetch(url)
        assert response.status_code == 200
        assert "Boston Globe" in html
        assert response.encoding == "utf-8"

    def test_bad_domain(self):
        try:
            url = "https://123_NO_DOIMAN"
            _, _ = webpages.fetch(url)
            assert False
        except requests.exceptions.ConnectionError:
            assert True

    def test_bad_response(self):
        url = "https://uionline.detma.org/static/glossary.aspx?term=WHYOPTPMTTWOWAIVERRQSTS"
        try:
            _, _ = webpages.fetch(url)  # raises a 403
            assert False
        except RuntimeError:
            assert True

    class TestFinalUrl(unittest.TestCase):

        def test_archived_url(self):
            # properly handle pages at web archives (via memento headers)
            original_url = "https://www.nytimes.com/interactive/2018/12/10/business/location-data-privacy-apps.html"
            test_url = "https://web.archive.org/web/20181210092018/https://www.nytimes.com/interactive/2018/12/10/business/location-data-privacy-apps.html"
            headers = {
                "memento-datetime": "Mon, 10 Dec 2018 09:20:18 GMT",
                "link": f'<{original_url}>; rel="original"',
            }
            raw_html, response = mock_fetch(test_url, headers=headers)
            final_url = webpages.final_url(response)
            # Did it correctly pull the original URL out of the link header because the memento-datetime was there?
            assert final_url == original_url

        def test_memento_without_original_url(self):
            try:
                test_url = "https://web.archive.org/web/20210412063445id_/https://ehp.niehs.nih.gov/action/doUpdateAlertSettings?action=addJournal&journalCode=ehp&referrer=/action/doSearch?ContribAuthorRaw=Davis%2C+Jacquelyn&ContentItemType=research-article&startPage=&ContribRaw=Martin%2C+Denny"
                headers = {
                    "memento-datetime": "Mon, 10 Dec 2018 09:20:18 GMT",
                }
                raw_html, response = mock_fetch(test_url, headers=headers)
                _ = webpages.final_url(
                    response
                )  # should raise BadContentError, since archived but we can't tell from where
                assert False
            except BadContentError:
                assert True


if __name__ == "__main__":
    unittest.main()
