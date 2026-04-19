"""Open Food Facts product handler — searches for finished products by name + brand.

Uses the .net endpoint (world.openfoodfacts.net) which is the stable API mirror.
Extracts: dietary_flags, allergens, certifications, form_grade from product data.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_OFF_SEARCH_URL = "https://world.openfoodfacts.net/cgi/search.pl"
_HEADERS = {"User-Agent": "SphereCast/1.0"}

_DIETARY_KEYWORDS = {"vegan", "vegetarian", "halal", "kosher"}
_CERTIFICATION_KEYWORDS = {
    "organic", "non-gmo", "fair-trade", "rainforest-alliance",
    "utz", "non-gmo-project", "no-gluten", "gluten-free",
}

# Map OFF categories/labels to form_grade values
_FORM_KEYWORDS = {
    "powder": "powder",
    "tablet": "tablet",
    "capsule": "capsule",
    "gummy": "gummy",
    "gummies": "gummy",
    "liquid": "liquid",
    "softgel": "softgel",
    "drink": "liquid",
    "beverage": "liquid",
}
_GRADE_KEYWORDS = {
    "supplement": "supplement",
    "vitamin": "supplement",
    "mineral": "supplement",
    "hydration": "food",
    "protein": "food",
    "food": "food",
    "pharma": "pharma",
}


def _clean_tag(tag: str) -> str:
    """Convert OFF tag like `en:gluten-free` to `Gluten Free`."""
    if ":" in tag:
        tag = tag.split(":", 1)[1]
    return tag.replace("-", " ").title()


def _extract_form_grade(product: dict) -> dict[str, str | None]:
    """Infer form and grade from categories_tags, product_name, and labels."""
    form = None
    grade = None

    searchable = " ".join([
        product.get("product_name", ""),
        " ".join(product.get("categories_tags", [])),
    ]).lower()

    for keyword, value in _FORM_KEYWORDS.items():
        if keyword in searchable:
            form = value
            break

    for keyword, value in _GRADE_KEYWORDS.items():
        if keyword in searchable:
            grade = value
            break

    return {"form": form, "grade": grade}


def _aggregate(products: list[dict]) -> dict[str, Any]:
    """Aggregate product-level data from OFF search results."""
    allergen_contains: set[str] = set()
    allergen_free: set[str] = set()
    dietary: dict[str, bool] = {}
    cert_set: set[str] = set()
    form_grade = {"form": None, "grade": None}

    for product in products:
        # allergens
        for tag in product.get("allergens_tags", []):
            bare = tag.split(":", 1)[-1].lower()
            if bare and bare != "none":
                allergen_contains.add(_clean_tag(tag))

        # traces (may contain)
        for tag in product.get("traces_tags", []):
            bare = tag.split(":", 1)[-1].lower()
            if bare and bare != "none":
                allergen_contains.add(_clean_tag(tag))

        # labels → dietary flags + certifications
        for tag in product.get("labels_tags", []):
            bare = tag.split(":", 1)[-1].lower()

            if bare in _DIETARY_KEYWORDS:
                dietary[bare] = True

            for kw in _CERTIFICATION_KEYWORDS:
                if kw in bare:
                    cert_set.add(_clean_tag(tag))
                    break

        # ingredients_analysis_tags → vegan/vegetarian confirmation
        for tag in product.get("ingredients_analysis_tags", []):
            bare = tag.split(":", 1)[-1].lower()
            if bare == "vegan":
                dietary["vegan"] = True
            elif bare == "vegetarian":
                dietary["vegetarian"] = True
            elif bare == "non-vegan":
                dietary["vegan"] = False
            elif bare == "non-vegetarian":
                dietary["vegetarian"] = False

        # free-from labels (no-gluten, no-lactose, etc.)
        for tag in product.get("labels_tags", []):
            bare = tag.split(":", 1)[-1].lower()
            if bare.startswith("no-") or bare.endswith("-free"):
                allergen_free.add(_clean_tag(tag))

        # form_grade from first product that yields something
        if form_grade["form"] is None or form_grade["grade"] is None:
            fg = _extract_form_grade(product)
            if fg["form"] and not form_grade["form"]:
                form_grade["form"] = fg["form"]
            if fg["grade"] and not form_grade["grade"]:
                form_grade["grade"] = fg["grade"]

    return {
        "allergens_contains": sorted(allergen_contains),
        "allergens_free_from": sorted(allergen_free),
        "dietary_flags": dietary,
        "certifications": sorted(cert_set),
        "form_grade": form_grade,
    }


def open_food_facts_product_enrich(name: str, context: dict) -> list[dict]:
    """Enrich a finished product with data from Open Food Facts.

    Args:
        name: Product name (e.g. "Centrum Silver Women 50+").
        context: May contain "brand" for more precise search.

    Returns:
        List of property dicts for dietary_flags, allergens, certifications, form_grade.
    """
    search_term = name
    brand = context.get("brand")
    if brand:
        search_term = f"{brand} {name}"

    params = {
        "search_terms": search_term,
        "search_simple": "1",
        "json": "1",
        "page_size": "5",
    }

    try:
        response = httpx.get(
            _OFF_SEARCH_URL, params=params, headers=_HEADERS, timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.warning(
            "Open Food Facts product search failed for '%s' — %s", name, e,
        )
        return []

    products: list[dict] = data.get("products", [])
    if not products:
        logger.info("Open Food Facts: no products found for '%s'", name)
        return []

    aggregated = _aggregate(products)

    source_url = (
        f"https://world.openfoodfacts.net/cgi/search.pl"
        f"?search_terms={search_term}&search_simple=1&json=1&page_size=5"
    )

    results: list[dict] = []

    # allergens
    contains = aggregated["allergens_contains"]
    free_from = aggregated["allergens_free_from"]
    if contains or free_from:
        results.append({
            "property": "allergens",
            "value": {"contains": contains, "free_from": free_from},
            "source_url": source_url,
        })

    # dietary_flags
    dietary = aggregated["dietary_flags"]
    if dietary:
        results.append({
            "property": "dietary_flags",
            "value": dietary,
            "source_url": source_url,
        })

    # certifications
    certs = aggregated["certifications"]
    if certs:
        results.append({
            "property": "certifications",
            "value": certs,
            "source_url": source_url,
        })

    # form_grade
    fg = aggregated["form_grade"]
    if fg["form"] or fg["grade"]:
        results.append({
            "property": "form_grade",
            "value": fg,
            "source_url": source_url,
        })

    return results
