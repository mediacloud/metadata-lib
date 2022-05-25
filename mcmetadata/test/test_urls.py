import unittest

from .. import urls


class TestCanonicalDomain(unittest.TestCase):

    def test_french_domain(self):
        test_url = "https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        d = urls.canonical_domain(test_url)
        assert d == "france24.com"

    def test_org(self):
        test_url = "https://www.kpbs.org/news/2019/jul/09/migrants-cameroon-protest-immigration-process-tiju/"
        d = urls.canonical_domain(test_url)
        assert d == "kpbs.org"

    def test_hyphen(self):
        test_url = "https://www.kenya-today.com/media/moi-burial-confused-ruto-as-matiangi-declares-tuesday-a-public-holiday#comments"
        d = urls.canonical_domain(test_url)
        assert d == "kenya-today.com"

    def test_wordpress(self):
        test_url = "https://rahulb.wordpress.com/"
        d = urls.canonical_domain(test_url)
        assert d == "rahulb.wordpress.com"

    def test_case(self):
        test_url = "https://rahul.wordpress.com/2021/12/12/awesome-made-up-post"
        d = urls.canonical_domain(test_url)
        assert d == "rahul.wordpress.com"
        test_url = "https://rahuL.WoRdPrEsS.cOm/2021/12/12/awesome-made-up-post"
        d = urls.canonical_domain(test_url)
        assert d == "rahul.wordpress.com"


class TestNormalizeUrl(unittest.TestCase):

    def test_reuters_example(self):
        url1 = "http://feeds.reuters.com/~r/reuters/topnews/~3/nachplxyqso/u-s-probes-border-patrol-as-criticism-of-detention-centers-rises-iduskcn1ty1a5"
        normalized_url1 = urls.normalize_url(url1)
        url2 = "http://feeds.reuters.com/~r/reuters/topNews/~3/NacHplXYqSo/u-s-probes-border-patrol-as-criticism-of-detention-centers-rises-idUSKCN1TY1A5"
        normalized_url2 = urls.normalize_url(url2)
        assert normalized_url1 == normalized_url2

    def test_double_protocol(self):
        url = "http://http://www.al-monitor.com/pulse"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://al-monitor.com/pulse"

    def test_missing_slash(self):
        url = "http:/www.mysite.com/"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://mysite.com/"

    def test_missing_slash(self):
        url = "//www.mysite.com/"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://mysite.com/"

    def test_wrong_slashes(self):
        url = "http:\\\\www.mysite.com/"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://mysite.com/"

    def missing_port(self):
        url = "https://www.gpo.gov:/fdsys/pkg/PL"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "https://gpo.gov/fdsys/pkg/PL"

    def missing_trailing_slash(self):
        url = "http://newsmachete.com?page=2"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://newsmachete.com/"


if __name__ == "__main__":
    unittest.main()
