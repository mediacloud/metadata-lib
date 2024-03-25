import unittest

import pytest

from .. import content, languages, webpages
from . import filesafe_url, read_fixture


@pytest.fixture
def use_cache(request):
    return request.config.getoption('--use-cache')


class TestLanguageFromText(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def get_use_cache(self, use_cache):
        self.use_cache = use_cache

    def _fetch_and_validate(self, url: str, expected_language_code: str):
        if self.use_cache:
            try:
                html_text = read_fixture(filesafe_url(url))
            except Exception:
                html_text, _ = webpages.fetch(url)
        else:
            html_text, _ = webpages.fetch(url)
        article = content.from_html(url, html_text)
        lang_code = languages._from_text(article['text'])
        assert lang_code == expected_language_code

    def test_india_times(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.indiatimes.com/explainers/news/united-nations-climate-report-means-for-india-wet-bulb-temperature-563318.html",
            "en"
        )

    def test_corriere_della_sera(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.corriere.it/esteri/22_marzo_07/bombe-ucraine-donbass-soldati-russi-azioni-umanitarie-mondo-parallelo-mosca-176a20ea-9e41-11ec-aa45-e6507f140451.shtml",
            "it"
        )

    def test_urdu(self):
        self._fetch_and_validate("https://web.archive.org/web/https://naibaat.pk/amp/2022/04/08/49027/", "ur")

    def test_hindi(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://hindi.oneindia.com/amphtml/news/india/aam-aadmi-party-reaction-on-amit-shah-statement-on-corona-case-in-delhi-567287.html",
            "hi"
        )

    def test_korean_failure(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.mk.co.kr/news/society/view/2020/07/693939/", "ko"
        )

    def test_language_without_region(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm",
            "pt"
        )


class TestLanguageFromHtml(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def get_use_cache(self, use_cache):
        self.use_cache = use_cache

    def _fetch_and_validate(self, url: str, expected_language_code: str):
        if self.use_cache:
            try:
                html_text = read_fixture(filesafe_url(url))
            except Exception:
                html_text, _ = webpages.fetch(url)
        else:
            html_text, _ = webpages.fetch(url)
        article = content.from_html(url, html_text)
        lang_code = languages.from_html(html_text, article['text'])
        assert lang_code == expected_language_code

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
        # encoding is wrong, content is actually 'ko'
        self._fetch_and_validate(
            "https://www.mk.co.kr/news/society/view/2020/07/693939/", "ko"
        )

    def test_language_without_region(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm",
            "pt-br"
        )

    def test_chinese_example(self):
        # webpage says 'en', but actually content is 'zh'
        self._fetch_and_validate("https://web.archive.org/web/http://world.huanqiu.com/hot/2016-08/9334639.html", "zh")

    def test_mixed(self):
        # content is in both 'DE' and 'EN'... but more is in EN
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.finanznachrichten.de/nachrichten-2016-08/38189388-bittium-oyj-bittium-corporation-s-half-year-financial-report-january-june-2016-004.htm",
            "en"
        )

    def test_spanish(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.sdpnoticias.com/enelshow/musica/integrante-queda-u-t-t.html",
            "es"
        )

    def test_albanian(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/http://telegraf.al/bota-rajoni/mancester-sulm-i-tmerrshem-plagosen-pese-persona/",
            "sq"
        )

    def test_russian_blog(self):
        self._fetch_and_validate("https://web.archive.org/web/http://aptsvet.livejournal.com/", "ru")


class TestLangaugePicking(unittest.TestCase):

    def test_more_specific(self):
        assert languages._pick_between_languages('pt-br', 'pt') == 'pt-br'

    def test_prefer_detected(self):
        assert languages._pick_between_languages('en', 'zh') == 'zh'

    def test_same(self):
        assert languages._pick_between_languages('es', 'es') == 'es'

    def test_missing(self):
        assert languages._pick_between_languages(None, 'zh') == 'zh'
        assert languages._pick_between_languages('zh', None) == 'zh'
        assert languages._pick_between_languages(None, None) is None


if __name__ == "__main__":
    unittest.main()
