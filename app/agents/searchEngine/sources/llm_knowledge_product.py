"""LLM knowledge handler for finished products.

Asks Claude for high-confidence facts about a finished product's compliance
properties. Trust tier: "inferred".
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import anthropic

from app.agents.searchEngine.sources.cost_tracker import track_usage

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"

PRODUCT_PROPERTIES = [
    "dietary_flags",
    "allergens",
    "certifications",
    "regulatory_status",
    "form_grade",
]

PROMPT = """You are a food/supplement industry expert. For the finished product "{product_name}" (brand: {brand}), provide any properties you know with high confidence. Only state facts you are very confident about — return null if unsure.

IMPORTANT: If you don't know a property, return null for the ENTIRE property — do NOT return an object with null sub-fields.

Return a JSON object with these properties (use null if unsure):
- dietary_flags: {{"vegan": bool, "vegetarian": bool, "halal": bool, "kosher": bool}} or null
- allergens: {{"contains": ["allergen list"], "free_from": ["allergen list"]}} or null
- certifications: [list of certifications like "organic", "non-gmo", "gmp"] or null
- regulatory_status: {{"gras": bool}} or null
- form_grade: {{"form": "powder|liquid|tablet|capsule|gummy|softgel", "grade": "food|supplement|pharma"}} or null

Return only the JSON object, no additional commentary."""


def _is_empty(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def llm_knowledge_product_enrich(name: str, context: dict) -> list[dict]:
    """Enrich a finished product using LLM knowledge."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.debug("ANTHROPIC_API_KEY not set — skipping llm_knowledge_product")
        return []

    brand = context.get("brand", "unknown")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": PROMPT.format(product_name=name, brand=brand),
            }],
        )
        track_usage(response, MODEL, "llm_knowledge_product")

        raw_text = response.content[0].text
        logger.debug("llm_knowledge_product raw response: %s", raw_text[:500])

        json_str = raw_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        extracted: dict[str, Any] = json.loads(json_str.strip())

        results = []
        for prop in PRODUCT_PROPERTIES:
            value = extracted.get(prop)
            if value is not None and not _is_empty(value):
                results.append({
                    "property": prop,
                    "value": value,
                    "source_url": None,
                })

        logger.info(
            "llm_knowledge_product: returned %d properties for '%s'",
            len(results), name,
        )
        return results

    except Exception as e:
        logger.warning(
            "llm_knowledge_product handler failed for '%s' — %s", name, e,
        )
        return []
