import unittest
import datetime as dt

from .. import dates
from .. import webpages


class TestDates(unittest.TestCase):

    def test_date_subhead(self):
        u = "https://www.sun-sentinel.com/community/fl-cn-calendar-events-20211201-20211129-sv3syeeuwzeallnr4vcanvaeti-story.html"
        raw_html, response = webpages.fetch(u)
        pub_date = dates.guess_publication_date(raw_html, u)
        assert pub_date.date() == dt.date(2021, 11, 29)

    def test_date_in_url(self):
        url = "https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"
        raw_html, response = webpages.fetch(url)
        pub_date = dates.guess_publication_date(raw_html, url)
        assert pub_date.date() == dt.date(2021, 4, 30)

    def test_date_in_meta_tags(self):
        url = "https://www.foxnews.com/politics/biden-cancel-school-loans-corinthian-college-students"
        raw_html, response = webpages.fetch(url)
        pub_date = dates.guess_publication_date(raw_html, url)
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
            date = dates.guess_publication_date(raw_html, u)
            assert date is None

    def test_day_month_year(self):
        u = "https://www.eeas.europa.eu/eeas/eu-world-0_en"
        raw_html, response = webpages.fetch(u)
        date = dates.guess_publication_date(raw_html, u)
        assert date.date() == dt.date(2022, 3, 30)

    def test_no_date(self):
        u = "http://archive.org"
        raw_html, response = webpages.fetch(u)
        date = dates.guess_publication_date(raw_html, u)
        assert date is None

    def test_max_date(self):
        u = "https://www.canarias7.es/cultura/cimientos-artes-escenicas-20220718203045-nt.html"
        raw_html, response = webpages.fetch(u)
        date = dates.guess_publication_date(raw_html, u)
        assert date.date() == dt.date(2022, 7, 17)
        date = dates.guess_publication_date(raw_html, u, max_date=dt.datetime(2020, 1, 1))
        assert date is None

