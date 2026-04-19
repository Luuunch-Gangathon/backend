"""Merged LLM enrichment handler — single call with reasoning and self-assessed confidence.

Replaces llm_knowledge + llm_general_fallback with one call that:
1. Grounds answers in reasoning (chain-of-thought)
2. References known standards (FALCPA allergens, dietary classification by origin)
3. Self-assesses confidence per property (high/medium/low)
4. Uses constrained vocabularies for values

Trust tier mapping:
  confidence "high"   -> "inferred"
  confidence "medium" -> "speculative"
  confidence "low"    -> "speculative"
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

PROMPT = """You are a food science and regulatory expert. For the raw material "{material_name}", provide properties based on established facts.

INSTRUCTIONS:
1. For each property, first reason about what you know (cite standards, origin, chemical nature), then give the value.
2. Base allergen classification on FDA FALCPA major allergens: milk, eggs, fish, shellfish, tree nuts, peanuts, wheat, soybeans, sesame.
3. Base dietary flags on ingredient origin: animal-derived = not vegan; animal byproduct = not vegetarian; porcine = not halal; check kosher status based on source.
4. Base regulatory status on whether the ingredient is on the FDA GRAS list or is a commonly recognized food additive.
5. Assess your confidence for each property: "high" (well-established fact), "medium" (reasonable inference), "low" (uncertain/guessing).
6. If you truly don't know, return null for the entire property.

Return a JSON object with these properties. Each property must be an object with "value", "confidence", and "reasoning" fields:

{{
  "functional_role": {{
    "value": ["role1", "role2"] or null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "brief explanation"
  }},
  "source_origin": {{
    "value": "plant" | "animal" | "synthetic" | "mineral" or null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "brief explanation"
  }},
  "dietary_flags": {{
    "value": {{"vegan": bool, "vegetarian": bool, "halal": bool, "kosher": bool}} or null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "brief explanation of why each flag is set"
  }},
  "allergens": {{
    "value": {{"contains": ["from FALCPA list only"], "free_from": ["from FALCPA list only"]}} or null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "brief explanation"
  }},
  "certifications": {{
    "value": ["cert1", "cert2"] or null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "brief explanation"
  }},
  "regulatory_status": {{
    "value": {{"gras": bool}} or null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "brief explanation citing FDA status"
  }},
  "form_grade": {{
    "value": {{"form": "powder" | "liquid" | "tablet" | "capsule" | "softgel" | "gummy" | null, "grade": "food" | "supplement" | null}} or null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "brief explanation"
  }}
}}

Return only the JSON object, no additional commentary."""

PROPERTIES = [
    "functional_role",
    "source_origin",
    "dietary_flags",
    "allergens",
    "certifications",
    "regulatory_status",
    "form_grade",
]

CONFIDENCE_MAP = {
    "high": "inferred",
    "medium": "speculative",
    "low": "speculative",
}


def _is_empty(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def llm_enrichment_enrich(name: str, context: dict) -> list[dict]:
    """Enrich a material with a single LLM call that includes reasoning and confidence."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.debug("ANTHROPIC_API_KEY not set — skipping llm_enrichment")
        return []

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": PROMPT.format(material_name=name),
            }],
        )
        track_usage(response, MODEL, "llm_enrichment")

        raw_text = response.content[0].text
        logger.debug("llm_enrichment raw response: %s", raw_text[:500])

        json_str = raw_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        extracted: dict[str, Any] = json.loads(json_str.strip())

        results = []
        for prop in PROPERTIES:
            entry = extracted.get(prop)
            if entry is None:
                continue
            if not isinstance(entry, dict):
                continue

            value = entry.get("value")
            if value is None or _is_empty(value):
                continue

            confidence_raw = entry.get("confidence", "low")
            confidence = CONFIDENCE_MAP.get(confidence_raw, "speculative")
            reasoning = entry.get("reasoning", "")

            results.append({
                "property": prop,
                "value": value,
                "confidence": confidence,
                "reasoning": reasoning,
            })

        logger.info(
            "llm_enrichment: returned %d properties for '%s'",
            len(results), name,
        )
        return results

    except Exception as e:
        logger.warning(
            "llm_enrichment handler failed for '%s' — %s", name, e,
        )
        return []
