from typing import Optional
import py3langid as langid
import re
import logging
import trafilatura.utils

logger = logging.getLogger(__name__)

meta_tag_pattern1 = re.compile(r"<meta[^>]* (?:name|property)=.dc\.language.[^>]* content=\"([^\"]+)\"", re.S | re.I)
meta_tag_pattern2 = re.compile(r"<meta[^>]* (?:http-equiv)=.Content-Language.[^>]* content=\"([^\"]+)\"", re.S | re.I)
html_tag_pattern = re.compile(r"<html[^>]* (?:xml:lang|lang)=\"([^\"]+)\"", re.S | re.I)


def from_html(html: str, content: Optional[str] = None) -> Optional[str]:
    """
    Try to guess document langauge from metadata, falling back to text-based guess if desired
    """
    language_indication = None  # the language metadata suggests
    language_guess = None  # the detected language from an algorithm
    # first check for document-level tags
    dc_language_tag_matches = meta_tag_pattern1.search(html)
    http_equiv_language_tag_matches = meta_tag_pattern2.search(html)
    html_language_matches = html_tag_pattern.search(html)   # fall back to HTML-level language
    if dc_language_tag_matches:
        language_indication = dc_language_tag_matches.group(1)
    elif http_equiv_language_tag_matches:
        language_indication = http_equiv_language_tag_matches.group(1)
    elif html_language_matches:
        language_indication = html_language_matches.group(1)
    # also try to guess the language
    if content:
        language_guess = _from_text(content)
    # not make a decision based on the two language pieces of info
    return _pick_between_languages(language_indication, language_guess)


def _pick_between_languages(indication: Optional[str], guess: Optional[str]) -> Optional[str]:
    if (indication is not None) and (guess is not None):
        # if they are the same language then return the one with higher resolution
        if guess.startswith(indication):
            return guess
        if indication.startswith(guess):
            return indication
        # Prefer the detected language if both are set, because the indication often comes from an unconfiured CMS
        # This happens a lot in non-english langauges
        logger.debug("Language mismatch - indicated {} but guessed {}".format(indication, guess))
        return guess
    elif (indication is None) and (guess is not None):
        return guess
    elif (indication is not None) and (guess is None):
        return indication
    # can't find a language
    return None


def _from_text(content: str) -> Optional[str]:
    # make sure a misleading encoding doesn't mess us up
    decoded_content = trafilatura.utils.decode_file(content)
    try:
        lang, prob = langid.classify(decoded_content)
        return lang
    except Exception as _:
        return None
