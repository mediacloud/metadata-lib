import htmldate
import dateparser
from typing import Dict

from . import webpages
from . import content
from . import domains
from . import titles
from . import languages

__VERSION__ = "0.1.1"


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
    pub_date_str = htmldate.find_date(raw_html, url=true_url, original_date=True)
    pub_date = dateparser.parse(pub_date_str) if pub_date_str else None
    article = content.from_html(true_url, raw_html)
    canonical_domain = domains.from_url(true_url)
    article_title = titles.from_html(raw_html, article['title'])
    try:
        language_code = languages.from_text(article['text'])
    except Exception as _:
        language_code = None
    return dict(
        original_url=true_url,
        canonical_domain=canonical_domain,
        publication_date=pub_date,
        language=language_code,
        text_extraction_method=article['extraction_method'],
        article_title=article_title,
        text_content=article['text'],
        version=__VERSION__,
    )
