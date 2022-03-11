from typing import Optional
import re
import logging

from . import html as html

logger = logging.getLogger(__name__)


def from_html(html_text: str, fallback_title: str = None, trim_to_length: int = 0) -> Optional[str]:
    """
    Parse the content for tags that might indicate the story's title.
    stc: https://github.com/mediacloud/backend/blob/master/apps/common/src/python/mediawords/util/parse_html.py#L160
    Arguments:
    :html_text - html to parse for title
    :fallback_title - use this title if we can't fine one
    :trim_to_length - if specified, trim the title to this length
    Returns: the title of the article as a string
    """

    title_meta_re = r'(?:og:title|hdl|twitter:title|dc.title|dcterms.title|title)'

    match = re.search(r"<meta (?:name|property)=.%s. content=\"([^\"]+)\"" % title_meta_re, html_text, flags=re.S | re.I)
    title = match.group(1) if match else None

    if title is None:
        match = re.search(r"<meta (?:name|property)=.%s. content=\'([^\']+)\'" % title_meta_re, html_text, flags=re.S | re.I)
        title = match.group(1) if match else None

    if title is None:
        match = re.search(r"<title(?: [^>]*)?>(.*?)</title>", html_text, flags=re.S | re.I)
        title = match.group(1) if match else None

    if title:
        title = html.strip_tags(title)
        title = title.strip()
        title = re.sub(r'\s+', ' ', title)

        # Moved from _get_medium_title_from_response()
        title = re.sub(r'^\W*home\W*', '', title, flags=re.I)

    if title is None or title == '':
        title = fallback_title

    if trim_to_length > 0:
        title = title[0:trim_to_length]

    return title
