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
        meta = content.from_html(self.URL, html_text, False)
        assert meta["extraction_method"] == "trafilatura"
        assert meta["top_image_url"] == self.EXPRECTED_IMG_URL
        meta = content.from_html(self.URL, html_text, True)


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


class TestContentLinks(unittest.TestCase):
    """The `include_links` flag on each extractor's `extract` method."""

    URL = "https://www.cnn.com/2023/12/12/politics/takeaways-volodymyr-zelensky-washington/index.html"
    # the hyperlinks inside the story body - the page itself has ~350 <a> tags
    EXPECTED_LINKS = [
        {
            "text": "Volodymyr Zelensky",
            "href": "https://www.cnn.com/2022/03/29/europe/volodymyr-zelensky-fast-facts/index.html",
        },
        {
            "text": "Washington on Tuesday",
            "href": "https://www.cnn.com/politics/live-news/zelensky-biden-visit-12-12-23/index.html",
        },
        {
            "text": "members of Congress Tuesday morning",
            "href": "https://www.cnn.com/2023/12/12/politics/ukraine-zelensky-washington-trip/index.html",
        },
        {
            "text": "the US declassified new intelligenc",
            "href": "https://www.cnn.com/politics/live-news/zelensky-biden-visit-12-12-23#h_80a87d6b200a0b6b4ffbb29a1f0871cb",
        },
        {
            "text": "a July speech.",
            "href": "https://www.whitehouse.gov/briefing-room/speeches-remarks/2023/07/12/remarks-by-president-biden-on-supporting-ukraine-defending-democratic-values-and-taking-action-to-address-global-challenges-vilnius-lithuania/",
        },
    ]

    def setUp(self) -> None:
        self.html_content, _ = mock_fetch(self.URL)

    def test_link_items_have_text_and_href(self):
        extractor = content.TrafilaturaExtractor()
        extractor.extract(self.URL, self.html_content, include_links=True)
        for link in extractor.content["links"]:
            assert set(link.keys()) == {"text", "href"}

    def test_no_links_key_unless_asked(self):
        for extractor_info in content.extractors:
            extractor = extractor_info["instance"]
            extractor.extract(self.URL, self.html_content)
            assert "links" not in extractor.content, extractor_info["method"]

    def test_trafilatura_text_has_no_markdown_link_syntax(self):
        # asking trafilatura for links can change the text it returns, but the "(url)" half of its markdown
        # should never survive into the text we hand back
        extractor = content.TrafilaturaExtractor()
        extractor.extract(self.URL, self.html_content, include_links=True)
        text = extractor.content["text"]
        assert len(extractor.content["links"]) > 0
        for link in extractor.content["links"]:
            assert f"]({link['href']})" not in text

    def test_from_html_passes_the_flag_through(self):
        meta = content.from_html(self.URL, self.html_content, include_links=True)
        assert meta["extraction_method"] == content.METHOD_TRAFILATURA
        assert meta["links"] == self.EXPECTED_LINKS

    def test_links_are_absolute_in_order_and_not_deduplicated(self):
        base = "https://news.example.com/2026/01/story.html"
        body = (
            "<p>"
            + ("Filler sentence to clear the minimum length. " * 20)
            + (
                "<a href='/local/one.html'>relative</a> "
                "<a href='/local/one.html'>the very same link again</a> "
                "<a href='https://example.org/abs'>absolute</a> "
                "<a href='#section'>same page anchor</a> "
                "<a href='mailto:news@example.com'>email</a></p>"
            )
        )
        extractor = content.ReadabilityExtractor()
        extractor.extract(
            base,
            f"<html><body><article>{body}</article></body></html>",
            include_links=True,
        )
        # repeats stay in, and the order matches the story
        assert extractor.content["links"] == [
            {"text": "relative", "href": "https://news.example.com/local/one.html"},
            {
                "text": "the very same link again",
                "href": "https://news.example.com/local/one.html",
            },
            {"text": "absolute", "href": "https://example.org/abs"},
        ]


if __name__ == "__main__":
    unittest.main()
