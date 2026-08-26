import unittest
from typing import Optional

import lxml.html
import requests

from .. import content, webpages
from ..exceptions import BadContentError
from . import mock_fetch


class TestContentMetadata(unittest.TestCase):
    URL = "https://www.nbcnews.com/health/health-news/rfk-jrs-cdc-panel-discuss-covid-vaccine-injuries-upcoming-meeting-rcna260694"
    EXPRECTED_IMG_URL = "https://media-cldnry.s-nbcnews.com/image/upload/t_nbcnews-fp-1200-630,f_auto,q_auto:best/rockcms/2026-02/260225-moderna-covid-vaccine-vl-312p-924ca2.jpg"

    def test_top_image(self):
        html_text, _ = mock_fetch(self.URL)
        meta = content.from_html(self.URL, html_text)
        assert meta["top_image_url"] == self.EXPRECTED_IMG_URL


class TestContentParsers(unittest.TestCase):

    URL = "https://web.archive.org/web/https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"

    def setUp(self) -> None:
        # load the content once and run parsers on exact same HTML
        self.html_content, _ = mock_fetch(self.URL)

    def test_readability(self):
        extractor = content.ReadabilityExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True
        # verify result has no tags as well, since we have to remove them by hand
        text_has_html = (
            lxml.html.fromstring(extractor.content["text"]).find(".//*") is not None
        )
        assert text_has_html is False

    def test_trafilatura(self):
        extractor = content.TrafilaturaExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_boilerpipe3(self):
        extractor = content.BoilerPipe3Extractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_goose(self):
        extractor = content.GooseExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_newspaper3k(self):
        extractor = content.Newspaper3kExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_rawhtml(self):
        extractor = content.RawHtmlExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_lxml(self):
        extractor = content.LxmlExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True


class TestContentFromUrl(unittest.TestCase):

    def _fetch_and_validate(self, url: str, expected_method: Optional[str]):
        # these should all be cached locally
        html_text, _ = mock_fetch(url)
        results = content.from_html(
            url, html_text
        )  # will throw BadContentError if needed
        assert results["url"] == url
        assert len(results["text"]) > content.MINIMUM_CONTENT_LENGTH
        assert results["extraction_method"] == expected_method
        return results

    def test_failure_javascript_alert(self):
        url = "https://web.archive.org/web/http://www.prigepp.org/aula-foro-answer.php?idcomentario=301c4&idforo=cc0&idcrso=467&CodigoUni=100190"
        results = self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        assert "Dirigido a Operadores de Justicia de toda la región" in results["text"]

    def test_failure_all_javascript(self):
        # this is rendered all by JS, so we can't do anything
        url = "https://web.archive.org/web/https://nbcmontana.com/news/local/2-women-killed-children-hurt-in-western-nebraska-crash"
        try:
            self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
            assert False
        except BadContentError:
            assert True

    def test_lanacion(self):
        # this one has a "Javascript required" check, which readability-lxml doesn't support but Trifilatura does
        url = "https://web.archive.org/web/https://www.lanacion.com.ar/seguridad/cordoba-en-marzo-asesinaron-a-tres-mujeres-nid1884942/"
        results = self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        assert (
            "Cuando llegaron los agentes encontraron a la mujer en el dormitorio tirada"
            in results["text"]
        )

    def test_cnn(self):
        url = "https://web.archive.org/web/https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"
        results = self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        assert (
            "McConnell is calling on the education secretary to abandon the idea."
            in results["text"]
        )

    def test_from_url_informe_correintes(self):
        url = "http://www.informecorrientes.com/vernota.asp?id_noticia=44619"
        results = self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        assert (
            "En este sentido se trabaja en la construcción de sendos canales a cielo abierto"
            in results["text"]
        )

    def test_from_url_página_12(self):
        # this one has a "Javascript required" check, which readability-lxml doesn't support but Trifilatura does
        url = "https://web.archive.org/web/https://www.pagina12.com.ar/338796-coronavirus-en-argentina-se-registraron-26-053-casos-y-561-m"
        results = self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        assert (
            "Por otro lado, fueron realizados en el día 84.085 tests" in results["text"]
        )

    def test_method_success_stats(self):
        url = "https://web.archive.org/web/https://www.pagina12.com.ar/338796-coronavirus-en-argentina-se-registraron-26-053-casos-y-561-m"
        self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        url = "http://www.informecorrientes.com/vernota.asp?id_noticia=44619"
        self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        stats = content.method_success_stats
        assert stats[content.METHOD_TRAFILATURA] >= 0
        assert stats[content.METHOD_READABILITY] == 0
        assert stats[content.METHOD_BEAUTIFUL_SOUP_4] == 0

    def test_encoding_fix(self):
        url = "https://web.archive.org/web/https://www.mk.co.kr/news/society/view/2020/07/693939/"
        results = self._fetch_and_validate(url, content.METHOD_TRAFILATURA)
        assert (
            "Á" not in results["text"]
        )  # this would be there if the encoding isn't being read right
        assert "수도권과" in results["text"]

    def test_too_short_content(self):
        url = "https://web.archive.org/web/20161214233744id_/http://usnatarchives.tumblr.com/post/66921244001/cast-your-vote-for-the-immigration-act-to-be/embed"
        try:
            self._fetch_and_validate(url, None)
            assert False
        except BadContentError:
            assert True

    def test_failing_url(self):
        # run this one against live internet connection to verify schema fails
        url = "chrome://newtab/"
        try:
            _, _ = webpages.fetch(url)
            assert False
        except requests.exceptions.InvalidSchema:
            # this is an image, so it should return nothing
            assert True

    def test_not_html(self):
        # run this one against live internet to get image because that won't cache
        url = "https://s3.amazonaws.com/CFSV2/obituaries/photos/4736/635311/5fecf89b1a6fb.jpeg"
        try:
            _, _ = webpages.fetch(url)
            assert False
        except RuntimeError:
            # this is an image, so it should return nothing
            assert True


if __name__ == "__main__":
    unittest.main()
