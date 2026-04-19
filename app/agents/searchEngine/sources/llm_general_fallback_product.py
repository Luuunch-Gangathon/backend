"""LLM general fallback handler for finished products.

Speculative completion for product properties that no other source could fill.
Trust tier: "speculative".
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import anthropic

from app.agents.searchEngine.sources.cost_tracker import track_usage
from app.agents.searchEngine.product_property_schema import normalize_product_value

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"

PROMPT = """You are a food/supplement industry expert. For the finished product "{product_name}" (brand: {brand}), I need best-effort values for the properties listed below. Previous lookups returned nothing — fill in what you reasonably can.

Rules:
1. If you can make a reasonable inference (even at low confidence), provide a value.
2. If the property is genuinely not applicable, return null with "not_applicable": true.
3. Do NOT confuse "I don't know" with "not applicable".

Return a JSON object where each key is a property name. Each value is either:
- null (truly unknown)
- An object: {{"value": <the property value>, "not_applicable": false}}
- An object: {{"value": null, "not_applicable": true, "reason": "brief explanation"}}

Properties to fill:
{properties_list}

Property schemas:
- dietary_flags: {{"vegan": bool, "vegetarian": bool, "halal": bool, "kosher": bool}}
- allergens: {{"contains": ["list"], "free_from": ["list"]}}
- certifications: [list of certification names]
- regulatory_status: {{"gras": bool}}
- form_grade: {{"form": "powder|liquid|tablet|capsule|gummy|softgel", "grade": "food|supplement|pharma"}}

Return only the JSON object, no commentary."""


def _is_empty(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def llm_general_fallback_product_enrich(name: str, context: dict) -> list[dict]:
    """Speculative enrichment for product properties still missing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — skipping llm_general_fallback_product")
        return []

    from app.agents.searchEngine.product_config import PRODUCT_PROPERTIES

    missing = context.get("missing_properties", PRODUCT_PROPERTIES)
    if not missing:
        return []

    brand = context.get("brand", "unknown")
    properties_list = "\n".join(f"- {p}" for p in missing)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": PROMPT.format(
                    product_name=name,
                    brand=brand,
                    properties_list=properties_list,
                ),
            }],
        )
        track_usage(response, MODEL, "llm_general_fallback_product")

        raw_text = response.content[0].text
        logger.debug("llm_general_fallback_product raw: %s", raw_text[:500])

        json_str = raw_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        extracted: dict[str, Any] = json.loads(json_str.strip())

        results = []
        for prop in missing:
            entry = extracted.get(prop)
            if entry is None:
                continue
            if not isinstance(entry, dict):
                normalized = normalize_product_value(prop, entry)
                if normalized is not None and not _is_empty(normalized):
                    results.append({
                        "property": prop,
                        "value": normalized,
                        "source_url": None,
                    })
                continue

            if entry.get("not_applicable"):
                logger.info(
                    "llm_general_fallback_product: '%s' N/A for '%s' — %s",
                    prop, name, entry.get("reason", ""),
                )
                continue

            value = entry.get("value")
            if value is not None and not _is_empty(value):
                results.append({
                    "property": prop,
                    "value": value,
                    "source_url": None,
                })

        logger.info(
            "llm_general_fallback_product: returned %d properties for '%s'",
            len(results), name,
        )
        return results

    except Exception as e:
        logger.warning(
            "llm_general_fallback_product handler failed for '%s' — %s", name, e,
        )
        return []
