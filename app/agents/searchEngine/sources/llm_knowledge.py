"""LLM knowledge handler — last-resort enrichment from LLM training data.

No external sources are queried. The LLM answers from its own knowledge.
Trust tier: "inferred" — cheapest and least authoritative source.
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


def _is_empty(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False

PROPERTIES = [
    "functional_role",
    "source_origin",
    "dietary_flags",
    "allergens",
    "certifications",
    "regulatory_status",
    "form_grade",
]

PROMPT = """You are a materials science expert. For the raw material "{material_name}", provide any properties you know with high confidence. Only state facts you are very confident about — it is better to return null than to guess.

IMPORTANT: If you don't know a property, return null for the ENTIRE property — do NOT return an object with null sub-fields like {{"contains": null, "free_from": null}}. That should just be null.

Return a JSON object with these properties (use null if unsure):
- functional_role: [list of roles] or null
- source_origin: "plant" | "animal" | "synthetic" | "mineral" or null
- dietary_flags: {{"vegan": bool, "vegetarian": bool, "halal": bool, "kosher": bool}} or null
- allergens: {{"contains": ["list of allergens"], "free_from": ["list"]}} or null
- certifications: [list] or null
- regulatory_status: {{"gras": bool}} or null
- form_grade: {{"form": "...", "grade": "..."}} or null

Return only the JSON object, no additional commentary."""


def llm_knowledge_enrich(name: str, context: dict) -> list[dict]:
    """Enrich a material using LLM knowledge — no external sources.

    Returns a list of property dicts. source_url is always None.
    Falls back to empty list on any error.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — skipping llm_knowledge handler")
        return []

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": PROMPT.format(material_name=name)}],
        )
        track_usage(response, MODEL, "llm_knowledge")

        raw_text = response.content[0].text
        logger.debug("LLM knowledge raw response: %s", raw_text[:500])

        # Strip optional markdown code fences
        json_str = raw_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        extracted: dict[str, Any] = json.loads(json_str.strip())

        results = []
        for prop in PROPERTIES:
            value = extracted.get(prop)
            if value is not None and not _is_empty(value):
                results.append(
                    {
                        "property": prop,
                        "value": value,
                        "source_url": None,
                        "raw_excerpt": "LLM knowledge (no external source)",
                    }
                )

        logger.info(
            "llm_knowledge: returned %d properties for '%s'", len(results), name
        )
        return results

    except Exception as e:
        logger.warning(
            "llm_knowledge handler failed for '%s' — %s", name, e
        )
        return []
