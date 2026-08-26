import datetime as dt
import unittest

import mcmetadata
from mcmetadata.test import mock_fetch

from .. import content, extract


class TestExtract(unittest.TestCase):

    def test_shortened(self):
        shortened_url = "https://cnn.it/3wGkGU1"
        results = extract(
            shortened_url
        )  # need to fetch full so the URL resolves via headers (cannot cache)
        assert "is_shortened" in results
        assert results["is_shortened"] is True
        assert results["original_url"] == shortened_url
        assert results["url"] != shortened_url
        assert (
            results["url"]
            == "https://www.cnn.com/2022/08/29/weather/weather-news-labor-day-tropical-system-texas-rain-wxn/index.html"
        )

    def test_homepage(self):
        url = "https://web.archive.org/web/"
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html)
        assert "is_homepage" in results
        assert results["is_homepage"] is True

    def test_no_date(self):
        # Fail gracefully for webpages that aren't news articles, and thus don't have publication dates
        url = (
            "https://web.archive.org/web/20260116030752/https://somervilleunitedfc.org/"
        )
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html)
        assert "publication_date" in results
        assert results["publication_date"] is None
        assert "is_homepage" in results
        assert results["is_homepage"] is False

    def test_observers(self):
        test_url = "https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        raw_html, _ = mock_fetch(test_url)
        results = extract(test_url, raw_html)
        assert "publication_date" in results
        assert results["publication_date"] == dt.datetime(2019, 8, 27, 0, 0)
        assert "text_content" in results
        assert len(results["text_content"]) > 7000
        assert "text_extraction_method" in results
        assert results["text_extraction_method"] == content.METHOD_TRAFILATURA
        assert "canonical_domain" in results
        assert results["canonical_domain"] == "france24.com"
        assert "article_title" in results
        assert (
            results["article_title"]
            == "African migrants trapped in Mexico protest for right to travel to USA"
        )
        assert "language" in results
        assert results["language"] == "en"
        assert "url" in results
        assert (
            results["url"]
            == "https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        )

    def test_language(self):
        url = "https://web.archive.org/web/https://www.mk.co.kr/news/society/view/2020/07/693939/"
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html)
        assert "language" in results
        assert results["language"] == "ko"

    def test_regionalized_language(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html)
        assert "pt" == results["language"]
        assert "pt-br" == results["full_language"]

    def test_redirected_url(self):
        url = "https://redirect.me/r/qhw3yh"
        results = extract(url)  # need to fetch live so the redirect happens
        assert url == results["original_url"]
        final_url = "https://www.trussvilletribune.com/2022/03/02/three-students-from-center-point-receive-academic-scholarships/"
        assert final_url == results["url"]
        assert "trussvilletribune.com" == results["canonical_domain"]
        assert (
            results["normalized_url"]
            == "http://trussvilletribune.com/2022/03/02/three-students-from-center-point-receive-academic-scholarships/"
        )
        assert results["language"] == "en"

    def test_basic(self):
        url = "https://www.indiatimes.com/news/india/75th-independence-day-india-august-15-576959.html"
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html)
        assert url == results["original_url"]
        assert url == results["url"]
        assert "unique_url_hash" in results
        assert "other" not in results
        assert "version" in results
        assert results["version"] == mcmetadata.__version__

    def test_other_metadata(self):
        url = "https://www.indiatimes.com/news/india/75th-independence-day-india-august-15-576959.html"
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html, include_other_metadata=True)
        assert url == results["original_url"]
        assert url == results["url"]
        assert "other" in results
        assert results["text_extraction_method"] == content.METHOD_TRAFILATURA
        assert (
            results["other"]["raw_title"]
            == "India's 75th Year Of Freedom: Why Was August 15 Chosen As Independence Day?"
        )
        assert results["other"]["raw_publish_date"] == dt.datetime(2022, 8, 14, 0, 0)
        assert len(results["other"]["authors"]) == 1
        assert results["other"]["authors"][0] == "Gursharan Bhalla"

    def test_whitespace_removal(self):
        previous_min_content_length = content.MINIMUM_CONTENT_LENGTH
        content.MINIMUM_CONTENT_LENGTH = 10
        url = "https://observador.vsports.pt/embd/75404/m/9812/obsrv/53a58b677b53143428e47d43d5887139?autostart=false"
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html)
        # the point here is that it removes all pre and post whitespace - tons of junk
        assert len(results["text_content"]) == 110
        content.MINIMUM_CONTENT_LENGTH = previous_min_content_length

    def test_overrides(self):
        url = "https://www.indiatimes.com/news/india/75th-independence-day-india-august-15-576959.html"
        overrides = dict(
            text_content="This is some text",
            article_title="This is a title",
            canonical_url="https://www.example.com/",
            language="pt",
            publication_date=dt.date(2023, 1, 1),
        )
        # validate not the same as overrides
        html_content, _ = mock_fetch(url)
        results = extract(url, html_content)
        assert results["text_content"] != overrides["text_content"]
        assert results["article_title"] != overrides["article_title"]
        assert results["language"] != overrides["language"]
        assert results["publication_date"] != overrides["publication_date"]
        # now use overrides and validate they are changed
        results = extract(url, html_content, overrides=overrides)
        assert results["text_content"] == overrides["text_content"]
        assert results["article_title"] == overrides["article_title"]
        assert results["language"] == overrides["language"]
        assert results["publication_date"] == overrides["publication_date"]
        assert results["canonical_url"] == overrides["canonical_url"]

    def test_default_title(self):
        # throws too short error if no default
        url = "https://web.archive.org/web/20111013162600id_/http://www.azftf.gov/(F(r8GSI1MAawoG8fkwp0vWYNSTuweOi8-9wgJOr4j83rTcpZDuFOV5E2PG737tNitGhzYAsUmVcwVEcgwKEtYFADTmzsQMJto9bZTOzDBHUGRpirFPIt4osB08CAslzBk-ih5ATrsM-P7DRxDwcNdmfB4jU1Y1))/WhatWeDo/Volunteer/Pages/default.aspx"
        raw_html, _ = mock_fetch(url)
        results = extract(url, raw_html)
        assert results["article_title"] is None
        # verify throws too short error
        defaults = dict(article_title="This is a title")
        results = extract(url, raw_html, defaults=defaults)
        assert results["article_title"] == defaults["article_title"]

    def test_default_pub_date(self):
        html = "<html><body>sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf</body></html>"
        # verify can't guess date
        results = extract("https://www.example.com", html_text=html)
        assert results["publication_date"] is None
        # now with default
        defaults = dict(publication_date=dt.datetime(2023, 2, 1))
        results = extract("https://www.example.com", html_text=html, defaults=defaults)
        assert results["publication_date"] == defaults["publication_date"]

    def test_canonical_url(self):
        canonical_url = "https://www.example.com/sample-page"
        # extract from page with <Link> as per: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
        html = f"<html><head><link rel='canonical' href='{canonical_url}' /></head><body><h1>Sample Content</h1><p>sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf</p><p>Copyright 2024</p></body></html>"
        results = extract("https://www.example.com", html_text=html)
        assert results["canonical_url"] == canonical_url
        # extract from page with <Meta> as per: https://developers.facebook.com/docs/sharing/webmasters/getting-started/versioned-link/
        html = f"<html><head><meta property='og:url' content='{canonical_url}' /></head><body><h1>Sample Content</h1><p>sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf sdf asdf asfewaf lkjl;kjf ;iasjfoijfésadsf</p><p>Copyright 2024</p></body></html>"
        results = extract("https://www.example.com", html_text=html)
        assert results["canonical_url"] == canonical_url


class TestStats(unittest.TestCase):

    def test_reset(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        raw_html, _ = mock_fetch(url)
        _ = extract(url, raw_html)
        assert mcmetadata.stats.get("total") > 0
        mcmetadata.reset_stats()
        assert mcmetadata.stats.get("total") == 0

    def test_total_works(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        raw_html, _ = mock_fetch(url)
        _ = extract(url, raw_html)
        assert mcmetadata.stats.get("total") > 0
        for s in mcmetadata.STAT_NAMES:
            assert s in mcmetadata.stats  # stat is recorded
            assert mcmetadata.stats.get(s) > 0  # has real data
            if s != "total":  # is less than total
                assert mcmetadata.stats.get("url") < mcmetadata.stats.get("total")

    def test_passed_in_accumulator(self):
        mcmetadata.reset_stats()
        local_stats = {s: 0 for s in mcmetadata.STAT_NAMES}
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        raw_html, _ = mock_fetch(url)
        _ = extract(url, raw_html, stats_accumulator=local_stats)
        for s in mcmetadata.STAT_NAMES:  # verify global counter didn't count
            assert s in mcmetadata.stats
            assert mcmetadata.stats.get(s) == 0
        for s in mcmetadata.STAT_NAMES:  # verify local counter did count
            assert s in local_stats
            assert local_stats.get(s) > 0


if __name__ == "__main__":
    unittest.main()
