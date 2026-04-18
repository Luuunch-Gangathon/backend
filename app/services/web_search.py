"""Web search enrichment via OpenAI Responses API."""
from __future__ import annotations

import json
import logging
import os
import re

from openai import AsyncOpenAI

from app.prompts.loader import render
from app.schemas.tool_results import EnrichedMaterial

logger = logging.getLogger(__name__)

_openai = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def discover_alternatives(
    query: str,
    limit: int = 5,
    product_profile: dict | None = None,
) -> list[dict]:
    """Use OpenAI Responses API with hosted web_search_preview to find
    candidate alternatives to `query`.

    When `product_profile` is provided (dietary flags, allergens, required
    certifications), the LLM filters/ranks alternatives to satisfy those
    constraints.

    Returns a list of enriched dicts in the exact shape store_embedding expects.
    """
    system_prompt = render(
        "system/web_search_enrich",
        query=query,
        limit=limit,
        product_profile=product_profile,
    )

    user_content = f"Find {limit} ingredient alternatives to: {query}"
    if product_profile:
        user_content += (
            "\n\nThe replacement must satisfy the product's dietary, allergen,"
            " and certification requirements described in the system prompt."
        )

    response = await _openai.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search_preview"}],
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    output_text = _extract_text(response)
    if not output_text:
        logger.warning("web_search: empty response for query %r", query)
        return []

    raw_alternatives = _parse_alternatives(output_text)

    results: list[dict] = []
    for item in raw_alternatives[:limit]:
        try:
            material = EnrichedMaterial(**item)
            if material.normalized_name:
                results.append(material.model_dump())
        except Exception as exc:
            logger.warning("web_search: skipping invalid item: %s", exc)

    logger.info("web_search: discovered %d alternatives for %r", len(results), query)
    return results


def _extract_text(response) -> str:
    """Pull plain text from a Responses API response object."""
    # Prefer the convenience property if present (SDK >= 1.68)
    if hasattr(response, "output_text"):
        return response.output_text or ""

    text = ""
    for item in getattr(response, "output", []):
        if getattr(item, "type", None) == "message":
            for block in getattr(item, "content", []):
                if hasattr(block, "text"):
                    text += block.text
    return text


def _parse_alternatives(text: str) -> list[dict]:
    """Extract the alternatives list from the LLM response text."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip()

    json_match = re.search(r'\{[\s\S]*"alternatives"[\s\S]*\}', text)
    if not json_match:
        logger.warning("web_search: no JSON with 'alternatives' key found")
        return []

    try:
        data = json.loads(json_match.group(0))
        return data.get("alternatives", [])
    except json.JSONDecodeError as exc:
        logger.warning("web_search: JSON parse error: %s", exc)
        return []
