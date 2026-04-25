"""
Structured data extraction from HTML (JSON-LD, OpenGraph, meta tags).

This module extracts metadata from standardized structured data formats
before falling back to content-based extraction. These sources are typically
more reliable than parsing article content directly.

Extracts:
- title/headline
- author
- publication date
- description
- wire service signals (for syndicated content detection)
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# JSON-LD script block pattern
_JSONLD_BLOCK_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

# Meta tag patterns - both attribute orderings
_META_OG_TITLE_RE = re.compile(
    r'<meta\s+(?:property|name)=["\']og:title["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_OG_TITLE_ALT_RE = re.compile(
    r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:title["\']',
    re.IGNORECASE,
)

_META_AUTHOR_RE = re.compile(
    r'<meta\s+(?:property|name)=["\'](?:article:author|author)["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_AUTHOR_ALT_RE = re.compile(
    r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\'](?:article:author|author)["\']',
    re.IGNORECASE,
)

_META_PUBTIME_RE = re.compile(
    r'<meta\s+(?:property|name)=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_PUBTIME_ALT_RE = re.compile(
    r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']article:published_time["\']',
    re.IGNORECASE,
)

_META_DESCRIPTION_RE = re.compile(
    r'<meta\s+(?:property|name)=["\'](?:og:description|description)["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_DESCRIPTION_ALT_RE = re.compile(
    r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\'](?:og:description|description)["\']',
    re.IGNORECASE,
)

# Wire service distributor meta tags
_META_DISTRIBUTOR_CATEGORY_RE = re.compile(
    r'<meta\s+(?:property|name)=["\']article:distributor_category["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_DISTRIBUTOR_CATEGORY_ALT_RE = re.compile(
    r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']article:distributor_category["\']',
    re.IGNORECASE,
)

_META_DISTRIBUTOR_NAME_RE = re.compile(
    r'<meta\s+(?:property|name)=["\']article:distributor_name["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_DISTRIBUTOR_NAME_ALT_RE = re.compile(
    r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']article:distributor_name["\']',
    re.IGNORECASE,
)

# Canonical URL pattern
_CANONICAL_LINK_RE = re.compile(
    r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', re.IGNORECASE
)
_CANONICAL_LINK_ALT_RE = re.compile(
    r'<link\s+href=["\']([^"\']+)["\']\s+rel=["\']canonical["\']', re.IGNORECASE
)

# Article types to process in JSON-LD
ARTICLE_TYPES = frozenset(
    {
        "newsarticle",
        "article",
        "reportagenewsarticle",
        "webpage",
        "blogposting",
        "socialmediaposting",
    }
)


def extract_from_html(html_text: str, url: str | None = None) -> dict[str, Any]:
    """
    Extract structured metadata from HTML.

    Tries sources in order of reliability:
    1. JSON-LD structured data (schema.org - most standardized)
    2. OpenGraph and standard meta tags
    3. Canonical URL (for wire detection)

    Args:
        html_text: Raw HTML content
        url: Original URL (used for cross-domain wire detection)

    Returns:
        Dictionary with extracted fields:
        - title: Article headline
        - author: Author name(s)
        - publish_date: Publication date (ISO string)
        - description: Article description/summary
        - source: Extraction source ('json_ld', 'meta_tags', None)
        - wire_signals: Dict with wire service detection info (if found)
    """
    result: dict[str, Any] = {
        "title": None,
        "author": None,
        "publish_date": None,
        "description": None,
        "source": None,
        "wire_signals": None,
        "canonical_url": None,
    }

    # =========================================================================
    # 1. JSON-LD structured data (FIRST - most standardized, schema.org)
    # =========================================================================
    if "application/ld+json" in html_text:
        jsonld_result = _extract_from_jsonld(html_text)
        if jsonld_result:
            for key in ("title", "author", "publish_date", "description"):
                if jsonld_result.get(key) and not result.get(key):
                    result[key] = jsonld_result[key]
            if jsonld_result.get("title") or jsonld_result.get("author"):
                result["source"] = "json_ld"
            # Check for wire signals in JSON-LD
            if jsonld_result.get("wire_signals"):
                result["wire_signals"] = jsonld_result["wire_signals"]

    # =========================================================================
    # 2. OpenGraph and standard meta tags
    # =========================================================================
    meta_result = _extract_from_meta_tags(html_text)
    for key in ("title", "author", "publish_date", "description"):
        if meta_result.get(key) and not result.get(key):
            result[key] = meta_result[key]
            if not result["source"]:
                result["source"] = "meta_tags"

    # Check for wire distributor signals
    if meta_result.get("wire_signals"):
        if result["wire_signals"]:
            # Merge wire signals
            result["wire_signals"]["detection_methods"].extend(
                meta_result["wire_signals"].get("detection_methods", [])
            )
            result["wire_signals"]["services"].extend(
                meta_result["wire_signals"].get("services", [])
            )
        else:
            result["wire_signals"] = meta_result["wire_signals"]

    # =========================================================================
    # 3. Canonical URL check for cross-domain wire detection
    # =========================================================================
    canonical_url = _extract_canonical_url(html_text)
    if canonical_url:
        result["canonical_url"] = canonical_url

        if url:
            canonical_signals = _check_canonical_for_wire(canonical_url, url)
            if canonical_signals:
                if result["wire_signals"]:
                    result["wire_signals"]["detection_methods"].extend(
                        canonical_signals.get("detection_methods", [])
                    )
                    result["wire_signals"]["services"].extend(
                        canonical_signals.get("services", [])
                    )
                else:
                    result["wire_signals"] = canonical_signals

    return result


def _extract_from_jsonld(html_text: str) -> dict[str, Any] | None:
    """Extract metadata from JSON-LD script blocks."""
    result: dict[str, Any] = {}

    for match in _JSONLD_BLOCK_RE.finditer(html_text):
        try:
            data = json.loads(match.group(1))

            primary_items: list[Any] = []
            fallback_items: list[Any] = []

            def _append_candidate(candidate: Any) -> None:
                if not isinstance(candidate, dict):
                    return
                item_type = candidate.get("@type", "")
                if isinstance(item_type, list):
                    item_type = item_type[0] if item_type else ""
                item_type_lower = item_type.lower() if isinstance(item_type, str) else ""

                if item_type_lower and item_type_lower in ARTICLE_TYPES and item_type_lower != "webpage":
                    primary_items.append(candidate)
                else:
                    fallback_items.append(candidate)

            if isinstance(data, list):
                for candidate in data:
                    _append_candidate(candidate)
            elif isinstance(data, dict):
                _append_candidate(data)
                graph_items = data.get("@graph")
                if isinstance(graph_items, list):
                    for candidate in graph_items:
                        _append_candidate(candidate)
            else:
                continue

            items: list[Any] = primary_items + fallback_items

            for item in items:
                if not isinstance(item, dict):
                    continue

                # Check @type
                item_type = item.get("@type", "")
                if isinstance(item_type, list):
                    item_type = item_type[0] if item_type else ""

                # Only process article-like types
                if item_type and item_type.lower() not in ARTICLE_TYPES:
                    continue

                # Get headline/title
                if not result.get("title"):
                    headline = item.get("headline") or item.get("name")
                    if headline and isinstance(headline, str):
                        result["title"] = headline.strip()

                # Get author
                if not result.get("author"):
                    author = item.get("author")
                    author_name = _extract_author_from_jsonld_field(author)
                    if author_name:
                        result["author"] = author_name

                # Get datePublished
                if not result.get("publish_date"):
                    pub_date = item.get("datePublished") or item.get("dateCreated")
                    if pub_date:
                        result["publish_date"] = pub_date

                # Get description
                if not result.get("description"):
                    desc = item.get("description")
                    if desc and isinstance(desc, str):
                        result["description"] = desc.strip()

                # Check for wire signals
                wire_signals = _check_jsonld_for_wire(item)
                if wire_signals:
                    result["wire_signals"] = wire_signals

                # If we have title and author, we're done
                if result.get("title") and result.get("author"):
                    return result

        except (json.JSONDecodeError, TypeError):
            continue

    return result if result else None


def _extract_author_from_jsonld_field(author: Any) -> str | None:
    """
    Extract author name from JSON-LD author field.

    Handles various formats:
    - String: "John Smith"
    - Object: {"@type": "Person", "name": "John Smith"}
    - Array: [{"@type": "Person", "name": "John Smith"}, ...]
    """
    if isinstance(author, str):
        return author.strip()
    elif isinstance(author, dict):
        name = author.get("name")
        if name and isinstance(name, str):
            return name.strip()
    elif isinstance(author, list) and author:
        # Collect all author names
        names = []
        for auth in author:
            if isinstance(auth, str):
                names.append(auth.strip())
            elif isinstance(auth, dict):
                name = auth.get("name")
                if name and isinstance(name, str):
                    names.append(name.strip())
        if names:
            return ", ".join(names)
    return None


def _check_jsonld_for_wire(item: dict) -> dict[str, Any] | None:
    """Check JSON-LD item for wire service signals."""
    signals: dict[str, Any] = {"detection_methods": [], "services": [], "evidence": []}

    # Check isBasedOn for republished content
    is_based_on = item.get("isBasedOn", "")
    if is_based_on and isinstance(is_based_on, str):
        # Known wire service domains
        wire_domains = {
            "apnews.com": "Associated Press",
            "reuters.com": "Reuters",
            "npr.org": "NPR",
            "upi.com": "UPI",
            "afp.com": "AFP",
        }
        for domain, service in wire_domains.items():
            if domain in is_based_on.lower():
                signals["detection_methods"].append("jsonld_isBasedOn")
                signals["services"].append(service)
                signals["evidence"].append(f"isBasedOn contains {domain}")
                break

    # Check mainEntityOfPage for cross-domain reference
    main_entity = item.get("mainEntityOfPage")
    if isinstance(main_entity, dict):
        entity_id = main_entity.get("@id", "")
        if entity_id:
            wire_domains = {
                "apnews.com": "Associated Press",
                "reuters.com": "Reuters",
                "npr.org": "NPR",
            }
            for domain, service in wire_domains.items():
                if domain in entity_id.lower():
                    signals["detection_methods"].append("jsonld_mainEntityOfPage")
                    signals["services"].append(service)
                    signals["evidence"].append(f"mainEntityOfPage contains {domain}")
                    break

    return signals if signals["detection_methods"] else None


def _extract_from_meta_tags(html_text: str) -> dict[str, Any]:
    """Extract metadata from OpenGraph and standard meta tags."""
    result: dict[str, Any] = {}

    # Title (og:title)
    match = _META_OG_TITLE_RE.search(html_text)
    if not match:
        match = _META_OG_TITLE_ALT_RE.search(html_text)
    if match:
        result["title"] = match.group(1).strip()

    # Author (article:author or author)
    match = _META_AUTHOR_RE.search(html_text)
    if not match:
        match = _META_AUTHOR_ALT_RE.search(html_text)
    if match:
        result["author"] = match.group(1).strip()

    # Publication time
    match = _META_PUBTIME_RE.search(html_text)
    if not match:
        match = _META_PUBTIME_ALT_RE.search(html_text)
    if match:
        result["publish_date"] = match.group(1).strip()

    # Description
    match = _META_DESCRIPTION_RE.search(html_text)
    if not match:
        match = _META_DESCRIPTION_ALT_RE.search(html_text)
    if match:
        result["description"] = match.group(1).strip()

    # Wire distributor signals
    wire_signals = _check_meta_tags_for_wire(html_text)
    if wire_signals:
        result["wire_signals"] = wire_signals

    return result


def _check_meta_tags_for_wire(html_text: str) -> dict[str, Any] | None:
    """Check meta tags for wire service distributor signals."""
    signals: dict[str, Any] = {"detection_methods": [], "services": [], "evidence": []}

    # Check distributor_category
    match = _META_DISTRIBUTOR_CATEGORY_RE.search(html_text)
    if not match:
        match = _META_DISTRIBUTOR_CATEGORY_ALT_RE.search(html_text)
    if match:
        category = match.group(1).strip().lower()
        if category in ("wires", "wire", "syndicated", "syndication"):
            signals["detection_methods"].append("og_distributor_category")
            signals["evidence"].append(f"distributor_category={category}")

            # Also get distributor name if available
            name_match = _META_DISTRIBUTOR_NAME_RE.search(html_text)
            if not name_match:
                name_match = _META_DISTRIBUTOR_NAME_ALT_RE.search(html_text)
            if name_match:
                distributor = name_match.group(1).strip()
                signals["services"].append(distributor)
                signals["evidence"].append(f"distributor_name={distributor}")

    return signals if signals["detection_methods"] else None


def _check_canonical_for_wire(
    canonical_url: str, article_url: str
) -> dict[str, Any] | None:
    """Check if canonical URL points to a different wire service domain."""
    from urllib.parse import urlparse

    try:
        canonical_parsed = urlparse(canonical_url)
        article_parsed = urlparse(article_url)

        canonical_domain = canonical_parsed.netloc.lower()
        article_domain = article_parsed.netloc.lower()

        # Remove www. prefix
        if canonical_domain.startswith("www."):
            canonical_domain = canonical_domain[4:]
        if article_domain.startswith("www."):
            article_domain = article_domain[4:]

        # If same domain, no wire signal
        if canonical_domain == article_domain:
            return None

        # Check if canonical is a known wire service
        wire_domains = {
            "apnews.com": "Associated Press",
            "reuters.com": "Reuters",
            "npr.org": "NPR",
            "upi.com": "UPI",
            "afp.com": "AFP",
            "healthday.com": "HealthDay",
            "theconversation.com": "The Conversation",
        }

        for domain, service in wire_domains.items():
            if canonical_domain == domain or canonical_domain.endswith("." + domain):
                return {
                    "detection_methods": ["canonical_cross_domain"],
                    "services": [service],
                    "evidence": [f"canonical={canonical_url[:100]}"],
                }

    except Exception:
        pass

    return None


def _extract_canonical_url(html_text: str) -> str | None:
    """Extract canonical URL from link tags in the HTML."""
    match = _CANONICAL_LINK_RE.search(html_text)
    if not match:
        match = _CANONICAL_LINK_ALT_RE.search(html_text)
    return match.group(1).strip() if match else None
