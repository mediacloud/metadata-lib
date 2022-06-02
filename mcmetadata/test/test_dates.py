import unittest
import datetime as dt

from .. import _parse_pub_date
from .. import webpages


class TestParsePubDate(unittest.TestCase):

    def test_date_in_url(self):
        url = "https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"
        raw_html, response = webpages.fetch(url)
        pub_date = _parse_pub_date(raw_html, url)
        assert pub_date.date() == dt.date(2021, 4, 30)

    def test_date_in_meta_tags(self):
        url = "https://www.foxnews.com/politics/biden-cancel-school-loans-corinthian-college-students"
        raw_html, response = webpages.fetch(url)
        pub_date = _parse_pub_date(raw_html, url)
        assert pub_date.date() == dt.date(2022, 6, 1)

    def test_no_date(self):
        url = "http://archive.org"
        raw_html, response = webpages.fetch(url)
        date = _parse_pub_date(raw_html, url)
        assert date is None
