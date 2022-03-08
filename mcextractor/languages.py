from typing import Optional
import cld2
import logging

logger = logging.getLogger(__name__)


def from_text(text: str) -> Optional[str]:
    is_reliable, text_bytes_found, details = cld2.detect(text)
    if is_reliable and len(details) > 0:
        return details[0][1]
    return None
