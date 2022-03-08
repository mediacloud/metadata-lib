import htmldate
import py3langid as langid
import dateparser
from typing import Dict

from . import http as http
from . import content as content
from . import domain as domain
from . import title as title


def extract(url: str, html_text: str = None) -> Dict:
    # first fetch the content if we need to
    raw_html = http.fetch(url) if html_text is None else html_text
    # parse out the metadata we care about
    pub_date_str = htmldate.find_date(raw_html, url=url, original_date=True)
    pub_date = dateparser.parse(pub_date_str)
    article = content.from_html(url, raw_html)
    canonical_domain = domain.get_canonical(url)
    article_title = title.article_title(raw_html, article['title'])
    try:
        language = langid.classify(article['text'])[0]
    except Exception as _:
        language = None
    return dict(
        publication_date=pub_date,
        text_content=article['text'],
        text_extraction_method=article['extraction_method'],
        canonical_domain=canonical_domain,
        article_title=article_title,
        language=language,
    )


