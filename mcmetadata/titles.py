from typing import Optional
import re
import logging
import string

from . import html as html

logger = logging.getLogger(__name__)

title_meta_pattern = "(?:og:title|hdl|twitter:title|dc.title|dcterms.title|title)"
meta_tag_pattern_1 = re.compile(r"<meta[^>]*(?:name|property)=.%s.[^>]*content=\"([^\"]+)\"" % title_meta_pattern,
                                re.S | re.I)
meta_tag_pattern_2 = re.compile(r"<meta[^>]*(?:name|property)=.%s.[^>]*content=\'([^\']+)\'" % title_meta_pattern,
                                re.S | re.I)

title_tag_pattern = re.compile(r"<title(?: [^>]*)?>(.*?)</title>", re.S | re.I)

whitespace_pattern = re.compile(r'\s+')

home_pattern = re.compile(r'^\W*home\W*', re.I)


def from_html(html_text: str, fallback_title: str = None, trim_to_length: int = 0) -> Optional[str]:
    """
    Parse the content for tags that might indicate the story's title. Tuned for online news webpages.
    stc: https://github.com/mediacloud/backend/blob/master/apps/common/src/python/mediawords/util/parse_html.py#L160
    Arguments:
    :html_text - html to parse for title
    :fallback_title - use this title if we can't fine one
    :trim_to_length - if specified, trim the title to this length
    Returns: the title of the article as a string
    """

    # looks for meta tag titles first
    match = meta_tag_pattern_1.search(html_text)
    title = match.group(1) if match else None
    if title is None:  # check for same pattern in single quotes
        match = meta_tag_pattern_2.search(html_text)
        title = match.group(1) if match else None

    # if no meta tag, check for title tags
    if title is None:
        match = title_tag_pattern.search(html_text)
        title = match.group(1) if match else None

    # if we found one, clean it up
    if title:
        title = html.strip_tags(title)
        title = title.strip()
        title = whitespace_pattern.sub(' ', title)
        # Moved from _get_medium_title_from_response()
        title = home_pattern.sub('', title)

    # if we didn't find anything, fall back on what the upstream code might have found as a candidate
    if title is None or title == '':
        title = fallback_title

    # optionally trim to a max length
    if trim_to_length > 0:
        title = title[0:trim_to_length]

    return title


params_pattern = re.compile(r'\&#?[a-z0-9]*', re.I)
separator_pattern = re.compile(r'(?:\- )|[:|]')
MAX_TITLE_LENGTH = 1024
SEPARATOR_PLACEHOLDER = "| "


def normalize_title(story_title: str, publication_name: Optional[str] = None) -> str:
    """
    Clean up the news article title, and also try to remove any publication name embedded in it.
    Useful for comparing hashes to identify duplicate stories at different URLs.
    """
    new_story_title = _normalize_text_for_comparison(story_title)
    if publication_name is None:
        return new_story_title
    new_story_title_parts = new_story_title.split(SEPARATOR_PLACEHOLDER)
    if len(new_story_title_parts) == 1:
        return new_story_title_parts
    first_part = new_story_title_parts[0].strip()
    if first_part == new_story_title:
        return new_story_title
    normalized_pub_name = _normalize_text_for_comparison(publication_name)
    if first_part == normalized_pub_name:
        return (" {} ".format(SEPARATOR_PLACEHOLDER)).join(new_story_title_parts[1:])
    if len(first_part) < 32:
        return new_story_title
    return first_part


def _normalize_text_for_comparison(title_part: str) -> str:
    new_title = title_part
    new_title = html.strip_tags(new_title)  # junk HTML
    new_title = params_pattern.sub(" ", new_title)  # URL params
    new_title = new_title.lower()
    new_title = separator_pattern.sub(SEPARATOR_PLACEHOLDER, new_title)  # keep all separators
    new_title = new_title.strip(string.punctuation)  # ditch all punctuation
    new_title = whitespace_pattern.sub(" ", new_title)  # cleanup remaining whitespace
    new_title = new_title[:MAX_TITLE_LENGTH]
    return new_title.strip()
