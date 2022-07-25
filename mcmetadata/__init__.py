from typing import Dict
import logging
import datetime as dt

from . import webpages
from . import content
from . import urls
from . import titles
from . import languages
from . import dates

__version__ = "0.7.2"

logger = logging.getLogger(__name__)

# Publication dates more than this many days in the future will be ignored (because they are probably bad guesses)
MAX_FUTURE_PUB_DATE = 90


def extract(url: str, html_text: str = None) -> Dict:
    # first fetch the real content (if we need to)
    if html_text is None:
        raw_html, response = webpages.fetch(url)
        # check for archived URLs
        if 'memento-datetime' in response.headers:
            final_url = response.links['original']['url']  # the original url archived
        else:
            final_url = response.url  # followed all the redirects
    else:
        final_url = url  # trust that the user knows which URL the content actually came from
        raw_html = html_text
    # parse out the metadata we care about
    max_pub_date = dt.datetime.now() + dt.timedelta(days=+MAX_FUTURE_PUB_DATE)
    pub_date = dates.guess_publication_date(raw_html, final_url, max_date=max_pub_date)
    article = content.from_html(final_url, raw_html)
    article_title = titles.from_html(raw_html, article['title'])
    full_langauge = languages.from_html(raw_html, article['text'])  # could be something like "pt-br"
    return dict(
        original_url=url,
        url=final_url,
        normalized_url=urls.normalize_url(final_url),
        canonical_domain=urls.canonical_domain(final_url),
        publication_date=pub_date,
        language=full_langauge[:2] if full_langauge else full_langauge,  # keep this as a two-letter code, like "en"
        full_langauge=full_langauge,  # could be a full region language code, like "en-AU"
        text_extraction_method=article['extraction_method'],
        article_title=article_title,
        normalized_article_title=titles.normalize_title(article_title),
        text_content=article['text'],
        version=__version__,
    )
