import htmldate
import dateparser
from typing import Dict, Optional
import logging
import datetime as dt

from . import webpages
from . import content
from . import urls
from . import titles
from . import languages

__version__ = "0.5.3"

logger = logging.getLogger(__name__)


def _parse_pub_date(html=str, url=str) -> Optional[dt.datetime]:
    pub_date = None
    try:
        pub_date_str = htmldate.find_date(html, url=url, original_date=True)
        if pub_date_str:
            pub_date = dateparser.parse(pub_date_str)
    except:
        # if there is no date found, or it is in a format that can't be parsed, ignore and just keep going
        logger.error('Publication date parsing failed', exc_info=1)
    return pub_date


def extract(url: str, html_text: str = None) -> Dict:
    # first fetch the content if we need to
    if html_text is None:
        raw_html, response = webpages.fetch(url)
        if 'memento-datetime' in response.headers:
            true_url = response.links['original']['url']  # the original url archived
        else:
            true_url = response.url  # followed all the redirects
    else:
        true_url = url
        raw_html = html_text
    # parse out the metadata we care about
    pub_date = _parse_pub_date(raw_html, true_url)
    article = content.from_html(true_url, raw_html)
    article_title = titles.from_html(raw_html, article['title'])
    return dict(
        original_url=true_url,
        normalized_url=urls.normalize_url(url),
        canonical_domain=urls.canonical_domain(true_url),
        publication_date=pub_date,
        language=languages.from_text(article['text']),
        text_extraction_method=article['extraction_method'],
        article_title=article_title,
        normalized_article_title=titles.normalize_title(article_title),
        text_content=article['text'],
        version=__version__,
    )
