import unittest

from parameterized import parameterized

from .. import feeds


class TestFeedNormalization(unittest.TestCase):

    @parameterized.expand([
        ('https://Aaa.Bbb/ccc?a=1&c=3&b=2#z', 'http://aaa.bbb/ccc?a=1&b=2&c=3#z'),
        ('http://aaA.bbB:80/ccc?c=3&b=2&a=1#Z', 'http://aaa.bbb/ccc?a=1&b=2&c=3#z'),
        ('https://aaA.bbB:443/ccc?c=3&b=2&a=1#Z', 'http://aaa.bbb/ccc?a=1&b=2&c=3#z'),
        ('http://aaA.bbB:123/ccc?c=3&b=2&a=1#Z', 'http://aaa.bbb:123/ccc?a=1&b=2&c=3#z'),
        ('http://peoplesdailyng.com/feed/', 'http://peoplesdailyng.com/feed'),
        ('https://www.peoplesdailyng.com/feed', 'http://peoplesdailyng.com/feed'),
    ])
    def test_normalize(self, test_url, normalized_url):
        assert feeds.normalize_url(test_url) == normalized_url
