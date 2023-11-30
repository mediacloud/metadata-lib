import logging
import re
import tldextract
from typing import Optional
import url_normalize
from furl import furl
import ipaddress
import pathlib

from .urlshortners import URL_SHORTENER_HOSTNAMES

# a list of high-volume domains that Media Cloud has historically ingested from, but are not news domains
base_dir = pathlib.Path(__file__).parent.resolve()
with open(pathlib.Path(base_dir, 'data', 'domain-skip-list.txt')) as f:
    NON_NEWS_DOMAINS = [line.strip() for line in f.readlines() if len(line.strip()) > 0]

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


def _is_suffix_only_parsed_url(parsed_url) -> bool:
    return (len(parsed_url.domain) == 0) and (len(parsed_url.subdomain) == 0) and (len(parsed_url.suffix)) > 0


def canonical_domain(raw_url: str) -> str:
    """
    Return a useful canonical domain name given a url. In general this is the logical unique part of the domain.
    However, to support news-based media research, this takes into account a list of exceptinos where this isn't the
    case (wordpress.com, substack.com, etc). This also handles Google AMP domains appropriately.
    Created by James O'Toole with input from Emily Ndulue, Linas Valiukas, Anissa Piere, and Fernando Bermejo.
    :param raw_url: the full URL to extract a unique domain from
    :return:
    """
    # handle IP addresses first
    try:
        parsed_domain = tldextract.extract(raw_url)
        ipaddress.ip_address(parsed_domain.domain)
        # if this continues, it means the URL is hosted at an IP address
        return parsed_domain.domain
    except ValueError:
        pass

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

    # handle exceptions
    if candidate_domain == '':
        # country-level domains like gov.cn
        if _is_suffix_only_parsed_url(parsed_domain):
            candidate_domain = parsed_domain.suffix

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
    watch_match = yt_watch_pattern.match(url)
    if watch_match:
        return f'https://www.youtube.com/watch?v={watch_match.group(1)}'
    embed_match = yt_embed_pattern.match(url)
    if embed_match:
        return f'https://www.youtube.com/watch?v={embed_match.group(1)}'
    channel_match = yt_channel_pattern.match(url)
    if channel_match:
        return f'https://www.youtube.com/channel/{channel_match.group(1)}'
    user_match = yt_channel_pattern.match(url)
    if user_match:
        return f'https://www.youtube.com/user/{user_match.group(1)}'
    generic_match = yt_generic_pattern.match(url)
    if generic_match:
        return f'https://www.youtube.com/{generic_match.group(1)}'
    return url


def _remove_query_params(url: str) -> str:
    uri = furl(url)
    uri.fragment.set(path='')  # Remove #fragment
    parameters_to_remove = [
        # Facebook parameters (https://developers.facebook.com/docs/games/canvas/referral-tracking)
        'fb_action_ids', 'fb_action_types', 'fb_source', 'fb_ref', 'action_object_map', 'action_type_map',
        'action_ref_map', 'fsrc_fb_noscript',
        'yclid', '_openstat',  # metrika.yandex.ru parameters
        'sort'  # Make the sorting default (e.g. on Reddit)
        # Some other parameters (common for tracking session IDs, advertising, etc.)
        'PHPSESSID', 'PHPSESSIONID', 'cid', 's_cid', 'sid', 'ncid', 'ir', 'ref', 'oref', 'eref', 'ns_mchannel',
        'ns_campaign', 'ITO', 'wprss', 'custom_click', 'source', 'feedName', 'feedType', 'skipmobile', 'skip_mobile',
        'altcast_code',
        # Delete the "empty" parameter (e.g. in http://www-nc.nytimes.com/2011/06/29/us/politics/29marriage.html?=_r%3D6)
        ''
    ]
    if 'facebook.com' in uri.host.lower():
        # Additional parameters specifically for the facebook.com host
        parameters_to_remove += [ 'ref', 'fref', 'hc_location' ]
    if 'nytimes.com' in uri.host.lower():
        # Additional parameters specifically for the nytimes.com host
        parameters_to_remove += ['emc', 'partner', '_r', 'hp', 'inline', 'smid', 'WT.z_sma', 'bicmp', 'bicmlukp',
            'bicmst', 'bicmet', 'abt', 'abg']
    if 'livejournal.com' in uri.host.lower():
        # Additional parameters specifically for the livejournal.com host
        parameters_to_remove += ['thread', 'nojs']
    if 'google.' in uri.host.lower():
        # Additional parameters specifically for the google.[com,lt,...] host
        parameters_to_remove += ['gws_rd', 'ei']
    # Some Australian websites append the "nk" parameter with a tracking hash
    if uri.query.params and 'nk' in uri.query.params and uri.query.params['nk'] is not None:
        for nk_value in uri.query.params['nk']:
            if re.search(r'^[0-9a-fA-F]+$', nk_value, re.I):
                parameters_to_remove += ['nk']
                break
    # Remove cruft parameters
    for parameter in parameters_to_remove:
        if ' ' in parameter:
            logger.warning('Invalid cruft parameter "%s"' % parameter)
        uri.query.params.pop(parameter, None)
    for name in list(uri.query.params.keys()):  # copy of list to be able to delete
        # Remove parameters that start with '_' (e.g. '_cid') because they're
        # more likely to be the tracking codes
        if name.startswith('_'):
            uri.query.params.pop(name, None)
        # Remove GA parameters, current and future (e.g. "utm_source",
        # "utm_medium", "ga_source", "ga_medium")
        # (https://support.google.com/analytics/answer/1033867?hl=en)
        if name.startswith('ga_') or name.startswith('utm_'):
            uri.query.params.pop(name, None)
    return uri.url


archive_url_pattern = re.compile(r'^https://archive.is/[a-z0-9]/[a-z0-9]+/(.*)', re.I)
another_url_pattern = re.compile(r'^(https?://)(m|beta|media|data|image|www|cdn|topic|article|news|archive|blog|video|search|preview|login|shop|sports?|act|donate|press|web|photos?|\d+?).?\.(.*\.)', re.I)
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
    if yt_generic_pattern.match(url):  # YouTube URLs video IDs are case sensitive
        url = normalize_youtube_url(url)
    else:
        url = url.lower()
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
    url = _remove_query_params(url)
    # Remove empty values in query string, e.g. http://bash.org/?244321=
    url = url.replace('=&', '&')
    url = re.sub(r'=$', '', url)

    return url


HOMEPAGE_URL_PATH_REGEXES = [
    # Empty path (e.g. http://www.nytimes.com)
    re.compile(r'^$', re.I),
    # One or more slash (e.g. http://www.nytimes.com/, http://m.wired.com///)
    re.compile(r'^/+$', re.I),
    # Limited number of either all-lowercase or all-uppercase (but not both)
    # characters and no numbers, e.g.:
    # * /en/,
    # * /US
    # * /global/,
    # * /trends/explore
    # but not:
    # * /oKyFAMiZMbU
    # * /1uSjCJp
    re.compile(r'^[a-z/\-_]{1,18}/?$'),
    re.compile(r'^[A-Z/\-_]{1,18}/?$'),
]


def is_homepage_url(raw_url: str) -> bool:
    """Returns true if URL is a homepage-like URL (ie. not an article)."""
    url = raw_url.strip() # remove whitespace
    if is_shortened_url(url):  # if it is shortened than it should get a free pass becasue we have to resolve it later
        return False
    uri = furl(url)
    for homepage_url_path_regex in HOMEPAGE_URL_PATH_REGEXES:
        matches = re.search(homepage_url_path_regex, str(uri.path))
        if matches:
            return True
    return False


def is_shortened_url(raw_url: str) -> bool:
    """Returns true if URL is a shortened URL (e.g. with Bit.ly)."""
    url = raw_url.strip()
    uri = furl(url)
    if str(uri.path) is not None and str(uri.path) in ['', '/']:
        # Assume that most of the URL shorteners use something like
        # bit.ly/abcdef, so if there's no path or if it's empty, it's not a
        # shortened URL
        return False

    uri_host = uri.host.lower()
    if uri_host in URL_SHORTENER_HOSTNAMES:
        return True

    # Otherwise match the typical https://wapo.st/4FGH5Re3 format
    if re.match(r'https?://[a-z]{1,4}\.[a-z]{2}/([a-z0-9]){3,12}/?$', url, flags=re.IGNORECASE) is not None:
        return True

    return False
