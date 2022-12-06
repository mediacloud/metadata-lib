import unittest
from typing import Optional
import pytest
import re
from surt import surt
from .. import titles
from .. import webpages
from . import read_fixture


@pytest.fixture
def use_cache(request):
    return request.config.getoption('--use-cache')


def filesafe_url(url):
    url = re.sub('"', "", url)
    s = surt(url) 
    filesafe_surt = "cached-"+re.sub("\W+", "", url)
    return filesafe_surt


class TestTitle(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def get_use_cache(self, use_cache):
        self.use_cache = use_cache

    @staticmethod
    def _load_and_validate(fixture_filename: str, expected_title: str):
        html_text = read_fixture(fixture_filename)
        assert titles.from_html(html_text) == expected_title
    
    def _fetch_and_validate(self, url: str, expected_title: Optional[str]):
        if self.use_cache:
            try:
                html_text = read_fixture(filesafe_url(url))
            except:
                html_text, _ = webpages.fetch(url)
        else:
            html_text, _ = webpages.fetch(url)
        assert titles.from_html(html_text) == expected_title

    def test_meta_og_title(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.indiatimes.com/explainers/news/united-nations-climate-report-means-for-india-wet-bulb-temperature-563318.html",
            "Explained: What Does The New United Nations 'Alarming' Climate Report Mean For India?"
        )
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.corriere.it/esteri/22_marzo_07/bombe-ucraine-donbass-soldati-russi-azioni-umanitarie-mondo-parallelo-mosca-176a20ea-9e41-11ec-aa45-e6507f140451.shtml",
            "Cosa sanno, davvero, i cittadini russi su quello che sta accadendo in Ucraina?"
        )

    def test_meta_og_title2(self):
        self._load_and_validate("bloomberg-original.html", "Elon Got His Deal")

    def test_title_tag(self):
        self._load_and_validate("bloomberg-no-meta.html", "Elon Got His Deal")

    def test_title_fail(self):
        self._fetch_and_validate("https://web.archive.org/web/https://ura.news/news/1052317323",
                                 "Нюша поддержала Putin Team и поздравила больных детей с новым годом")

    def test_title_encoding(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://hindi.oneindia.com/amphtml/news/india/aam-aadmi-party-reaction-on-amit-shah-statement-on-corona-case-in-delhi-567287.html",
            "अमित शाह के बयान पर AAP का पलटवार- अनलॉक से बढ़े मामले, इस वजह से मांगी केंद्र सरकार से मदद"
        )

    def test_title_encoding2(self):
        self._fetch_and_validate(
            "https://web.archive.org/web/https://www.elimpulso.com/tag/tregua/",
            "▷ Archivos de Tregua"
        )

    def test_remove_media_source_name_suffix(self):
        url = "https://web.archive.org/web/http://timesofindia.indiatimes.com/videos/news/punjab-exit-poll-c-voter-predicts-majority-for-aap/videoshow/57559218.cms"
        self._fetch_and_validate(
            url, "Punjab exit poll: C-Voter predicts majority for AAP"
        )
        url = "https://web.archive.org/web/https://www.cbc.ca/news/canada/kitchener-waterloo/teen-driver-charged-following-collision-near-shakespeare-opp-say-1.5230335?cmp=rss"
        self._fetch_and_validate(
            url, "Teen driver charged following collision near Shakespeare: OPP"
        )

    def test_remove_section_prefix(self):
        url = "https://web.archive.org/web/https://www.thestar.com/business/economy/opinion/2019/08/23/what-the-fed-could-learn-from-canada.html"
        self._fetch_and_validate(
            url, "What the Fed could learn from Canada"
        )

    def test_prefix_and_suffix(self):
        url = "https://web.archive.org/web/http://www.ozap.com/actu/invites-salut-les-terriens-recoit-florent-pagny-et-frederic-lopez/544047"
        self._fetch_and_validate(
            url, 'Invités : "Salut les Terriens !" reçoit Florent Pagny et Frédéric Lopez'
        )

    def test_special_chars(self):
        url = "https://web.archive.org/web/https://www.lanacion.com.ar/agencias/iran-promete-una-respuesta-inmediata-ante-cualquier-accion-politica-de-oiea-ministerio-nid03062022/"
        self._fetch_and_validate(
            url, 'Irán promete una respuesta "inmediata" ante cualquier acción "política" de OIEA (ministerio)'
        )

    def test_short_meta_long_content_title(self):
        url = "https://web.archive.org/web/https://www.jpnn.com/news/kamrussamad-ppkm-darurat-dihentikan-angka-kematian-berpotensi-tembus-5000-per-hari"
        self._fetch_and_validate(
            url, 'Kamrussamad: PPKM Darurat Dihentikan, Angka Kematian Berpotensi Tembus 5.000 per Hari'
        )

    def test_no_title(self):
        url = "https://web.archive.org/web/20220301020549/http://www.graiul.ro/2022/02/25/gura-lumii-☺-cabana-silvica-vanduta-dar-nu-autoritatilor/?utm_source=rss&utm_medium=rss&utm_campaign=gura-lumii-%25e2%2598%25ba-cabana-silvica-vanduta-dar-nu-autoritatilor"
        self._fetch_and_validate(
            url, 'Gura lumii ☺ Cabană silvică vândută, dar nu autorităților'
        )

    def test_vanity_fair(self):
        url = "https://web.archive.org/web/20220422074927/https://www.harpersbazaar.com/jp/fashion/fashion-column/a36414759/howtobe-sustainable-fashion-210514-hns/"
        self._fetch_and_validate(
            url, 'サステナブルなワードローブにシフトする10のアイデア'
        )

    def test_no_title(self):
        url = "https://web.archive.org/web/20111013162600id_/http://www.azftf.gov/(F(r8GSI1MAawoG8fkwp0vWYNSTuweOi8-9wgJOr4j83rTcpZDuFOV5E2PG737tNitGhzYAsUmVcwVEcgwKEtYFADTmzsQMJto9bZTOzDBHUGRpirFPIt4osB08CAslzBk-ih5ATrsM-P7DRxDwcNdmfB4jU1Y1))/WhatWeDo/Volunteer/Pages/default.aspx"
        self._fetch_and_validate(
            url, None
        )
        url = "https://web.archive.org/web/20161214220739id_/http://services.santabarbaraca.gov/CAP/MG130450/Agenda.htm"
        self._fetch_and_validate(
            url, None
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
