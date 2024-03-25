import datetime as dt
import time
import unittest

import pytest

import mcmetadata

from .. import content, extract, webpages
from ..exceptions import BadContentError


class TestExtract(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def slow_down_tests(self):
        yield
        time.sleep(0.5)

    def setUp(self) -> None:
        webpages.DEFAULT_TIMEOUT_SECS = 30  # try to avoid timeout errors

    def tearDown(self):
        time.sleep(1)  # sleep time in seconds

    def test_shortened(self):
        shortened_url = "https://cnn.it/3wGkGU1"
        results = extract(url=shortened_url)
        assert 'is_shortened' in results
        assert results['is_shortened'] is True
        assert results['original_url'] == shortened_url
        assert results['url'] != shortened_url
        assert results['url'] == "https://www.cnn.com/2022/08/29/weather/weather-news-labor-day-tropical-system-texas-rain-wxn/index.html"

    def test_homepage(self):
        results = extract(url="https://web.archive.org/web/")
        assert 'is_homepage' in results
        assert results['is_homepage'] is True

    def test_no_date(self):
        # Fail gracefully for webpages that aren't news articles, and thus don't have publication dates
        results = extract(url="https://web.archive.org/web/https://example.com/")
        assert 'publication_date' in results
        assert results['publication_date'] is None
        assert 'is_homepage' in results
        assert results['is_homepage'] is False

    def test_observers(self):
        test_url = "https://web.archive.org/web/https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        results = extract(test_url)
        assert 'publication_date' in results
        assert results['publication_date'] == dt.datetime(2019, 8, 27, 0, 0)
        assert 'text_content' in results
        assert len(results['text_content']) > 7000
        assert 'text_extraction_method' in results
        assert results['text_extraction_method'] == content.METHOD_TRAFILATURA
        assert 'canonical_domain' in results
        assert results['canonical_domain'] == 'france24.com'
        assert 'article_title' in results
        assert results['article_title'] == 'African migrants trapped in Mexico protest for right to travel to USA'
        assert 'language' in results
        assert results['language'] == 'en'
        assert 'original_url' in results
        assert results['original_url'] == "https://web.archive.org/web/https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        assert 'url' in results
        assert results['url'] == 'https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey'

    def test_archived_url(self):
        # properly handle pages at web archives (via memento headers)
        test_url = "https://web.archive.org/web/https://www.nytimes.com/interactive/2018/12/10/business/location-data-privacy-apps.html"
        results = extract(test_url)
        assert 'canonical_domain' in results
        assert results['canonical_domain'] == 'nytimes.com'
        assert 'original_url' in results
        assert results['url'] == 'https://www.nytimes.com/interactive/2018/12/10/business/location-data-privacy-apps.html'

    def test_language(self):
        url = "https://web.archive.org/web/https://www.mk.co.kr/news/society/view/2020/07/693939/"
        results = extract(url)
        assert 'language' in results
        assert results['language'] == 'ko'

    def test_regionalized_language(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        results = extract(url)
        assert "pt" == results['language']
        assert "pt-br" == results['full_language']

    def test_redirected_url(self):
        url = "https://api.follow.it/track-rss-story-click/v3/ecuhSAhRa8kTTPWTA7xaXioxzwoq1nFt"
        results = extract(url)
        assert url == results['original_url']
        final_url = "https://www.trussvilletribune.com/2022/03/02/three-students-from-center-point-receive-academic-scholarships/"
        assert final_url == results['url']
        assert "trussvilletribune.com" == results['canonical_domain']
        assert results['normalized_url'] == "http://trussvilletribune.com/2022/03/02/three-students-from-center-point-receive-academic-scholarships/"
        assert results['language'] == 'en'

    def test_basic(self):
        url = "https://www.indiatimes.com/news/india/75th-independence-day-india-august-15-576959.html"
        results = extract(url)
        assert url == results['original_url']
        assert url == results['url']
        assert 'unique_url_hash' in results
        assert 'other' not in results
        assert 'version' in results
        assert results['version'] == mcmetadata.__version__

    def test_other_metadata(self):
        url = "https://www.indiatimes.com/news/india/75th-independence-day-india-august-15-576959.html"
        results = extract(url, include_other_metadata=True)
        assert url == results['original_url']
        assert url == results['url']
        assert 'other' in results
        assert results['text_extraction_method'] == content.METHOD_TRAFILATURA
        assert results['other']['raw_title'] == "India's 75th Year Of Freedom: Why Was August 15 Chosen As Independence Day?"
        assert results['other']['raw_publish_date'] == dt.datetime(2022, 8, 14, 0, 0)
        assert results['other']['top_image_url'].startswith("https://im.indiatimes.in/content/2022/Aug/flag_62f4964dc6314.jpg")
        assert len(results['other']['authors']) == 1

    def test_whitespace_removal(self):
        previous_min_content_length = content.MINIMUM_CONTENT_LENGTH
        content.MINIMUM_CONTENT_LENGTH = 10
        url = "https://observador.vsports.pt/embd/75404/m/9812/obsrv/53a58b677b53143428e47d43d5887139?autostart=false"
        results = extract(url, include_other_metadata=True)
        # the point here is that it removes all pre and post whitespace - tons of junk
        assert len(results['text_content']) == 110
        content.MINIMUM_CONTENT_LENGTH = previous_min_content_length

    def test_url_whitespace_removal(self):
        url = ' https://www.letras.com.br/banda-n-drive/eden '
        results = extract(url)
        assert results is not None

    def test_memento_without_original_url(self):
        try:
            url = "https://web.archive.org/web/20210412063445id_/https://ehp.niehs.nih.gov/action/doUpdateAlertSettings?action=addJournal&journalCode=ehp&referrer=/action/doSearch?ContribAuthorRaw=Davis%2C+Jacquelyn&ContentItemType=research-article&startPage=&ContribRaw=Martin%2C+Denny"
            _ = extract(url, include_other_metadata=True)
            assert False
        except BadContentError:
            assert True

    def test_overrides(self):
        url = "https://www.indiatimes.com/news/india/75th-independence-day-india-august-15-576959.html"
        overrides = dict(
            text_content="This is some text",
            article_title="This is a title",
            language="pt",
            publication_date=dt.date(2023, 1, 1)
        )
        # validate not the same as overrides
        results = extract(url)
        assert results['text_content'] != overrides['text_content']
        assert results['article_title'] != overrides['article_title']
        assert results['language'] != overrides['language']
        assert results['publication_date'] != overrides['publication_date']
        # now use overrides and validate they are changed
        results = extract(url, overrides=overrides)
        assert results['text_content'] == overrides['text_content']
        assert results['article_title'] == overrides['article_title']
        assert results['language'] == overrides['language']
        assert results['publication_date'] == overrides['publication_date']

    def test_default_title(self):
        # throws too short error if no default
        url = "https://web.archive.org/web/20111013162600id_/http://www.azftf.gov/(F(r8GSI1MAawoG8fkwp0vWYNSTuweOi8-9wgJOr4j83rTcpZDuFOV5E2PG737tNitGhzYAsUmVcwVEcgwKEtYFADTmzsQMJto9bZTOzDBHUGRpirFPIt4osB08CAslzBk-ih5ATrsM-P7DRxDwcNdmfB4jU1Y1))/WhatWeDo/Volunteer/Pages/default.aspx"
        results = extract(url)
        assert results['article_title'] is None
        # verify throws too short error
        defaults = dict(article_title="This is a title")
        results = extract(url, defaults=defaults)
        assert results['article_title'] == defaults['article_title']

    def test_default_pub_date(self):
        html = "<html><body>sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf</body></html>"
        # verify can't guess date
        results = extract("https://www.example.com", html_text=html)
        assert results['publication_date'] is None
        # now with default
        defaults = dict(publication_date=dt.datetime(2023, 2, 1))
        results = extract("https://www.example.com", html_text=html, defaults=defaults)
        assert results['publication_date'] == defaults['publication_date']


class TestStats(unittest.TestCase):

    def test_reset(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        _ = extract(url)
        assert mcmetadata.stats.get('total') > 0
        mcmetadata.reset_stats()
        assert mcmetadata.stats.get('total') == 0

    def test_total_works(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        _ = extract(url)
        assert mcmetadata.stats.get('total') > 0
        for s in mcmetadata.STAT_NAMES:
            assert s in mcmetadata.stats  # stat is recorded
            assert mcmetadata.stats.get(s) > 0  # has real data
            if s != 'total':  # is less than total
                assert mcmetadata.stats.get('url') < mcmetadata.stats.get('total')

    def test_passed_in_accumulator(self):
        mcmetadata.reset_stats()
        local_stats = {s: 0 for s in mcmetadata.STAT_NAMES}
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        _ = extract(url, stats_accumulator=local_stats)
        for s in mcmetadata.STAT_NAMES:  # verify global counter didn't count
            assert s in mcmetadata.stats
            assert mcmetadata.stats.get(s) == 0
        for s in mcmetadata.STAT_NAMES:  # verify local counter did count
            assert s in local_stats
            assert local_stats.get(s) > 0


if __name__ == "__main__":
    unittest.main()
