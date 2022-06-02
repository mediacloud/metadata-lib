import logging
import re
import tldextract
from typing import Optional
import url_normalize

logger = logging.getLogger(__name__)

blog_domain_pattern = re.compile(
        r'\.go\.com|\.wordpress\.com|\.blogspot\.|\.livejournal\.com|\.privet\.ru|\.wikia\.com'
        r'|\.24open\.ru|\.patch\.com|\.tumblr\.com|\.github\.io|\.typepad\.com'
        r'|\.squarespace\.com|\.substack\.com|\.iheart\.com|\.ampproject\.org|\.mail\.ru|\.wixsite\.com'
        r'|\.medium.com|\.free\.fr|\.list-manage\.com|\.over-blog\.com|\.weebly\.com|\.typeform\.com'
        r'|\.nationbuilder\.com|\.tripod\.com|\.insanejournal\.com|\.cloudfront\.net|\.wpengine\.com'
        r'|\.noblogs\.org|\.formstack\.com|\.altervista\.org|\.home\.blog|\.kinja\.com|\.sagepub\.com'
        r'|\.ning\.com|\.hypotheses\.org|\.narod\.ru|\.submittable\.com|\.smalltownpapers\.com'
        r'|\.herokuapp\.com|\.newsvine\.com|\.newsmemory\.com|\.beforeitsnews\.com|\.jimdo\.com'
        r'|\.wickedlocal\.com|\.radio\.com|\.stackexchange\.com|\.buzzsprout\.com'
        r'|\.appspot\.com|\.simplecast\.com|\.fc2\.com|\.podomatic\.com|\.azurewebsites\.|\.sharepoint\.com'
        r'|\.windows\.net|\.wix\.com|\.googleblog\.com|\.hubpages\.com|\.gitlab\.io|\.blogs\.com'
        r'|\.shinyapps\.io', re.I)


def canonical_domain(raw_url: str) -> str:
    """
    Return a useful canonical domain name given a url. In general this is the logical unique part of the domain.
    However, to support news-based media research, this takes into account a list of exceptinos where this isn't the
    case (wordpress.com, substack.com, etc). This also handles Google AMP domains appropriately.
    Created by James O'Toole with input from Emily Ndulue, Linas Valiukas, Anissa Piere, and Fernando Bermejo.
    :param raw_url: the full URL to extract a unique domain from
    :return:
    """
    url = normalize_url(raw_url)
    parsed_domain = tldextract.extract(url)
    # treat certain domains differently
    is_blogging_subdomain = blog_domain_pattern.search(url)
    if is_blogging_subdomain:
        # treat the subdomain as part of the official domain for blogging-like domains
        candidate_domain = parsed_domain.subdomain.lower() + '.' + parsed_domain.registered_domain.lower()
    else:
        # default to "registered domain" the URL is attributed to
        candidate_domain = parsed_domain.registered_domain.lower()

    # also handle amp URLs smartly
    if 'cdn.ampproject.org' in candidate_domain:
        candidate_domain = candidate_domain.replace('.cdn.ampproject.org', '').\
            replace('amp-', '').\
            replace('/', '').\
            replace('--', '-')
        candidate_domain = candidate_domain.replace("-", ".")

    return candidate_domain


# broken URLs that look like this: http://http://www.al-monitor.com/pulse
double_protocol_url_pattern = re.compile(r'(https?://)https?:?//', re.I)
# URLs with only one slash after "http" ("http:/www.")
missing_slash_url_pattern = re.compile(r'(https?:/)(\w)', re.I)
# urls just start with //
missing_protocol_url_pattern = re.compile(r'^//', re.I)
# bad slashes - backslash to forward
bad_slashes_url_pattern = re.compile(r'\\')
# missing port, e.g. "https://www.gpo.gov:/fdsys/pkg/PL<...>"
missing_port_url_pattern = re.compile(r'^(https?://[\w\d\-.]+):($|/)', re.I)
# Add slash after domain name: ie. http://newsmachete.com?page=2 -> http://newsmachete.com/?page=2
missing_domain_slash_url_pattern = re.compile(r'(https?://[^/]+)\?', re.I)
# spaces
spaces_url_pattern = re.compile(r' ')


def _fix_common_url_mistakes(url: str) -> Optional[str]:
    if url is None:
        return None
    url = url.strip()
    url = double_protocol_url_pattern.sub(r"\1", url)
    url = missing_slash_url_pattern.sub(r"\1/\2", url)
    url = missing_protocol_url_pattern.sub('http://', url)
    url = bad_slashes_url_pattern.sub(r'/', url)
    url = re.sub(missing_port_url_pattern, r"\1\2", url)
    url = missing_domain_slash_url_pattern.sub(r"\1/?", url)
    url = spaces_url_pattern.sub( r'%20', url)
    return url


yt_watch_pattern = re.compile(r'https?://[^/]*youtube.com/watch\?v=([^&]+)', re.I)
yt_embed_pattern = re.compile(r'https?://[^/]*youtube.com/embed/([^\?]+)', re.I)
yt_channel_pattern = re.compile(r'https?://[^/]*youtube.com/channel/([^\?]+)', re.I)
yt_user_pattern = re.compile(r'https?://[^/]*youtube.com/user/([^\?]+)', re.I)
yt_generic_pattern = re.compile(r'https?://[^/]*youtube.com/(.*)', re.I)


def normalize_youtube_url(url: str) -> str:
    """
    Convert various youtube video urls into a standard form. Important to do this so that you don't get multiple URLs
    for the same video, which matters because YouTube has a tight API quota so you don't want to be hittig it when
    for content you have already.
    """
    watch_match = yt_watch_pattern.match(url, re.IGNORECASE)
    if watch_match:
        return f'https://www.youtube.com/watch?v={watch_match.group(1)}'
    embed_match = yt_embed_pattern.match(url, re.IGNORECASE)
    if embed_match:
        return f'https://www.youtube.com/watch?v={embed_match.group(1)}'
    channel_match = yt_channel_pattern.match(url, re.IGNORECASE)
    if channel_match:
        return f'https://www.youtube.com/channel/{channel_match.group(1)}'
    user_match = yt_channel_pattern.match(url, re.IGNORECASE)
    if user_match:
        return f'https://www.youtube.com/user/{user_match.group(1)}'
    generic_match = yt_generic_pattern.match(url, re.IGNORECASE)
    if generic_match:
        return f'https://www.youtube.com/{generic_match.group(1)}'
    return url


archive_url_pattern = re.compile(r'^https://archive.is/[a-z0-9]/[a-z0-9]+/(.*)', re.I)
another_url_pattern = re.compile(r'^(https?://)(m|beta|media|data|image|www?|cdn|topic|article|news|archive|blog|video|search|preview|login|shop|sports?|act|donate|press|web|photos?|\d+?).?\.(.*\.)', re.I)
podomatic_url_pattern = re.compile(r'http://.*pron.*\.podomatic\.com', re.I)
anchor_url_pattern = re.compile(r'#.*')
multiple_slashes_url_pattern = re.compile(r'(//.*/)/+', re.I)
http_url_pattern = re.compile(r'^https:', re.I)
trailing_slash_url_pattern = re.compile(r'https?://[^/]*$', re.I)


def normalize_url(url: str) -> Optional[str]:
    """
    Support later deduplicaton of URLs by applying a simple set of transformations on a URL to make it match other
    equivalent URLs as well as possible. This normalization is "lossy":
     * makes the whole URL lowercase
     * removes subdomain parts "m.", "data.", "news.", ...in some cases).
    """
    if url is None:
        return None
    if len(url) == 0:
        return None
    url = _fix_common_url_mistakes(url)
    url = url.lower()
    url = normalize_youtube_url(url)
    # make archive.is links look like the destination link
    url = archive_url_pattern.sub(r'\1', url)
    if not url.startswith('http'):
        url = 'http://' + url
    # r2.ly redirects through the hostname, ala http://543.r2.ly
    if 'r2.ly' not in url:
        url = another_url_pattern.sub(r"\1\3", url)
    # collapse the vast array of http://pronkraymond83483.podomatic.com/ urls into http://pronkpops.podomatic.com/
    url = podomatic_url_pattern.sub('http://pronkpops.podomatic.com', url)
    # get rid of anchor text
    url = anchor_url_pattern.sub('', url)
    # get rid of multiple slashes in a row
    url = multiple_slashes_url_pattern.sub(r"\1", url)
    url = http_url_pattern.sub('http:', url)
    # canonical_url might raise an encoding error if url is not invalid; just skip the canonical url step in the case
    # noinspection PyBroadException
    try:
        url = url_normalize.url_normalize(url)
    except Exception as ex:
        logger.warning("Unable to get normalized URL for %s: %s" % (url, str(ex),))
    # add trailing slash
    if trailing_slash_url_pattern.search(url):
        url += '/'
    return url
