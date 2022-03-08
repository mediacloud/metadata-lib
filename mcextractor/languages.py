from typing import Optional
import py3langid as langid
import logging

logger = logging.getLogger(__name__)


def from_text(text: str) -> Optional[str]:
    try:
        lang, prob = langid.classify(text)
        return lang
    except Exception as _:
        return None
