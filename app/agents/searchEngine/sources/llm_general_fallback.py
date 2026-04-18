"""LLM general fallback handler — last-resort speculative enrichment.

Called only when all previous sources (including constrained llm_knowledge)
produced no value for a property. Uses a broader prompt that:
  - Makes low-confidence inferences rather than refusing to answer.
  - Explicitly marks properties as N/A when the concept doesn't apply to
    the material category (e.g. dietary_flags for a pure inorganic mineral).

N/A properties are returned as null — they stay unknown, not fabricated.
Trust tier: "speculative" — lowest authority, treat as weak prior only.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import anthropic

from app.agents.searchEngine.sources.cost_tracker import track_usage
from app.agents.searchEngine.property_schema import normalize_value

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"

PROMPT = """You are a materials science expert. For the raw material "{material_name}", I need best-effort values for the properties listed below. Previous authoritative lookups returned nothing — fill in what you reasonably can.

Rules:
1. If you can make a reasonable inference (even at low confidence), provide a value.
2. If the property is **genuinely not applicable** to this material's category (e.g. asking for "vegan" classification of a pure inorganic mineral like calcium carbonate where the concept of veganism is a category mismatch), return null AND set "not_applicable" to true with a brief reason.
3. Do NOT confuse "I don't know" with "not applicable". Uncertainty → give your best guess. True category mismatch → null + not_applicable.
4. Return null for the entire property object if you have no basis at all.

Return a JSON object where each key is a property name. Each value is either:
- null (truly unknown and not applicable)
- An object: {{"value": <the property value>, "not_applicable": false}}
- An object: {{"value": null, "not_applicable": true, "reason": "brief explanation"}}

Properties to fill:
{properties_list}

Property schemas:
- functional_role: [list of role strings, e.g. ["emulsifier", "stabilizer"]]
- source_origin: "plant" | "animal" | "synthetic" | "mineral"
- dietary_flags: {{"vegan": bool, "vegetarian": bool, "halal": bool, "kosher": bool}}
- allergens: {{"contains": ["list"], "free_from": ["list"]}}
- certifications: [list of certification names]
- regulatory_status: {{"gras": bool}}
- form_grade: {{"form": "powder|liquid|...", "grade": "food|pharma|..."}}

Return only the JSON object, no commentary."""


def _is_empty(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def llm_general_fallback_enrich(name: str, context: dict) -> list[dict]:
    """Speculative enrichment for properties still null after all other sources.

    The caller (engine) passes which properties are still missing via
    context["missing_properties"]. Falls back to all PROPERTIES if not set.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.debug("ANTHROPIC_API_KEY not set — skipping llm_general_fallback")
        return []

    from app.agents.searchEngine.config import PROPERTIES as ALL_PROPERTIES

    missing = context.get("missing_properties", ALL_PROPERTIES)
    if not missing:
        return []

    properties_list = "\n".join(f"- {p}" for p in missing)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        material_name=name,
                        properties_list=properties_list,
                    ),
                }
            ],
        )
        track_usage(response, MODEL, "llm_general_fallback")

        raw_text = response.content[0].text
        logger.debug("llm_general_fallback raw response: %s", raw_text[:500])

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
                # LLM returned a raw value — normalize against schema before accepting
                normalized = normalize_value(prop, entry)
                if normalized is not None and not _is_empty(normalized):
                    results.append({
                        "property": prop,
                        "value": normalized,
                        "source_url": None,
                        "raw_excerpt": "LLM general fallback (speculative)",
                    })
                continue

            if entry.get("not_applicable"):
                reason = entry.get("reason", "not applicable to this material")
                logger.info(
                    "llm_general_fallback: '%s' N/A for '%s' — %s", prop, name, reason
                )
                # Leave as null — do not emit a result so the engine keeps it unknown
                continue

            value = entry.get("value")
            if value is not None and not _is_empty(value):
                results.append({
                    "property": prop,
                    "value": value,
                    "source_url": None,
                    "raw_excerpt": "LLM general fallback (speculative)",
                })

        logger.info(
            "llm_general_fallback: returned %d properties for '%s'", len(results), name
        )
        return results

    except Exception as e:
        logger.warning(
            "llm_general_fallback handler failed for '%s' — %s", name, e
        )
        return []
