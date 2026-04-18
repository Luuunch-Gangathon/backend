"""Supplier website handler — crawl supplier product pages and extract properties.

Uses crawl4ai for page crawling and LLM-powered structured extraction.
Uses DuckDuckGo for URL discovery.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

EXTRACTION_INSTRUCTION = """
Extract material properties from this product page for the material "{material_name}".

Rules:
- Set is_correct_material to false if this page is NOT about "{material_name}"
- Only extract what is explicitly stated on the page — do not infer or guess
- Leave fields as null if the information is not present
- For allergens, list what the page explicitly says under "contains" and "free_from"
- For dietary_flags, look for vegan, vegetarian, halal, kosher mentions
- For certifications, look for Non-GMO, Organic, GMP, BSE/TSE Free, etc.
- For price, include the unit (e.g. "$25/kg")
"""


class MaterialProperties(BaseModel):
    """Schema for LLM extraction from supplier product pages."""

    is_correct_material: bool
    chemical_identity: Optional[dict[str, Any]] = None
    functional_role: Optional[list[str]] = None
    source_origin: Optional[str] = None
    dietary_flags: Optional[dict[str, Any]] = None
    allergens: Optional[dict[str, Any]] = None
    certifications: Optional[list[str]] = None
    regulatory_status: Optional[dict[str, Any]] = None
    form_grade: Optional[dict[str, Any]] = None
    price: Optional[str] = None


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


def convert_to_handler_results(
    props: MaterialProperties,
    source_url: str,
    raw_markdown: str,
) -> list[dict]:
    """Convert MaterialProperties to the handler result format.

    Returns empty list if is_correct_material is False.
    Only includes properties that have non-None values.
    """
    if not props.is_correct_material:
        return []

    results = []
    for field_name in _PROPERTY_FIELDS:
        value = getattr(props, field_name)
        if value is not None:
            results.append(
                {
                    "property": field_name,
                    "value": value,
                    "source_url": source_url,
                    "raw_excerpt": raw_markdown[:500] if raw_markdown else None,
                }
            )
    return results


import anthropic
from crawl4ai import AsyncWebCrawler


async def _crawl_page(url: str) -> str | None:
    """Crawl a URL and return clean markdown. Returns None on failure."""
    try:
        logger.info("Crawling URL: %s", url)
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
        markdown = getattr(result, "markdown", "") or ""
        logger.info("Page crawled, markdown length: %d chars", len(markdown))
        return markdown if markdown else None
    except Exception:
        logger.warning("Crawl failed for %s", url, exc_info=True)
        return None


def _extract_properties(markdown: str, material_name: str) -> MaterialProperties | None:
    """Call Anthropic to extract structured properties from page markdown."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping extraction")
        return None

    schema_json = json.dumps(MaterialProperties.model_json_schema(), indent=2)
    prompt = f"""{EXTRACTION_INSTRUCTION.format(material_name=material_name)}

Return a JSON object matching this schema:
{schema_json}

Page content:
{markdown[:15000]}"""

    try:
        logger.info("Sending to Anthropic for extraction (material: %s, prompt length: %d)", material_name, len(prompt))
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        logger.info("Anthropic response: %s", raw_text[:2000])

        # Extract JSON from response (may be wrapped in markdown code blocks)
        json_str = raw_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        extracted = json.loads(json_str.strip())
        props = MaterialProperties(**extracted)

        logger.info("Extraction result — correct_material: %s, properties found: %d",
                     props.is_correct_material,
                     sum(1 for f in _PROPERTY_FIELDS if getattr(props, f) is not None))
        return props

    except Exception:
        logger.warning("LLM extraction failed for material: %s", material_name, exc_info=True)
        return None


async def _crawl_and_extract(
    url: str, material_name: str
) -> tuple[MaterialProperties, str] | None:
    """Crawl a URL and extract material properties using LLM.

    Returns (MaterialProperties, raw_markdown) or None on failure.
    """
    markdown = await _crawl_page(url)
    if not markdown:
        return None

    props = _extract_properties(markdown, material_name)
    if not props:
        return None

    return props, markdown


from app.api.search_engine.sources.search_utils import (
    get_supplier_domain,
    find_product_page,
)
from app.api.search_engine.sources.db_utils import get_supplier_names


def _run_crawl_and_extract(
    url: str, material_name: str
) -> tuple[MaterialProperties, str] | None:
    """Sync wrapper for _crawl_and_extract."""
    return asyncio.run(_crawl_and_extract(url, material_name))


def supplier_website_enrich(name: str, context: dict) -> list[dict]:
    """Enrich material properties by crawling supplier product pages.

    For each supplier associated with this material:
    1. Resolve the supplier's website domain
    2. Search for the material's product page on that domain
    3. Crawl the page and extract properties with LLM
    4. Return on first successful extraction
    """
    supplier_ids = context.get("supplier_ids", [])
    if not supplier_ids:
        return []

    supplier_names = get_supplier_names(supplier_ids)

    for supplier_name in supplier_names:
        domain = get_supplier_domain(supplier_name)
        if domain is None:
            logger.info("Could not resolve domain for supplier: %s", supplier_name)
            continue

        product_url = find_product_page(name, domain)
        if product_url is None:
            logger.info("No product page found for '%s' on %s", name, domain)
            continue

        result = _run_crawl_and_extract(product_url, name)
        if result is None:
            continue

        props, raw_markdown = result
        handler_results = convert_to_handler_results(props, product_url, raw_markdown)
        if handler_results:
            return handler_results

    return []
