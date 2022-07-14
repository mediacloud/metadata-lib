import unittest
import datetime as dt

from .. import _parse_pub_date
from .. import webpages


class TestParsePubDate(unittest.TestCase):

    def test_date_subhead(self):
        u = "https://www.sun-sentinel.com/community/fl-cn-calendar-events-20211201-20211129-sv3syeeuwzeallnr4vcanvaeti-story.html"
        raw_html, response = webpages.fetch(u)
        pub_date = _parse_pub_date(raw_html, u)
        assert pub_date.date() == dt.date(2021, 11, 29)

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

    def test_ignore_footer_copyright(self):
        urls = [
            "https://www.alliedmarketresearch.com/cytogenetics-market",
            "https://www.bakerbotts.com/footer/subscribe",
            "https://www.kingjamesbibleonline.org/1-Chronicles-Chapter-1/",
            "https://www.womblebonddickinson.com/us/people-search"
        ]
        for u in urls:
            raw_html, response = webpages.fetch(u)
            date = _parse_pub_date(raw_html, u)
            assert date is None

    def test_day_month_year(self):
        u = "https://www.eeas.europa.eu/eeas/eu-world-0_en"
        raw_html, response = webpages.fetch(u)
        date = _parse_pub_date(raw_html, u)
        assert date.date() == dt.date(2022, 3, 30)

    def test_no_date(self):
        u = "http://archive.org"
        raw_html, response = webpages.fetch(u)
        date = _parse_pub_date(raw_html, u)
        assert date is None
