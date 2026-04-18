"""Search utilities — DuckDuckGo wrapper with domain caching and LLM verification.

Domain discovery strategy:
1. Try direct URL construction ({name}.com, .net, .org, .io, common variations)
2. If none work, fall back to DDG search
3. Verify every candidate domain with an LLM check on the homepage

Provides:
- search(query) — generic web search returning title/url/snippet
- get_supplier_domain(name) — resolves supplier name to verified domain, cached
- find_product_page(material, domain) — finds product page via site: search
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from urllib.parse import urlparse

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

_domain_cache: dict[str, str | None] = {}

# Domains that are never supplier websites
_DOMAIN_BLOCKLIST = {
    "wikipedia.org", "en.wikipedia.org", "de.wikipedia.org",
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "youtube.com", "instagram.com", "reddit.com",
    "amazon.com", "ebay.com",
}


def search(query: str, max_results: int = 5) -> list[dict]:
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
    """Extract the registrable domain from a URL (strips www. prefix)."""
    hostname = urlparse(url).hostname or ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname


def _name_to_slug(name: str) -> str:
    """Convert a supplier name to a likely domain slug.

    'PureBulk' -> 'purebulk'
    'Jost Chemical' -> 'jostchemical'
    'Prinova USA' -> 'prinova'
    'Gold Coast Ingredients' -> 'goldcoastingredients'
    'Darling Ingredients / Rousselot' -> 'darlingredients'
    """
    # Take the part before any slash (e.g. "Darling Ingredients / Rousselot" -> "Darling Ingredients")
    name = name.split("/")[0].strip()
    # Remove common suffixes that rarely appear in domains
    for suffix in ["USA", "Inc", "LLC", "Co", "Corp", "Ltd", "GmbH"]:
        name = re.sub(rf"\b{suffix}\b\.?", "", name, flags=re.IGNORECASE)
    # Remove all non-alphanumeric, lowercase
    slug = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return slug


def _generate_candidate_domains(supplier_name: str) -> list[str]:
    """Generate likely domain candidates for a supplier name."""
    slug = _name_to_slug(supplier_name)
    if not slug:
        return []

    tlds = [".com", ".net", ".org", ".io", ".co"]
    candidates = [f"{slug}{tld}" for tld in tlds]

    # Also try with "global" suffix (common for B2B: prinovaglobal.com)
    candidates.append(f"{slug}global.com")

    return candidates


def _verify_domain_with_llm(domain: str, supplier_name: str, homepage_markdown: str) -> bool:
    """Ask LLM whether a homepage belongs to the expected supplier."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping domain verification")
        return False

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""I need to verify whether the website "{domain}" belongs to the company "{supplier_name}", which is a supplier of raw materials, ingredients, or chemicals.

Here is the homepage content (first 3000 chars):
{homepage_markdown[:3000]}

Answer with ONLY a JSON object: {{"is_match": true/false, "reason": "brief explanation"}}"""

        logger.info("Verifying domain %s for supplier '%s'", domain, supplier_name)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        logger.info("Domain verification response: %s", raw_text[:300])

        # Parse JSON from response
        json_str = raw_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        result = json.loads(json_str.strip())
        return result.get("is_match", False)

    except Exception:
        logger.warning("Domain verification failed for %s", domain, exc_info=True)
        return False


async def _check_domain_exists(domain: str) -> str | None:
    """Crawl homepage and return markdown if the domain is reachable."""
    from crawl4ai import AsyncWebCrawler

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=f"https://{domain}")
        markdown = getattr(result, "markdown", "") or ""
        if len(markdown) > 100:  # filter out empty/error pages
            return markdown
        return None
    except Exception:
        return None


def _try_direct_domains(supplier_name: str) -> str | None:
    """Try constructing the domain directly. Returns verified domain or None."""
    candidates = _generate_candidate_domains(supplier_name)
    logger.info("Trying direct domain candidates for '%s': %s", supplier_name, candidates)

    for domain in candidates:
        homepage_md = asyncio.run(_check_domain_exists(domain))
        if homepage_md is None:
            logger.debug("Domain %s not reachable", domain)
            continue

        logger.info("Domain %s is reachable, verifying with LLM...", domain)
        if _verify_domain_with_llm(domain, supplier_name, homepage_md):
            logger.info("Domain %s VERIFIED for supplier '%s'", domain, supplier_name)
            return domain
        else:
            logger.info("Domain %s rejected by LLM for supplier '%s'", domain, supplier_name)

    return None


def _try_search_domain(supplier_name: str) -> str | None:
    """Fall back to search-based domain discovery. Returns verified domain or None."""
    results = search(f'"{supplier_name}" supplier ingredients chemicals', max_results=5)
    if not results:
        return None

    # Try each result, skipping blocklisted domains
    seen_domains = set()
    for r in results:
        domain = extract_domain(r["url"])
        if not domain or domain in _DOMAIN_BLOCKLIST or domain in seen_domains:
            continue
        seen_domains.add(domain)

        logger.info("Search candidate: %s (from: %s)", domain, r["title"][:60])
        homepage_md = asyncio.run(_check_domain_exists(domain))
        if homepage_md is None:
            continue

        if _verify_domain_with_llm(domain, supplier_name, homepage_md):
            logger.info("Search domain %s VERIFIED for supplier '%s'", domain, supplier_name)
            return domain
        else:
            logger.info("Search domain %s rejected by LLM for supplier '%s'", domain, supplier_name)

    return None


def get_supplier_domain(supplier_name: str) -> str | None:
    """Resolve a supplier name to its verified website domain.

    Strategy:
    1. Try direct URL construction (fast, deterministic)
    2. Fall back to search-based discovery (broader)
    3. Every candidate is verified by crawling the homepage and asking LLM

    Results are cached — each supplier is resolved at most once.
    """
    if supplier_name in _domain_cache:
        return _domain_cache[supplier_name]

    # Step 1: direct URL construction
    domain = _try_direct_domains(supplier_name)

    # Step 2: search fallback
    if domain is None:
        logger.info("Direct URL failed for '%s', trying search...", supplier_name)
        domain = _try_search_domain(supplier_name)

    _domain_cache[supplier_name] = domain
    if domain is None:
        logger.warning("Could not resolve verified domain for supplier: %s", supplier_name)
    return domain


def find_product_page(material_name: str, domain: str) -> str | None:
    """Find a product page for a material on a specific supplier domain.

    Tries progressively broader queries:
    1. "{material}" product specifications site:{domain}
    2. "{material}" site:{domain}
    """
    queries = [
        f'"{material_name}" product specifications site:{domain}',
        f'"{material_name}" site:{domain}',
    ]

    for query in queries:
        results = search(query, max_results=3)
        if results:
            url = results[0]["url"]
            logger.info("Found product page: %s (query: %s)", url, query)
            return url

    return None
