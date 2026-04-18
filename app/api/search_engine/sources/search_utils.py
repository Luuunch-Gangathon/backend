"""Search utilities — DuckDuckGo wrapper with domain caching.

Provides three functions:
- search(query) — generic web search returning title/url/snippet
- get_supplier_domain(name) — resolves supplier name to domain, cached
- find_product_page(material, domain) — finds product page via site: search
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

_domain_cache: dict[str, str | None] = {}


def search(query: str, max_results: int = 3) -> list[dict]:
    """Search DuckDuckGo and return results as [{title, url, snippet}]."""
    try:
        with DDGS() as ddgs:
            raw = ddgs.text(query, max_results=max_results)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in raw
        ]
    except Exception:
        logger.warning("Search failed for query: %s", query, exc_info=True)
        return []


def extract_domain(url: str) -> str:
    """Extract the registrable domain from a URL.

    Strips a leading subdomain label when one is present:
    - Always strips a leading ``www.``
    - Strips the first label for hostnames with 4+ labels (handles multi-part
      TLDs such as ``co.uk`` where the registrable domain itself already has
      3 labels, so 4+ labels implies an extra subdomain prefix).
    """
    hostname = urlparse(url).hostname or ""
    parts = hostname.split(".")
    # Strip leading www. at any depth
    if parts and parts[0] == "www":
        parts = parts[1:]
    # Strip any remaining leading subdomain label when 4+ labels remain
    # (covers cases like sub.domain.example.co.uk -> domain.example.co.uk)
    elif len(parts) >= 4:
        parts = parts[1:]
    return ".".join(parts)


def get_supplier_domain(supplier_name: str) -> str | None:
    """Resolve a supplier name to its website domain. Results are cached."""
    if supplier_name in _domain_cache:
        return _domain_cache[supplier_name]

    results = search(f'"{supplier_name}" official website', max_results=3)
    if not results:
        _domain_cache[supplier_name] = None
        return None

    domain = extract_domain(results[0]["url"])
    _domain_cache[supplier_name] = domain or None
    return _domain_cache[supplier_name]


def find_product_page(material_name: str, domain: str) -> str | None:
    """Find a product page for a material on a specific supplier domain."""
    results = search(f'"{material_name}" site:{domain}', max_results=3)
    if not results:
        return None
    return results[0]["url"]
