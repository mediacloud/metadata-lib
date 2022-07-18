import unittest
from typing import Optional
import requests

from .. import content
from .. import webpages
from ..exceptions import UnableToExtractError


class TestContentParsers(unittest.TestCase):

    URL = "https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"

    def setUp(self) -> None:
        self.html_content, _ = webpages.fetch(self.URL)

    def test_readability(self):
        extractor = content.ReadabilityExtractor()
        results = extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_trafilatura(self):
        extractor = content.TrafilaturaExtractor()
        results = extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_boilerpipe3(self):
        extractor = content.BoilerPipe3Extractor()
        results = extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_goose(self):
        extractor = content.GooseExtractor()
        results = extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_newspaper3k(self):
        extractor = content.Newspaper3kExtractor()
        results = extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_rawhtml(self):
        extractor = content.RawHtmlExtractor()
        results = extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True


class TestContentFromUrl(unittest.TestCase):

    @staticmethod
    def _fetch_and_validate(url: str, expected_method: Optional[str]):
        html_text, _ = webpages.fetch(url)
        results = content.from_html(url, html_text)
        assert results['url'] == url
        assert len(results['text']) > content.MINIMUM_CONTENT_LENGTH
        assert results['extraction_method'] == expected_method
        return results

    def test_failure_javascript_alert(self):
        url = "http://www.prigepp.org/aula-foro-answer.php?idcomentario=301c4&idforo=cc0&idcrso=467&CodigoUni=100190"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Dirigido a Operadores de Justicia de toda la región" in results['text']

    def test_failure_all_javascript(self):
        # this is rendered all by JS, so we can't do anything
        url = "https://nbcmontana.com/news/local/2-women-killed-children-hurt-in-western-nebraska-crash"
        try:
            results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
            assert False
        except UnableToExtractError as _:
            assert True

    def test_failing_url(self):
        url = "chrome://newtab/"
        try:
            self._fetch_and_validate(url, None)
            assert False
        except requests.exceptions.InvalidSchema as _:
            # this is an image, so it should return nothing
            assert True

    def test_not_html(self):
        url = "https://s3.amazonaws.com/CFSV2/obituaries/photos/4736/635311/5fecf89b1a6fb.jpeg"
        try:
            self._fetch_and_validate(url, None)
        except RuntimeError:
            # this is an image, so it should return nothing
            assert True

    def test_lanacion(self):
        # this one has a "Javascript required" check, which readability-lxml doesn't support but Trifilatura does
        url = 'https://www.lanacion.com.ar/seguridad/cordoba-en-marzo-asesinaron-a-tres-mujeres-nid1884942/'
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Por segunda vez esta semana la provincia se ve sacudida" in results['text']

    def test_cnn(self):
        url = "https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "McConnell is calling on the education secretary to abandon the idea." in results['text']

    def test_from_url_informe_correintes(self):
        url = "http://www.informecorrientes.com/vernota.asp?id_noticia=44619"
        results = self._fetch_and_validate(url, content.METHOD_READABILITY)
        assert "En este sentido se trabaja en la construcción de sendos canales a cielo abierto" in results['text']

    def test_from_url_página_12(self):
        # this one has a "Javascript required" check, which readability-lxml doesn't support but Trifilatura does
        url = "https://www.pagina12.com.ar/338796-coronavirus-en-argentina-se-registraron-26-053-casos-y-561-m"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Por otro lado, fueron realizados en el día 84.085 tests" in results['text']

    def test_method_success_stats(self):
        url = "https://www.pagina12.com.ar/338796-coronavirus-en-argentina-se-registraron-26-053-casos-y-561-m"
        _ = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        url = "http://www.informecorrientes.com/vernota.asp?id_noticia=44619"
        _ = self._fetch_and_validate(url, content.METHOD_READABILITY)
        stats = content.method_success_stats
        assert stats[content.METHOD_TRIFILATURA] >= 1
        assert stats[content.METHOD_READABILITY] >= 1
        assert stats[content.METHOD_DRAGNET] == 0

    def test_encoding_fix(self):
        url = "https://www.mk.co.kr/news/society/view/2020/07/693939/"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Á" not in results['text']
        assert "수도권과" in results['text']


if __name__ == "__main__":
    unittest.main()
