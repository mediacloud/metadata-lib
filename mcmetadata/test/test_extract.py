import unittest
import datetime as dt

from .. import extract
from .. import content


class TestExtract(unittest.TestCase):

    def test_no_date(self):
        # Fail gracefully for webpages that aren't news articles, and thus don't have publication dates
        results = extract(url="https://example.com/")
        assert 'publication_date' in results
        assert results['publication_date'] is None

    def test_observers(self):
        test_url = "https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        results = extract(test_url)
        assert 'publication_date' in results
        assert results['publication_date'] == dt.datetime(2019, 8, 27, 0, 0)
        assert 'text_content' in results
        assert len(results['text_content']) > 7000
        assert 'text_extraction_method' in results
        assert results['text_extraction_method'] == content.METHOD_TRIFILATURA
        assert 'canonical_domain' in results
        assert results['canonical_domain'] == 'france24.com'
        assert 'article_title' in results
        assert results['article_title'] == 'African migrants trapped in Mexico protest for right to travel to USA'
        assert 'language' in results
        assert results['language'] == 'en'
        assert 'original_url' in results
        assert results['original_url'] == 'https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey'

    def test_archived_url(self):
        # properly handle pages at web archives (via memento headers)
        test_url = "https://web.archive.org/web/20220713083114/http://example.com/"
        results = extract(test_url)
        assert 'canonical_domain' in results
        assert results['canonical_domain'] == 'example.com'
        assert 'original_url' in results
        assert results['original_url'] == 'http://example.com/'

    def test_language(self):
        url = "https://www.mk.co.kr/news/society/view/2020/07/693939/"
        results = extract(url)
        assert 'language' in results
        assert results['language'] == 'ko'


if __name__ == "__main__":
    unittest.main()
