import datetime as dt
import importlib.metadata
import logging
import time
from typing import Any, Mapping, MutableMapping, Optional, cast

from . import content, dates, languages, structured_data, titles, urls, webpages

# work around to read the version from the pyproject.toml so it is maintained in one place
try:
    __version__ = importlib.metadata.version("mediacloud-metadata")
except importlib.metadata.PackageNotFoundError:  # pragma: no cover - vendored fallback
    __version__ = "1.4.1+vendored"

logger = logging.getLogger(__name__)

# Publication dates more than this many days in the future will be ignored (because they are probably bad guesses)
MAX_FUTURE_PUB_DATE = 90

STAT_NAMES = [
    "total",
    "fetch",
    "url",
    "pub_date",
    "content",
    "title",
    "language",
    "structured_data",
]
stats: dict[str, float] = cast(dict[str, float], dict.fromkeys(STAT_NAMES, 0.0))

# from https://github.com/counterdata-network/story-processor/blob/03f6de5dfdb69f6d3ae26972844b62eaf8f0f39d/processor/__init__.py#L49C1-L56C2
LOGGERS_IGNORE_INFO = [
    # NOTE! in sorted order!
    "readability.readability",
    "trafilatura.core",
    "trafilatura.htmlprocessing",
    "trafilatura.metadata",
    "trafilatura.readability_lxml",
    "trafilatura.xml",
]

# from https://github.com/counterdata-network/story-processor/blob/03f6de5dfdb69f6d3ae26972844b62eaf8f0f39d/processor/__init__.py#L93-L96
SENTRY_LOGGERS_TO_IGNORE = [
    # NOTE! in sorted order!
    "htmldate.utils",
    "trafilatura.core",
    "trafilatura.utils",
]


def extract(
    url: str,
    html_text: Optional[str] = None,
    include_other_metadata: Optional[bool] = False,
    defaults: Mapping[str, Any] = {},
    overrides: Mapping[str, Any] = {},
    stats_accumulator: MutableMapping[str, float] | None = None,
) -> dict:
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
    if (
        stats_accumulator is None
    ):  # can't default to global because of Python reference handling in defaults
        accumulator: MutableMapping[str, float] = stats
    else:
        accumulator = stats_accumulator
    use_other_metadata = bool(include_other_metadata)
    t0 = time.monotonic()
    # first fetch the real content (if we need to)
    t1 = t0
    if html_text is None:
        raw_html, response = webpages.fetch(url)
        # check for archived URLs
        if "memento-datetime" in response.headers:
            try:
                final_url = response.links["original"][
                    "url"
                ]  # the original url archived
            except KeyError:
                # maybe the responder doesn't provide the desired headers, so just fall back on the full URL because
                # there's nothing else we can really do
                final_url = response.url  # followed all the redirects
        else:
            final_url = response.url  # followed all the redirects
    else:
        final_url = (
            url  # trust that the user knows which URL the content actually came from
        )
        raw_html = html_text
    fetch_duration = time.monotonic() - t1
    accumulator["fetch"] += fetch_duration

    # url
    t1 = time.monotonic()
    normalized_url = urls.normalize_url(final_url)
    is_homepage_url = urls.is_homepage_url(url)
    is_shortened_url = urls.is_shortened_url(url)
    url_duration = time.monotonic() - t1
    accumulator["url"] += url_duration

    if "canonical_domain" in overrides:
        canonical_domain = overrides["canonical_domain"]
    else:
        canonical_domain = urls.canonical_domain(final_url)

    # =========================================================================
    # STRUCTURED DATA EXTRACTION (JSON-LD, meta tags) - do this first!
    # These are the most reliable sources for title, author, and pub date.
    # =========================================================================
    t1 = time.monotonic()
    struct_data = structured_data.extract_from_html(raw_html, final_url)
    structured_data_duration = time.monotonic() - t1
    accumulator["structured_data"] += structured_data_duration

    # Use structured data as defaults for subsequent extraction
    # This allows other extractors to fill in any missing fields
    struct_title = struct_data.get("title")
    struct_author = struct_data.get("author")
    struct_pub_date = struct_data.get("publish_date")
    struct_source = struct_data.get("source")  # 'json_ld' or 'meta_tags'

    # pub date stuff
    t1 = time.monotonic()
    max_pub_date = dt.datetime.now() + dt.timedelta(days=+MAX_FUTURE_PUB_DATE)
    if "publication_date" in overrides:
        pub_date = overrides["publication_date"]
    elif struct_pub_date:
        # Try to parse the structured date
        try:
            import dateparser

            parsed_date = dateparser.parse(struct_pub_date)
            if parsed_date and parsed_date <= max_pub_date:
                pub_date = parsed_date
            else:
                pub_date = None
        except Exception:
            pub_date = None
        # If structured date parsing failed, fall back to dates module
        if pub_date is None:
            default_date = defaults.get("publication_date") if defaults else None
            pub_date = dates.guess_publication_date(
                raw_html, final_url, max_date=max_pub_date, default_date=default_date
            )
    else:
        default_date = defaults.get("publication_date") if defaults else None
        pub_date = dates.guess_publication_date(
            raw_html, final_url, max_date=max_pub_date, default_date=default_date
        )
    pub_date_duration = time.monotonic() - t1
    accumulator["pub_date"] += pub_date_duration

    # content
    t1 = time.monotonic()
    if "text_content" in overrides:
        article = dict(
            extraction_method=content.METHOD_OVERRIDEN, text=overrides["text_content"]
        )
    else:
        article = content.from_html(final_url, raw_html, use_other_metadata)
    content_duration = time.monotonic() - t1
    accumulator["content"] += content_duration

    # title - prefer structured data (JSON-LD/meta tags) over content extraction
    t1 = time.monotonic()
    if "article_title" in overrides:
        article_title = overrides["article_title"]
        title_extraction_method = "override"
    elif struct_title:
        # Use structured data title (from JSON-LD or meta tags)
        article_title = struct_title
        title_extraction_method = f"structured_{struct_source or 'unknown'}"
    else:
        # Fall back to content-based extraction
        article_title = titles.from_html(raw_html, article["title"])
        title_extraction_method = "titles_module"
        if article_title is None:
            article_title = defaults.get("article_title") if defaults else None
            if article_title:
                title_extraction_method = "default"
    normalized_title = titles.normalize_title(article_title)
    title_duration = time.monotonic() - t1
    accumulator["title"] += title_duration

    # language
    t1 = time.monotonic()
    if "language" in overrides:
        full_language = overrides["language"]
    else:
        full_language = languages.from_html(
            raw_html, article["text"]
        )  # could be something like "pt-br"
        if full_language is None:
            full_language = defaults.get("language") if defaults else None
    language_duration = time.monotonic() - t1
    accumulator["language"] += language_duration

    # canonical url
    if "canonical_url" in overrides:
        canonical_url = overrides["canonical_url"]
    else:
        canonical_url = struct_data.get("canonical_url") or article.get(
            "canonical_url"
        )

    total_duration = time.monotonic() - t0
    accumulator["total"] += total_duration

    # Determine author - prefer structured data over content extraction
    if struct_author:
        final_author = struct_author
        author_extraction_method = f"structured_{struct_source or 'unknown'}"
    elif use_other_metadata and article.get("authors"):
        # Use authors from content extraction if available
        authors_list = article.get("authors", [])
        if isinstance(authors_list, list):
            final_author = "; ".join(str(a) for a in authors_list if a)
        else:
            final_author = str(authors_list) if authors_list else None
        author_extraction_method = "content_extraction"
    else:
        final_author = None
        author_extraction_method = None

    results = dict(
        original_url=url,
        url=final_url,
        normalized_url=normalized_url,
        unique_url_hash=urls.unique_url_hash(final_url),
        canonical_domain=canonical_domain,
        canonical_url=canonical_url,
        publication_date=pub_date,
        language=(
            full_language[:2] if full_language else full_language
        ),  # keep this as a two-letter code, like "en"
        full_language=full_language,  # could be a full region language code, like "en-AU"
        text_extraction_method=article["extraction_method"],
        title_extraction_method=title_extraction_method,
        author_extraction_method=author_extraction_method,
        article_title=article_title,
        normalized_article_title=normalized_title,
        article_author=final_author,  # NEW: author from structured data or content
        text_content=article["text"],
        is_homepage=is_homepage_url,
        is_shortened=is_shortened_url,
        version=__version__,
    )

    # Add wire service signals if detected
    wire_signals = struct_data.get("wire_signals")
    if wire_signals and wire_signals.get("detection_methods"):
        results["wire_signals"] = wire_signals

    # Provide raw_html so callers can run downstream heuristics (e.g., script parsing)
    results["raw_html"] = raw_html
    if use_other_metadata:
        # other metadata we've done less robust validation on, but might be useful
        results["other"] = dict(
            raw_title=article["title"] if "title" in article else None,
            raw_publish_date=(
                article["potential_publish_date"]
                if "potential_publish_date" in article
                else None
            ),
            top_image_url=(
                article["top_image_url"] if "top_image_url" in article else None
            ),
            authors=article["authors"] if "authors" in article else None,
            structured_data_source=struct_source,  # Track which structured source was used
        )

    return results


def reset_stats():
    global stats
    stats = cast(dict[str, float], dict.fromkeys(STAT_NAMES, 0.0))


def ignore_loggers() -> None:
    """
    Quiet down logging from libraries this module uses.
    """
    for name in LOGGERS_IGNORE_INFO:
        logging.getLogger(name).setLevel(logging.WARNING)


def sentry_ignore_loggers() -> None:
    """
    Tell sentry.io SDK to ignore loggers that can consume event
    quotas.  It's possible that this alone is sufficient for that
    purpose, and ignore_loggers need not be called if sentry quota
    is your only concern.
    """
    import sentry_sdk.integrations.logging

    for name in SENTRY_LOGGERS_TO_IGNORE:
        sentry_sdk.integrations.logging.ignore_logger(name)
