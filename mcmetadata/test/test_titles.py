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
        self._load_and_validate("bloomberg-no-meta.html", "Elon Got His Deal")

    def test_title_fail(self):
        self._fetch_and_validate("https://ura.news/news/1052317323", "Нюша поддержала Putin Team")

    def test_title_encoding(self):
        self._fetch_and_validate(
            "https://hindi.oneindia.com/amphtml/news/india/aam-aadmi-party-reaction-on-amit-shah-statement-on-corona-case-in-delhi-567287.html",
            "अमित शाह के बयान पर AAP का पलटवार- अनलॉक से बढ़े मामले, इस वजह से मांगी केंद्र सरकार से मदद | aam aadmi party reaction on amit shah statement on corona case in delhi"
        )

    def test_title_encoding2(self):
        self._fetch_and_validate(
            "https://www.elimpulso.com/tag/tregua/",
            "▷ Archivos de Tregua"
        )

    def test_remove_media_source_name_suffix(self):
        url = "http://timesofindia.indiatimes.com/videos/news/punjab-exit-poll-c-voter-predicts-majority-for-aap/videoshow/57559218.cms"
        self._fetch_and_validate(
            url, "Punjab exit poll: C-Voter predicts majority for AAP"
        )
        url = "https://www.cbc.ca/news/canada/kitchener-waterloo/teen-driver-charged-following-collision-near-shakespeare-opp-say-1.5230335?cmp=rss"
        self._fetch_and_validate(
            url, "Teen driver charged following collision near Shakespeare: OPP"
        )

    def test_remove_section_prefix(self):
        url = "https://www.thestar.com/business/economy/opinion/2019/08/23/what-the-fed-could-learn-from-canada.html"
        self._fetch_and_validate(
            url, "What the Fed could learn from Canada"
        )

    def test_prefix_and_suffix(self):
        url = "http://www.ozap.com/actu/invites-salut-les-terriens-recoit-florent-pagny-et-frederic-lopez/544047"
        self._fetch_and_validate(
            url, 'Invités : "Salut les Terriens !" reçoit Florent Pagny et Frédéric Lopez'
        )

    def test_special_chars(self):
        url = "https://www.lanacion.com.ar/agencias/iran-promete-una-respuesta-inmediata-ante-cualquier-accion-politica-de-oiea-ministerio-nid03062022/"
        self._fetch_and_validate(
            url, 'Irán promete una respuesta "inmediata" ante cualquier acción "política" de OIEA (ministerio)'
        )

class TestNormalizeTitle(unittest.TestCase):

    def test_with_tags(self):
        title = "This is my <b>awesome article</b>"
        assert titles.normalize_title(title) == "this is my awesome article"

    def test_whitespace(self):
        title = "  This is my <b>awesome article</b>"
        assert titles.normalize_title(title) == "this is my awesome article"

    def test_with_separator(self):
        title = "My article - My Media"
        assert titles.normalize_title(title) == ("my article - my media")

    def test_multi_part_title(self):
        title = "My article about something awesome that happened - My Media"
        assert titles.normalize_title(title) == "my article about something awesome that happened - my media"

    def test_first_part_pub_name(self):
        media_name = "Washington Post"
        title = media_name + " - My article about something awesome that happened"
        assert titles.normalize_title(title) == "washington post - my article about something awesome that happened"


if __name__ == "__main__":
    unittest.main()
