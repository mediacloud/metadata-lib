from typing import Dict, Optional
import logging
import datetime as dt
import time

from . import webpages
from . import content
from . import urls
from . import titles
from . import languages
from . import dates

__version__ = "0.8.0"

logger = logging.getLogger(__name__)

# Publication dates more than this many days in the future will be ignored (because they are probably bad guesses)
MAX_FUTURE_PUB_DATE = 90

STAT_NAMES = ['total', 'fetch', 'url', 'pub_date', 'content', 'title', 'language']
stats = {s: 0 for s in STAT_NAMES}


def extract(url: str, html_text: Optional[str] = None, include_other_metadata: Optional[bool] = False) -> Dict:
    """
    The core method of this library - returns all the useful information extracted from the HTML of the next
    article at the supplied URL.

    :param str url: A valid URL to some news article online that we want to extract info from
    :param str html_text: (optional) Supply the HTML text you already fetched from that URL. If None, we will download
                          the HTML for you, with some reasonable timeout defaults.
    :param bool include_other_metadata: Pass in true to top_image, authors, and other things returned under an `other`
                                        property in the results. Warning - this can slow down extraction by around 5x.
                                        In addition, we haven't tested the robustness and accuracy of these at scale.
    """
    t0 = time.time()
    # first fetch the real content (if we need to)
    t1 = time.time()
    if html_text is None:
        raw_html, response = webpages.fetch(url)
        # check for archived URLs
        if 'memento-datetime' in response.headers:
            try:
                final_url = response.links['original']['url']  # the original url archived
            except KeyError:
                # maybe the responder doesn't provide the desired headers, so just fall back on the full URL because
                # there's nothing else we can really do
                final_url = response.url  # followed all the redirects
        else:
            final_url = response.url  # followed all the redirects
    else:
        final_url = url  # trust that the user knows which URL the content actually came from
        raw_html = html_text
    fetch_duration = time.time() - t1
    stats['fetch'] += fetch_duration

    # url
    t1 = time.time()
    normalized_url = urls.normalize_url(final_url)
    canonical_domain = urls.canonical_domain(final_url)
    is_homepage_url = urls.is_homepage_url(url)
    is_shortened_url = urls.is_shortened_url(url)
    url_duration = time.time() - t1
    stats['url'] += url_duration

    # pub date stuff
    t1 = time.time()
    max_pub_date = dt.datetime.now() + dt.timedelta(days=+MAX_FUTURE_PUB_DATE)
    pub_date = dates.guess_publication_date(raw_html, final_url, max_date=max_pub_date)
    pub_date_duration = time.time() - t1
    stats['pub_date'] += pub_date_duration

    # content
    t1 = time.time()
    article = content.from_html(final_url, raw_html, include_other_metadata)
    content_duration = time.time() - t1
    stats['content'] += content_duration

    # title
    t1 = time.time()
    article_title = titles.from_html(raw_html, article['title'])
    normalized_title = titles.normalize_title(article_title)
    title_duration = time.time() - t1
    stats['title'] += title_duration

    # language
    t1 = time.time()
    full_language = languages.from_html(raw_html, article['text'])  # could be something like "pt-br"
    language_duration = time.time() - t1
    stats['language'] += language_duration

    total_duration = time.time() - t0
    stats['total'] += total_duration

    results = dict(
        original_url=url,
        url=final_url,
        normalized_url=normalized_url,
        canonical_domain=canonical_domain,
        publication_date=pub_date,
        language=full_language[:2] if full_language else full_language,  # keep this as a two-letter code, like "en"
        full_language=full_language,  # could be a full region language code, like "en-AU"
        text_extraction_method=article['extraction_method'],
        article_title=article_title,
        normalized_article_title=normalized_title,
        text_content=article['text'],
        is_homepage=is_homepage_url,
        is_shortened=is_shortened_url,
        version=__version__,
    )
    if include_other_metadata:
        # other metadata we've done less robust validation on, but might be useful
        results['other'] = dict(
            raw_title=article['title'],
            raw_publish_date=article['potential_publish_date'],
            top_image_url=article['top_image_url'],
            authors=article['authors'],
        )

    return results
