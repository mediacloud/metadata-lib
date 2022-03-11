import unittest
import requests

from .. import domains


class TestCanonicalDomain(unittest.TestCase):

    def test_french_domain(self):
        test_url = "https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        d = domains.from_url(test_url)
        assert d == "france24.com"

    def test_org(self):
        test_url = "https://www.kpbs.org/news/2019/jul/09/migrants-cameroon-protest-immigration-process-tiju/"
        d = domains.from_url(test_url)
        assert d == "kpbs.org"

    def test_hyphen(self):
        test_url = "https://www.kenya-today.com/media/moi-burial-confused-ruto-as-matiangi-declares-tuesday-a-public-holiday#comments"
        d = domains.from_url(test_url)
        assert d == "kenya-today.com"

    def test_case(self):
        test_url = "https://rahul.wordpress.com/2021/12/12/awesome-made-up-post"
        d = domains.from_url(test_url)
        assert d == "rahul.wordpress.com"
        test_url = "https://rahuL.WoRdPrEsS.cOm/2021/12/12/awesome-made-up-post"
        d = domains.from_url(test_url)
        assert d == "rahul.wordpress.com"


if __name__ == "__main__":
    unittest.main()
