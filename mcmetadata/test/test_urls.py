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
        test_url = "https://datatherapy.wordpress.com/2019/03/13/aligning-your-data-and-methods-your-mission/"
        d = urls.canonical_domain(test_url)
        assert d == "datatherapy.wordpress.com"
        test_url = "https://wordpress.com/blog/2022/05/19/your-website-looks-great-so-should-your-emails/"
        d = urls.canonical_domain(test_url)
        assert d == "wordpress.com"

    def test_amp_cdn(self):
        test_url = "https://www-example-com.cdn.ampproject.org/c/www.example.com/amp/doc.html"
        d = urls.canonical_domain(test_url)
        assert d == "www.example.com"

    def test_biz_journals(self):
        test_url = "https://www.bizjournals.com/bizjournals/news/2022/06/02/remote-raise-salary-promotion-pwc-hiring.html"
        d = urls.canonical_domain(test_url)
        assert d == "bizjournals.com"


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

    def test_missing_protocol(self):
        url = "//www.mysite.com/"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://mysite.com/"

    def test_wrong_slashes(self):
        url = "http:\\\\www.mysite.com/"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://mysite.com/"

    def test_missing_port(self):
        url = "https://www.gpo.gov:/fdsys/pkg/PL"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://gpo.gov/fdsys/pkg/pl"

    def test_missing_trailing_slash(self):
        url = "http://newsmachete.com?page=2"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://newsmachete.com/?page=2"


if __name__ == "__main__":
    unittest.main()
