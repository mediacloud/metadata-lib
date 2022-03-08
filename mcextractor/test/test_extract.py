import unittest
import datetime as dt

from .. import extract
from .. import content


class TestExtract(unittest.TestCase):

    def test_observers(self):
        test_url = "https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        results = extract(test_url)
        assert 'publication_date' in results
        assert results['publication_date'] == dt.datetime(2019, 8, 27, 0, 0)
        assert 'text_content' in results
        assert len(results['text_content']) > 7000
        assert 'text_extraction_method' in results
        assert results['text_extraction_method'] == content.METHOD_READABILITY
        assert 'canonical_domain' in results
        assert results['canonical_domain'] == 'france24.com'
        assert 'article_title' in results
        assert results['article_title'] == 'African migrants trapped in Mexico protest for right to travel to USA'
        assert 'language' in results
        assert results['language'] == 'en'


if __name__ == "__main__":
    unittest.main()
