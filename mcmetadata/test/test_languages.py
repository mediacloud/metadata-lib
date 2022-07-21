import unittest

from .. import content
from .. import webpages
from .. import languages


class TestLanguageFromText(unittest.TestCase):

    @staticmethod
    def _fetch_and_validate(url: str, expected_language_code: str, not_desired_language_code: str = False):
        html_text, _ = webpages.fetch(url)
        article = content.from_html(url, html_text)
        lang_code = languages._from_text(article['text'])
        assert lang_code == expected_language_code
        if not_desired_language_code:
            assert lang_code != not_desired_language_code

    def test_india_times(self):
        self._fetch_and_validate(
            "https://www.indiatimes.com/explainers/news/united-nations-climate-report-means-for-india-wet-bulb-temperature-563318.html",
            "en"
        )

    def test_corriere_della_sera(self):
        self._fetch_and_validate(
            "https://www.corriere.it/esteri/22_marzo_07/bombe-ucraine-donbass-soldati-russi-azioni-umanitarie-mondo-parallelo-mosca-176a20ea-9e41-11ec-aa45-e6507f140451.shtml",
            "it"
        )

    def test_urdu(self):
        self._fetch_and_validate(
            "https://naibaat.pk/amp/2022/04/08/49027/",
            "ur"
        )

    def test_hindi(self):
        self._fetch_and_validate(
            "https://hindi.oneindia.com/amphtml/news/india/aam-aadmi-party-reaction-on-amit-shah-statement-on-corona-case-in-delhi-567287.html",\
            "hi"
        )

    def test_korean_failure(self):
        self._fetch_and_validate(
            "https://www.mk.co.kr/news/society/view/2020/07/693939/", "ko", "qu"
        )

    def test_language_without_region(self):
        self._fetch_and_validate(
            "http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm",
            "pt"
        )


class TestLanguageFromHtml(unittest.TestCase):

    @staticmethod
    def _fetch_and_validate(url: str, expected_language_code: str, not_desired_language_code: str = None):
        html_text, _ = webpages.fetch(url)
        lang_code = languages.from_html(html_text)
        assert lang_code == expected_language_code
        if not_desired_language_code:
            assert lang_code != not_desired_language_code

    def test_meta_tag_pattern1(self):
        sample_str = '<meta NOT_name="dc.language" content="es" />'
        matches = languages.meta_tag_pattern1.search(sample_str)
        assert matches is None
        sample_str = '<meta name="dc.language" content="es" />'
        matches = languages.meta_tag_pattern1.search(sample_str)
        assert matches is not None
        assert matches.group(1) == 'es'

    def test_meta_tag_pattern2(self):
        sample_str = '<meta https-equiv="Content-Language" content="ko"/>'
        matches = languages.meta_tag_pattern2.search(sample_str)
        assert matches is None
        sample_str = '<meta data-rh="true" http-equiv="Content-Language" content="ko"/>'
        matches = languages.meta_tag_pattern2.search(sample_str)
        assert matches is not None
        assert matches.group(1) == 'ko'

    def test_html_tag_pattern(self):
        sample_str = '<html dc:lang="es">'
        matches = languages.html_tag_pattern.search(sample_str)
        assert matches is None
        sample_str = '<html lang="es">'
        matches = languages.html_tag_pattern.search(sample_str)
        assert matches is not None
        assert matches.group(1) == 'es'
        sample_str = '<html xml:lang="es">'
        matches = languages.html_tag_pattern.search(sample_str)
        assert matches is not None
        assert matches.group(1) == 'es'

    def test_korean_failure(self):
        self._fetch_and_validate(
            "https://www.mk.co.kr/news/society/view/2020/07/693939/", "ko", "qu"
        )

    def test_language_without_region(self):
        self._fetch_and_validate(
            "http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm",
            "pt-br"
        )


if __name__ == "__main__":
    unittest.main()
