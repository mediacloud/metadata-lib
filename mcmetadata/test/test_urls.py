import hashlib
import time
import unittest

from parameterized import parameterized

from .. import urls


class TestCanonicalDomain(unittest.TestCase):

    def tearDown(self):
        time.sleep(1)  # sleep time in seconds

    @parameterized.expand([
        ("https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey", "france24.com"),
        ("https://www.bizjournals.com/bizjournals/news/2022/06/02/remote-raise-salary-promotion-pwc-hiring.html", "bizjournals.com"),
        # make sure .org works right
        ("https://www.kpbs.org/news/2019/jul/09/migrants-cameroon-protest-immigration-process-tiju/", "kpbs.org"),
        # make sure hyphen doesn't mess things up
        ("https://www.kenya-today.com/media/moi-burial-confused-ruto-as-matiangi-declares-tuesday-a-public-holiday#comments", "kenya-today.com"),
        # check wordpress exception case
        ("https://datatherapy.wordpress.com/2019/03/13/aligning-your-data-and-methods-your-mission/", "datatherapy.wordpress.com"),
        ("https://wordpress.com/blog/2022/05/19/your-website-looks-great-so-should-your-emails/", "wordpress.com"),
        # check out an AMP CDN case
        ("https://www-example-com.cdn.ampproject.org/c/www.example.com/amp/doc.html", "www.example.com"),
        # try IP address as well
        ("https://147.182.248.18/2022/09/16/incrementan-accidentes-viales-en-toluca-en-dias-patrios/", "147.182.248.18"),
        # governmental suffixes
        ("http://www.gov.cn/", "gov.cn"),
        # close to but not 'www'
        ("http://wwf.or.jp/", "wwf.or.jp"),
        ("http://wwf.org.br/", "wwf.org.br"),
        # non-us examples
        ("https://www.sydney.edu.au", "sydney.edu.au"),
        ("https://travel.gc.ca", "travel.gc.ca"),
        ("http://rn.gov.br/", "rn.gov.br"),
        ('http://www.ma.gov.br/', 'ma.gov.br')
    ])
    def test_canonical_domain(self, test_url, domain):
        assert urls.canonical_domain(test_url) == domain


class TestNormalizeUrl(unittest.TestCase):

    def test_ref_removal(self):
        normalized = "http://upstract.com/x/fdf95bf448e1f2a8"
        url = "https://upstract.com/x/fdf95bf448e1f2a8"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == normalized
        url = "https://upstract.com/x/fdf95bf448e1f2a8?ref=rss"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == normalized

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

    def test_case_insensitive(self):
        url = "http://cnn.COM/my-story"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://cnn.com/my-story"

    def test_youtube_url(self):
        url = "https://www.youtube.com/watch?v=aFCO6WidGVM"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://youtube.com/watch?v=aFCO6WidGVM"

    def test_utm_removal(self):
        url = "http://uniradioinforma.com/noticias/coronavirus/677126/nuevos-sintomas-del-covid-prolongado.html?utm_campaign=rss&utm_medium=link"
        url_without_utm = "http://uniradioinforma.com/noticias/coronavirus/677126/nuevos-sintomas-del-covid-prolongado.html"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == url_without_utm
        url = "http://fake.com/article?foo=123&baz=321"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://fake.com/article?baz=321&foo=123"  # they get ordered
        url = "http://fake.com/article?utm_foo=123&baz=321"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://fake.com/article?baz=321"
        url = "http://fake.com/article?foo=123&UTM_baz=321"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://fake.com/article?foo=123"
        url = "https://www.uniradioinforma.com/noticias/coronavirus/677354/covid-segunda-causa-de-muerte-en-mexico-en-2021.html?utm_source=feed&utm_medium=link&utm_campaign=rss"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == "http://uniradioinforma.com/noticias/coronavirus/677354/covid-segunda-causa-de-muerte-en-mexico-en-2021.html"

    def test_remove_port(self):
        expected_url = "http://do.ma.in/what/ever"
        url = "https://do.ma.in:442/what/ever"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == expected_url
        url = "http://do.ma.in:80/what/ever"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == expected_url

    def test_ip_based_url(self):
        url = "http://10.2.3.4/hello/world.html"
        normalized_url = urls.normalize_url(url)
        assert normalized_url == url


class TestIsHomepageUrl(unittest.TestCase):

    def test_basic(self):
        url = "http://www.nytimes.com"
        assert urls.is_homepage_url(url) is True

    def test_ending_slashes(self):
        url = "http://www.nytimes.com/"
        assert urls.is_homepage_url(url) is True
        url = "http://www.wired.com///"
        assert urls.is_homepage_url(url) is True

    def test_language_code(self):
        url = "http://www.nytimes.com/en"
        assert urls.is_homepage_url(url) is True
        url = "http://www.nytimes.com/en/"
        assert urls.is_homepage_url(url) is True
        url = "http://www.nytimes.com/ES/"
        assert urls.is_homepage_url(url) is True

    def test_category(self):
        url = "http://www.nytimes.com/global/"
        assert urls.is_homepage_url(url) is True

    def test_short_unknown(self):
        url = "http://www.nytimes.com/oKyFAMiZMbU"
        assert urls.is_homepage_url(url) is False

    def test_shortened(self):
        url = "https://bit.ly/my-url"
        assert urls.is_homepage_url(url) is False

    def test_whitespace(self):
        url = ' https://www.letras.com.br/banda-n-drive/eden '  # a real URL from an RSS we fetched
        assert urls.is_homepage_url(url) is False


class TestIsShortenedUrl(unittest.TestCase):

    def test_known_domain(self):
        url = "https://bit.ly/my-url"
        assert urls.is_shortened_url(url) is True

    def test_not_one(self):
        url = "https://thekenyatimes.com/counties/kisumu-traders-alerted-about-cartels-in-stalls-issuance/"
        assert urls.is_shortened_url(url) is False

    def test_custom_pattern(self):
        url = "https://wapo.st/4FGH5Re3"
        assert urls.is_shortened_url(url) is True
        url = "http://nyti.ms/4K9g6u"
        assert urls.is_shortened_url(url) is True


class TestNonNewsDomains(unittest.TestCase):

    def test_none_empty(self):
        for domain in urls.NON_NEWS_DOMAINS:
            assert len(domain) > 0

    def test_inclusion(self):
        assert 'tiktok.com' in urls.NON_NEWS_DOMAINS
        assert 'cnn.com' not in urls.NON_NEWS_DOMAINS


class TestUniqueUrlHash(unittest.TestCase):

    def test_basic_uniqueness(self):
        url1 = "https://www.cnn.com/2023/12/12/politics/takeaways-volodymyr-zelensky-washington/index.html"
        url2 = "https://www.cnn.com/2023/12/12/entertainment/andre-braugher-obit/index.html"
        assert urls.unique_url_hash(url1) != urls.unique_url_hash(url2)

    def test_already_normalized_url(self):
        test_url = "http://thekenyatimes.com/counties/kisumu-traders-alerted-about-cartels-in-stalls-issuance/"
        expected_hash = hashlib.sha256(test_url.encode('utf-8')).hexdigest()
        assert urls.unique_url_hash(test_url) == expected_hash

    def test_normalizing(self):
        bad_hash = hashlib.sha256("https://upstract.com/x/fdf95bf448e1f2a8?ref=rss".encode('utf-8')).hexdigest()
        good_hash = hashlib.sha256(urls.normalize_url("https://upstract.com/x/fdf95bf448e1f2a8").encode('utf-8'))\
            .hexdigest()
        assert good_hash != bad_hash
        test_url = "https://upstract.com/x/fdf95bf448e1f2a8?ref=rss"
        unique_hash = urls.unique_url_hash(test_url)
        assert unique_hash == good_hash
        assert unique_hash != bad_hash


if __name__ == "__main__":
    unittest.main()
