"""FooDB source handler — determine natural source/origin of a material.

Queries the FooDB public API to find food source associations for a compound,
then classifies the origin as plant, animal, synthetic, or mineral.

API: https://foodb.ca/api/v1/compounds/search?q={name}

Note: FooDB's public API availability is uncertain. If the API is unavailable
or returns no useful data, the handler returns [] and the engine waterfalls to
the next source.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_BASE_API = "https://foodb.ca/api/v1/compounds/search"
_BASE_COMPOUND = "https://foodb.ca/compounds"

# Keywords that strongly indicate a food source category.
# Each list contains substrings matched case-insensitively against food names.
_PLANT_KEYWORDS = {
    "plant", "fruit", "vegetable", "grain", "herb", "seed", "bean", "root",
    "leaf", "flower", "bark", "nut", "berry", "oil", "wheat", "corn",
    "rice", "soy", "soya", "oat", "rye", "barley", "sugar", "cane",
    "beet", "potato", "tomato", "spinach", "kale", "broccoli", "onion",
    "garlic", "ginger", "turmeric", "pepper", "basil", "mint", "thyme",
    "rosemary", "oregano", "cinnamon", "vanilla", "cocoa", "coffee",
    "tea", "algae", "seaweed", "mushroom", "fungus",
}

_ANIMAL_KEYWORDS = {
    "animal", "meat", "milk", "dairy", "egg", "fish", "seafood", "beef",
    "pork", "chicken", "turkey", "lamb", "veal", "salmon", "tuna", "shrimp",
    "honey", "beeswax", "gelatin", "collagen", "whey", "casein", "butter",
    "cheese", "cream", "lard", "tallow",
}

_MINERAL_KEYWORDS = {
    "mineral", "salt", "rock", "clay", "silica", "calcium", "magnesium",
    "iron", "zinc", "copper", "selenium",
}


def _classify_origin(food_sources: list[str]) -> str | None:
    """Classify origin based on the names of associated food sources.

    Returns 'plant', 'animal', 'mineral', or None if undetermined.
    """
    if not food_sources:
        return None

    plant_score = 0
    animal_score = 0
    mineral_score = 0

    for food in food_sources:
        food_lower = food.lower()
        for kw in _PLANT_KEYWORDS:
            if kw in food_lower:
                plant_score += 1
                break
        for kw in _ANIMAL_KEYWORDS:
            if kw in food_lower:
                animal_score += 1
                break
        for kw in _MINERAL_KEYWORDS:
            if kw in food_lower:
                mineral_score += 1
                break

    scores = {
        "plant": plant_score,
        "animal": animal_score,
        "mineral": mineral_score,
    }

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return None
    return best


def _get_json(url: str, params: dict | None = None, headers: dict | None = None) -> dict | list | None:
    """GET a URL and return parsed JSON, or None on error."""
    api_key = os.environ.get("FOODB_API_KEY")
    req_headers: dict = headers or {}
    if api_key:
        req_headers = {**req_headers, "Authorization": f"Bearer {api_key}"}

    try:
        resp = httpx.get(url, params=params, headers=req_headers, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("FooDB HTTP error for %s: %s", url, exc)
        return None
    except httpx.RequestError as exc:
        logger.warning("FooDB request error for %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.warning("FooDB unexpected error for %s: %s", url, exc)
        return None


def foodb_enrich(name: str, context: dict) -> list[dict]:
    """Query FooDB for natural source/origin of a material.

    Args:
        name: Ingredient / material name to search for.
        context: Unused by this handler (kept for interface consistency).

    Returns:
        List with a single 'source_origin' result dict, or [] when
        FooDB is unavailable or no relevant data is found.
    """
    encoded = quote(name)
    params = {"q": name}

    data = _get_json(_BASE_API, params=params)
    if data is None:
        logger.info("FooDB: API unavailable or no response for '%s'", name)
        return []

    # The API may return a dict with a "data" key or a list directly.
    compounds: list[dict] = []
    if isinstance(data, list):
        compounds = data
    elif isinstance(data, dict):
        compounds = data.get("data", []) or data.get("compounds", []) or []

    if not compounds:
        logger.info("FooDB: no compounds found for '%s'", name)
        return []

    # Use the first matching compound.
    compound = compounds[0]

    # Extract food sources from the compound record.
    # FooDB compounds link to foods via "food_sources" or similar fields.
    food_sources: list[str] = []
    compound_id: str | None = None
    compound_public_id: str | None = None

    if isinstance(compound, dict):
        compound_id = str(compound.get("id", "")) or None
        compound_public_id = compound.get("public_id") or compound.get("foodb_id")

        # Food sources may be nested under different keys depending on API version.
        raw_foods = (
            compound.get("food_sources")
            or compound.get("foods")
            or compound.get("direct_parent")
            or []
        )

        if isinstance(raw_foods, list):
            for food in raw_foods:
                if isinstance(food, dict):
                    food_name = food.get("name") or food.get("food_name") or ""
                    if food_name:
                        food_sources.append(food_name)
                elif isinstance(food, str):
                    food_sources.append(food)

        # Fallback: use kingdom / direct_parent / super_class fields for classification.
        kingdom = compound.get("kingdom", "")
        direct_parent = compound.get("direct_parent", "")
        super_class = compound.get("super_class", "")
        sub_class = compound.get("sub_class", "")

        for field_val in (kingdom, direct_parent, super_class, sub_class):
            if field_val and isinstance(field_val, str):
                food_sources.append(field_val)

    origin = _classify_origin(food_sources)

    if origin is None:
        logger.info(
            "FooDB: could not classify origin for '%s' from sources: %s",
            name,
            food_sources,
        )
        return []

    # Build source URL.
    if compound_public_id:
        source_url = f"{_BASE_COMPOUND}/{compound_public_id}"
    elif compound_id:
        source_url = f"{_BASE_COMPOUND}/{compound_id}"
    else:
        source_url = f"{_BASE_COMPOUND}?utf8=\u2713&q={encoded}"

    food_list_str = ", ".join(food_sources[:5])
    if len(food_sources) > 5:
        food_list_str += f" (and {len(food_sources) - 5} more)"
    return [
        {
            "property": "source_origin",
            "value": origin,
            "source_url": source_url,
        }
    ]
