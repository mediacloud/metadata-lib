from typing import Optional
import re
import logging
import string
from html import unescape

from . import text

logger = logging.getLogger(__name__)

SHORT_TITLE_THRESHOLD = 20

title_meta_pattern = "(?:og:title|hdl|twitter:title|dc.title|dcterms.title|title)"
meta_tag_pattern_1 = re.compile(r"<meta[^>]*(?:name|property)=.%s.[^>]* content=\"([^\"]+)\"" % title_meta_pattern,
                                re.S | re.I)
meta_tag_pattern_2 = re.compile(r"<meta[^>]*(?:name|property)=.%s.[^>]* content=\'([^\']+)\'" % title_meta_pattern,
                                re.S | re.I)

title_tag_pattern = re.compile(r"<title(?: [^>]*)?>(.*?)</title>", re.S | re.I)

h1_tag_pattern = re.compile(r"<h1(?: [^>]*)?>(.*?)</h1>", re.S | re.I)

whitespace_pattern = re.compile(r'\s+')

home_pattern = re.compile(r'^\W+home\W+', re.I)


def from_html(html_text: str, fallback_title: str = None, trim_to_length: int = 0) -> Optional[str]:
    """
    Parse the content for tags that might indicate the story's title. Tuned for online news webpages.
    src: https://github.com/mediacloud/backend/blob/master/apps/common/src/python/mediawords/util/parse_html.py#L160
    Arguments:
    :html_text - html to parse for title
    :fallback_title - use this title if we can't fine one
    :trim_to_length - if specified, trim the title to this length
    Returns: the title of the article as a string
    """

    # looks for meta tag titles first
    match = meta_tag_pattern_1.search(html_text)
    title = match.group(1) if match else None
    if (title is None) or (len(title) < SHORT_TITLE_THRESHOLD):  # check for same pattern in single quotes
        match = meta_tag_pattern_2.search(html_text)
        title = match.group(1) if match else None

    # if no meta tag, check for title tags
    if title is None or (len(title) < SHORT_TITLE_THRESHOLD):
        match = title_tag_pattern.search(html_text)
        title = match.group(1).strip() if match else None

    # if we found one, clean it up
    if title and len(title) > 0:
        title = text.strip_tags(title)
        title = unescape(title)
        title = title.strip()
        title = whitespace_pattern.sub(' ', title)
        # Moved from _get_medium_title_from_response()
        title = home_pattern.sub('', title)

    # if we didn't find anything, fall back on what the upstream code might have found as a candidate
    if title is None or title == '':
        title = fallback_title

    if (title is not None) and len(title) > 0:
        # clean off any prefix/suffix
        normalized_title = _normalize_text_for_comparison(title)
        title_parts = separator_pattern.split(normalized_title)
        # title_parts = normalized_title.split(SEPARATOR_PLACEHOLDER)
        if len(title_parts) > 2:  # there are multiple parts, could be prefix, suffice, content, or some combo
            # we see media-name suffixes a lot more than prefixes, so err on the side of removing suffix and keeping prefix
            if len(title_parts[0]) < SHORT_TITLE_THRESHOLD:
                title = normalized_title[0: -len(title_parts[-1])-2]
            else:
                # but it could be multiple suffixes, so check by length
                last_part_index = len(title_parts) - 1  # start with the last one
                while len(title_parts[last_part_index]) < SHORT_TITLE_THRESHOLD:
                    last_part_index -= 1
                if last_part_index == len(title_parts) - 1:  # err on the side of keeping just the first part
                    last_part_index = 0
                end_str_index = sum([len(title_parts[i]) + 3 for i in range(last_part_index+1, len(title_parts))])
                title = normalized_title[0:-end_str_index]
        elif len(title_parts) > 1:  # there is a single prefix or suffix we might want to remove
            if len(title_parts[0]) < SHORT_TITLE_THRESHOLD:  # this is probably a prefix
                if len(title_parts[1]) < SHORT_TITLE_THRESHOLD:  # if both short, then probable a suffixed title
                    title = normalized_title[:-len(title_parts[1]) - 2:]
                else:  # second part is long, so consider it a prefixed title
                    title = normalized_title[len(title_parts[0])+2:]
            else:  # probably one or more suffixes
                title = title_parts[0]

    # if a single h1 on page, and it is subset of found title, go with that (to eliminate post-fixed titles in meta tags)
    match = h1_tag_pattern.search(html_text)
    if match and len(match.groups()) == 1:
        h1_title = unescape(text.strip_tags(match.group(1))).strip()
        if (len(h1_title) > SHORT_TITLE_THRESHOLD) and (h1_title in title.strip()):
            title = h1_title

    # optionally trim to a max length
    if trim_to_length > 0:
        title = title[0:trim_to_length]

    # strip again here because there might be dangling spaces from prefix/suffix cleaning
    return title.strip() if title else None


params_pattern = re.compile(r'\&#?[a-z0-9]*', re.I)
separator_pattern = re.compile(r' [:\|-] ')
MAX_TITLE_LENGTH = 1024
SEPARATOR_PLACEHOLDER = "| "


def normalize_title(story_title: str) -> str:
    """
    Useful for comparing hashes to identify duplicate stories at different URLs.
    """
    new_story_title = _normalize_text_for_comparison(story_title)
    new_story_title = new_story_title.lower()
    return new_story_title


def _normalize_text_for_comparison(title_part: str) -> str:
    new_title = title_part
    new_title = text.strip_tags(new_title)  # junk HTML
    new_title = params_pattern.sub(" ", new_title)  # URL params
    #new_title = separator_pattern.sub(SEPARATOR_PLACEHOLDER, new_title)  # keep all separators
    new_title = new_title.strip(string.punctuation)  # ditch all punctuation
    new_title = whitespace_pattern.sub(" ", new_title)  # cleanup remaining whitespace
    new_title = new_title[:MAX_TITLE_LENGTH]
    return new_title.strip()
