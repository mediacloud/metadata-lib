import unittest

from .. import title as title
from .. import http as http


class TestTitle(unittest.TestCase):

    @staticmethod
    def _fetch_and_validate(url: str, expected_title: str):
        html_text = http.fetch(url)
        assert title.article_title(html_text) == expected_title

    def test_india_times(self):
        self._fetch_and_validate(
            "https://www.indiatimes.com/explainers/news/united-nations-climate-report-means-for-india-wet-bulb-temperature-563318.html",
            "Explained: What Does The New United Nations &#x27;Alarming&#x27; Climate Report Mean For India?"
        )

    def test_corriere_della_sera(self):
        self._fetch_and_validate(
            "https://www.corriere.it/esteri/22_marzo_07/bombe-ucraine-donbass-soldati-russi-azioni-umanitarie-mondo-parallelo-mosca-176a20ea-9e41-11ec-aa45-e6507f140451.shtml",
            "Cosa sanno&#44; davvero&#44; i cittadini russi su quello che sta accadendo in Ucraina&#63;"
        )


if __name__ == "__main__":
    unittest.main()
