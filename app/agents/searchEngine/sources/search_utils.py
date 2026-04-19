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
# Known supplier domains — skip slow DDG+LLM discovery for these.
KNOWN_SUPPLIER_DOMAINS: dict[str, str] = {
    "purebulk": "purebulk.com",
    "bulksupplements": "bulksupplements.com",
}


def get_known_domain(supplier_name: str) -> str | None:
    """Check if supplier has a known domain. Case-insensitive."""
    return KNOWN_SUPPLIER_DOMAINS.get(supplier_name.lower().strip())


def shopify_product_search(domain: str, query: str, limit: int = 3) -> list[dict]:
    """Search a Shopify store's suggest API. Returns [{title, handle, url}].

    Free, no rate limits, returns exact product handles.
    """
    import httpx

    search_url = (
        f"https://{domain}/search/suggest.json"
        f"?q={query.replace(' ', '+')}"
        f"&resources[type]=product&resources[limit]={limit}"
    )
    try:
        resp = httpx.get(search_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        products = data.get("resources", {}).get("results", {}).get("products", [])
        return [
            {
                "title": p.get("title", ""),
                "handle": p.get("handle", ""),
                "url": f"https://{domain}/products/{p.get('handle', '')}",
            }
            for p in products
        ]
    except Exception as e:
        logger.warning("Shopify search failed on %s for '%s' — %s", domain, query, e)
        return []


def rank_product_urls(urls: list[str]) -> str | None:
    """Pick the best product URL from a list of candidates.

    Priority:
    1. /products/ URL not ending in -bulk → best
    2. /blog/ URL → fallback (may have dietary info)
    3. Anything else or -bulk → skip
    """
    product_urls = []
    blog_urls = []

    for url in urls:
        path = url.lower().split("?")[0]
        if "-bulk" in path.split("/")[-1]:
            continue
        if "/products/" in path:
            product_urls.append(url)
        elif "/blog/" in path:
            blog_urls.append(url)

    if product_urls:
        return product_urls[0]
    if blog_urls:
        return blog_urls[0]
    return None


def _title_matches_material(title: str, query_words: list[str]) -> bool:
    """Check if a Shopify product title is a plausible match for the material.

    Requires at least half of the query words (min 1) to appear in the title.
    This prevents "sodium" matching "BHB Sodium" when searching "sodium ascorbate".
    """
    title_words = set(re.findall(r'[a-z0-9]+', title.lower()))
    matches = sum(1 for w in query_words if w in title_words)
    # Require ALL words for short queries (1-2 words), majority for longer
    if len(query_words) <= 2:
        return matches == len(query_words)
    return matches >= (len(query_words) + 1) // 2  # ceil(n/2)


def find_product_page_known_domain(material_name: str, domain: str) -> str | None:
    """Find a product page on a known Shopify supplier domain.

    Strategy:
    1. Shopify suggest API with full material name
    2. If no results, try dropping the last word progressively (but never single word)
    3. Verify result title matches the material before accepting
    4. Pick best URL: /products/ (not -bulk) preferred
    """
    query = material_name.replace("-", " ")
    words = query.split()

    # Try full query, then progressively shorter (but min 2 words)
    queries_to_try = [" ".join(words[:i]) for i in range(len(words), 1, -1)]
    # Also try full query (even if single word)
    if len(words) == 1:
        queries_to_try = [query]

    for q in queries_to_try:
        results = shopify_product_search(domain, q)
        if not results:
            if q != query:
                logger.info("No Shopify results for '%s', trying shorter", q)
            continue

        # Filter results: title must plausibly match the material
        matched = [r for r in results if _title_matches_material(r["title"], words)]
        if not matched:
            logger.info("Shopify results for '%s' didn't match material '%s' (titles: %s)",
                        q, material_name,
                        ", ".join(r["title"] for r in results[:3]))
            continue

        urls = [r["url"] for r in matched]
        best = rank_product_urls(urls)
        if best:
            logger.info("Found product page: %s for '%s'", best, material_name)
            return best

    logger.info("No product found for '%s' on %s", material_name, domain)
    return None


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
    except Exception as e:
        logger.warning("Search failed for query: %s — %s", query, e)
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
        model = "claude-haiku-4-5-20251001"
        response = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        from app.agents.searchEngine.sources.cost_tracker import track_usage
        track_usage(response, model, "domain_verification")

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

    except Exception as e:
        logger.warning("Domain verification failed for %s — %s", domain, e)
        return False


async def _check_domain_exists(domain: str) -> str | None:
    """Crawl homepage and return markdown if the domain is reachable.

    Does a quick HEAD request first to avoid launching crawl4ai on dead URLs.
    """
    import httpx

    url = f"https://{domain}"
    try:
        async with httpx.AsyncClient(timeout=2, follow_redirects=True) as client:
            resp = await client.head(url)
            if resp.status_code >= 400:
                return None
    except Exception:
        return None

    from crawl4ai import AsyncWebCrawler

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
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
