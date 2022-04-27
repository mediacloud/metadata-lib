import unittest

from .. import titles
from .. import webpages
from . import read_fixture


class TestTitle(unittest.TestCase):

    @staticmethod
    def _load_and_validate(fixture_filename: str, expected_title: str):
        html_text = read_fixture(fixture_filename)
        assert titles.from_html(html_text) == expected_title

    @staticmethod
    def _fetch_and_validate(url: str, expected_title: str):
        html_text, _ = webpages.fetch(url)
        assert titles.from_html(html_text) == expected_title

    def test_meta_og_title(self):
        self._fetch_and_validate(
            "https://www.indiatimes.com/explainers/news/united-nations-climate-report-means-for-india-wet-bulb-temperature-563318.html",
            "Explained: What Does The New United Nations &#x27;Alarming&#x27; Climate Report Mean For India?"
        )
        self._fetch_and_validate(
            "https://www.corriere.it/esteri/22_marzo_07/bombe-ucraine-donbass-soldati-russi-azioni-umanitarie-mondo-parallelo-mosca-176a20ea-9e41-11ec-aa45-e6507f140451.shtml",
            "Cosa sanno&#44; davvero&#44; i cittadini russi su quello che sta accadendo in Ucraina&#63;"
        )

    def test_meta_og_title2(self):
        self._load_and_validate("bloomberg-original.html", "Elon Got His Deal")

    def test_title_tag(self):
        self._load_and_validate("bloomberg-no-meta.html", "Elon Got His Deal - Bloomberg")


if __name__ == "__main__":
    unittest.main()
