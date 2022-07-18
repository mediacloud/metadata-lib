import unittest
import requests

from .. import webpages


class TestFetch(unittest.TestCase):

    def test_regular_fetch(self):
        url = "https://bostonglobe.com"
        html, response = webpages.fetch(url)
        assert response.status_code == 200
        assert "Boston Globe" in html
        assert response.encoding == "utf-8"

    def test_non_utf8_encoding_fix(self):
        url = "https://www.mk.co.kr/news/society/view/2020/07/693939/"
        html, response = webpages.fetch(url, fix_encoding=False)
        assert response.status_code == 200
        assert response.encoding == "ISO-8859-1"
        assert response.apparent_encoding == "EUC-KR"
        html, response = webpages.fetch(url, fix_encoding=True)
        assert response.status_code == 200
        assert response.encoding == "EUC-KR"
        assert response.apparent_encoding == "EUC-KR"

    def test_bad_domain(self):
        try:
            url = "https://123_NO_DOIMAN"
            _, _ = webpages.fetch(url)
            assert False
        except requests.exceptions.ConnectionError:
            assert True


if __name__ == "__main__":
    unittest.main()
