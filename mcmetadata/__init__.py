from typing import Dict, Optional, Any, Mapping
import logging
import datetime as dt
import time

from . import webpages
from . import content
from . import urls
from . import titles
from . import languages
from . import dates

__version__ = "0.11.0"

logger = logging.getLogger(__name__)

# Publication dates more than this many days in the future will be ignored (because they are probably bad guesses)
MAX_FUTURE_PUB_DATE = 90

STAT_NAMES = ['total', 'fetch', 'url', 'pub_date', 'content', 'title', 'language']
stats = {s: 0 for s in STAT_NAMES}


def extract(url: str, html_text: Optional[str] = None, include_other_metadata: Optional[bool] = False,
            defaults: Mapping[str, Any] = {}, overrides: Mapping[str, Any] = {},
            stats_accumulator: Mapping[str, int] = None) -> Dict:
    """
    The core method of this library - returns all the useful information extracted from the HTML of the next
    article at the supplied URL.

    :param str url: A valid URL to some news article online that we want to extract info from
    :param str html_text: (optional) Supply the HTML text you already fetched from that URL. If None, we will download
                          the HTML for you, with some reasonable timeout defaults.
    :param bool include_other_metadata: Pass in true to top_image, authors, and other things returned under an `other`
                                        property in the results. Warning - this can slow down extraction by around 5x.
                                        In addition, we haven't tested the robustness and accuracy of these at scale.
    :param defaults: (optional) A dictionary of default values to use as fallback values if specific metadata can't
                     be found. Keys should be the same as the keys in the returned dictionary (supports
                     `publication_date`, `text_content`, `article_title`, and `language`).
    :param overrides: (optional) A dictionary of values to use instead of trying to parse them out from the content.
                     Keys should be the same as the keys in the returned dictionary (supports `publication_date`,
                     `article_title`, and `language`). This can be useful for speed optimizations,
                     since if an override is provided then that extraction method won't be called.
    :param stats_accumulator: (optional) A dictionary of stats to accumulate. This is useful if you want to track the
                 stats yourself _instead_ of in the module-level `stats` counter. If you pass this in then the
                 timings for the call will _not_ be added to the module-level `stats` counter. Should contain keys
                 for `STAT_NAMES` (see above).
    """
    if stats_accumulator is None:  # can't default to global because of Python reference handling in defaults
        stats_accumulator = stats
    t0 = time.monotonic()
    # first fetch the real content (if we need to)
    t1 = t0
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
    fetch_duration = time.monotonic() - t1
    stats_accumulator['fetch'] += fetch_duration

    # url
    t1 = time.monotonic()
    normalized_url = urls.normalize_url(final_url)
    canonical_domain = urls.canonical_domain(final_url)
    is_homepage_url = urls.is_homepage_url(url)
    is_shortened_url = urls.is_shortened_url(url)
    url_duration = time.monotonic() - t1
    stats_accumulator['url'] += url_duration

    # pub date stuff
    t1 = time.monotonic()
    max_pub_date = dt.datetime.now() + dt.timedelta(days=+MAX_FUTURE_PUB_DATE)
    if 'publication_date' in overrides:
        pub_date = overrides['publication_date']
    else:
        default_date = defaults.get('publication_date') if defaults else None
        pub_date = dates.guess_publication_date(raw_html, final_url, max_date=max_pub_date, default_date=default_date)
    pub_date_duration = time.monotonic() - t1
    stats_accumulator['pub_date'] += pub_date_duration

    # content
    t1 = time.monotonic()
    if 'text_content' in overrides:
        article = dict(extraction_method = content.METHOD_OVERRIDEN,
                       text=overrides['text_content'])
    else:
        article = content.from_html(final_url, raw_html, include_other_metadata)
    content_duration = time.monotonic() - t1
    stats_accumulator['content'] += content_duration

    # title
    t1 = time.monotonic()
    if 'article_title' in overrides:
        article_title = overrides['article_title']
    else:
        article_title = titles.from_html(raw_html, article['title'])
        if article_title is None:
            article_title = defaults.get('article_title') if defaults else None
    normalized_title = titles.normalize_title(article_title)
    title_duration = time.monotonic() - t1
    stats_accumulator['title'] += title_duration

    # language
    t1 = time.monotonic()
    if 'language' in overrides:
        full_language = overrides['language']
    else:
        full_language = languages.from_html(raw_html, article['text'])  # could be something like "pt-br"
        if full_language is None:
            full_language = defaults.get('language') if defaults else None
    language_duration = time.monotonic() - t1
    stats_accumulator['language'] += language_duration

    total_duration = time.monotonic() - t0
    stats_accumulator['total'] += total_duration

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
            raw_title=article['title'] if 'title' in article else None,
            raw_publish_date=article['potential_publish_date'] if 'potential_publish_date' in article else None,
            top_image_url=article['top_image_url'] if 'top_image_url' in article else None,
            authors=article['authors'] if 'authors' in article else None,
        )

    return results


def reset_stats():
    global stats
    stats = {s: 0 for s in STAT_NAMES}