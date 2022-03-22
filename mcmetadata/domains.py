import logging
import re
import tldextract

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

relative_path_pattern = re.compile(r'bizjournals\.com|stuff\.co\.nz', re.I)


def from_url(url: str) -> str:
    """
    Return a useful canonical domain name given a url. In general this is the logical unique part of the domain.
    However, to support news-based media research, this takes into account a list of exceptinos where this isn't the
    case (wordpress.com, substack.com, etc). This also handles Google AMP domains appropriately.
    Created by James O'Toole with input from Emily Ndulue, Linas Valiukas, Anissa Piere, and Fernando Bermejo.
    :param url: the full URL to extract a unique domain from
    :param headers: optionally helpful for pulling our archived URLs
    :return:
    """


    parsed_domain = tldextract.extract(url)

    is_blogging_subdomain = blog_domain_pattern.search(url)

    is_relative_path = relative_path_pattern.search(url)

    if is_blogging_subdomain:
        canonical_domain = parsed_domain.subdomain.lower() + '.' + parsed_domain.registered_domain.lower()
    elif is_relative_path:
        canonical_domain = parsed_domain.registered_domain.lower() + '/' + url + url.split('/')[3]
    else:
        canonical_domain = parsed_domain.registered_domain.lower()

    if 'cdn.ampproject.org' in canonical_domain:
        canonical_domain = canonical_domain.replace('.cdn.ampproject.org', '').\
            replace('amp-', '').\
            replace('/','').\
            replace('--', '-')
        last_dash_index = canonical_domain.rfind('-')
        canonical_domain = canonical_domain[:last_dash_index] + '.' + canonical_domain[last_dash_index + 1:]

    return canonical_domain
