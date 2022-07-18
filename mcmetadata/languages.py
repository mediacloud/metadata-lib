from typing import Optional
import py3langid as langid
import re
import logging

logger = logging.getLogger(__name__)

meta_tag_pattern1 = re.compile(r"<meta[^>]* (?:name|property)=.dc\.language.[^>]* content=\"([^\"]+)\"", re.S | re.I)
meta_tag_pattern2 = re.compile(r"<meta[^>]* (?:http-equiv)=.Content-Language.[^>]* content=\"([^\"]+)\"", re.S | re.I)
html_tag_pattern = re.compile(r"<html[^>]* (?:xml:lang|lang)=\"([^\"]+)\"", re.S | re.I)


def from_html(html: str, content: Optional[str] = None) -> Optional[str]:
    """
    Try to guess document langauge from metadata, falling back to text-based guess if desired
    """
    # first check for document-level tags
    dc_language_tag_matches = meta_tag_pattern1.search(html)
    if dc_language_tag_matches:
        return dc_language_tag_matches.group(1)
    http_equv_language_tag_matches = meta_tag_pattern2.search(html)
    if http_equv_language_tag_matches:
        return http_equv_language_tag_matches.group(1)
    # fall back to HTML-level language
    html_language_matches = html_tag_pattern.search(html)
    if html_language_matches:
        return html_language_matches.group(1)
    # now try text if included
    if content:
        return _from_text(content)
    # can't find a language
    return None


def _from_text(text: str) -> Optional[str]:
    try:
        lang, prob = langid.classify(text)
        return lang
    except Exception as _:
        return None
