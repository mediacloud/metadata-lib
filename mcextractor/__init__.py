import htmldate
import dateparser
from typing import Dict

from . import webpages
from . import content
from . import domains
from . import titles
from . import languages


def extract(url: str, html_text: str = None) -> Dict:
    # first fetch the content if we need to
    raw_html = webpages.fetch(url) if html_text is None else html_text
    # parse out the metadata we care about
    pub_date_str = htmldate.find_date(raw_html, url=url, original_date=True)
    pub_date = dateparser.parse(pub_date_str)
    article = content.from_html(url, raw_html)
    canonical_domain = domains.from_url(url)
    article_title = titles.from_html(raw_html, article['title'])
    try:
        language_code = languages.from_text(article['text'])
    except Exception as _:
        language_code = None
    return dict(
        publication_date=pub_date,
        text_content=article['text'],
        text_extraction_method=article['extraction_method'],
        canonical_domain=canonical_domain,
        article_title=article_title,
        language=language_code,
    )


