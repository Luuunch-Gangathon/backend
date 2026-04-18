"""Web search handler — fallback enrichment via DuckDuckGo + LLM extraction.

This is a trust-tier "inferred" handler. Cost-conscious by design:
- One DDG query, top result only
- One page crawl
- Max 5000 chars sent to LLM
- Uses Haiku (cheapest model)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import anthropic

from app.agents.searchEngine.sources.cost_tracker import track_usage
from app.agents.searchEngine.sources.search_utils import extract_domain, search
from app.agents.searchEngine.sources.supplier_website import _crawl_page

logger = logging.getLogger(__name__)

_SKIP_DOMAINS = {
    "wikipedia.org",
    "linkedin.com",
    "facebook.com",
    "youtube.com",
    "reddit.com",
    "amazon.com",
}

_PROPERTY_FIELDS = [
    "chemical_identity",
    "functional_role",
    "source_origin",
    "dietary_flags",
    "allergens",
    "certifications",
    "regulatory_status",
    "form_grade",
    "price",
]

EXTRACTION_PROMPT = """\
Given this web page about "{material_name}", extract any of these properties if explicitly stated:
- chemical_identity (CAS number, formula, synonyms)
- functional_role (what it does: binder, filler, lubricant, etc.)
- source_origin (plant, animal, synthetic, mineral)
- dietary_flags (vegan, vegetarian, halal, kosher — as booleans)
- allergens (contains and free_from lists)
- certifications (Non-GMO, Organic, GMP, etc.)
- regulatory_status (GRAS, EU-approved, recalls)
- form_grade (powder, liquid, capsule-grade, etc.)
- price (with unit)

Return a JSON object with only the properties you found. Use null for properties not mentioned.
Only extract what is explicitly stated — do not infer.

Page content:
{page_content}"""


def _extract_properties_from_page(markdown: str, material_name: str) -> dict[str, Any] | None:
    """Call OpenAI to extract properties from page content."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping web search extraction")
        return None

    prompt = EXTRACTION_PROMPT.format(
        material_name=material_name,
        page_content=markdown[:5000],
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        model = "claude-haiku-4-5-20251001"

        logger.info(
            "Web search extraction: sending %d chars to %s for '%s'",
            len(prompt),
            model,
            material_name,
        )

        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        track_usage(response, model, "web_search_extraction")

        raw_text = response.content[0].text
        logger.info("Web search LLM response: %s", raw_text[:500])

        # Strip markdown code fences if present
        json_str = raw_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        extracted = json.loads(json_str.strip())
        return extracted if isinstance(extracted, dict) else None

    except Exception as e:
        logger.warning("Web search LLM extraction failed for material: %s — %s", material_name, e)
        return None


def web_search_enrich(name: str, context: dict) -> list[dict]:
    """Enrich material properties via a single DuckDuckGo search + LLM extraction.

    Flow:
    1. Search DDG for "{name}" specifications properties vegan allergens certifications
    2. Take the first non-blocklisted result URL
    3. Crawl the page with crawl4ai
    4. Send first 5000 chars to Haiku for extraction
    5. Return one result dict per non-null property found
    """
    query = f'"{name}" specifications properties vegan allergens certifications'
    logger.info("Web search query: %s", query)

    results = search(query, max_results=5)
    if not results:
        logger.info("No web search results for '%s'", name)
        return []

    # Find first non-blocklisted result
    target_url = None
    for result in results:
        url = result.get("url", "")
        domain = extract_domain(url)
        if domain and domain not in _SKIP_DOMAINS:
            target_url = url
            logger.info("Web search selected URL: %s (domain: %s)", url, domain)
            break

    if not target_url:
        logger.info("All web search results were blocklisted for '%s'", name)
        return []

    # Crawl the page
    try:
        markdown = asyncio.run(_crawl_page(target_url))
    except Exception as e:
        logger.warning("Web search crawl failed for %s — %s", target_url, e)
        return []

    if not markdown:
        logger.info("Crawl returned no content for %s", target_url)
        return []

    # Extract properties with LLM
    extracted = _extract_properties_from_page(markdown, name)
    if not extracted:
        logger.info("No properties extracted from %s", target_url)
        return []

    # Convert to handler result format — only include non-null known properties
    raw_excerpt = markdown[:200]
    handler_results = []
    for field in _PROPERTY_FIELDS:
        value = extracted.get(field)
        if value is not None:
            handler_results.append(
                {
                    "property": field,
                    "value": value,
                    "source_url": target_url,
                    "raw_excerpt": raw_excerpt,
                }
            )

    logger.info(
        "Web search extracted %d properties for '%s' from %s",
        len(handler_results),
        name,
        target_url,
    )
    return handler_results
