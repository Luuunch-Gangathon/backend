"""Strict property schemas for product enrichment output.

Same structure as material property_schema.py but with the subset of
properties relevant to finished products: dietary_flags, allergens,
certifications, regulatory_status, form_grade.
"""

from __future__ import annotations

from typing import Any

PRODUCT_PROPERTY_TEMPLATES: dict[str, Any] = {
    "dietary_flags": {
        "vegan": None,
        "vegetarian": None,
        "halal": None,
        "kosher": None,
    },
    "allergens": {
        "contains": None,
        "free_from": None,
    },
    "certifications": None,  # list[str] | None
    "regulatory_status": {
        "gras": None,
        "has_recalls": False,
        "recalls": [],
        "has_adverse_events": False,
        "adverse_events_count": 0,
    },
    "form_grade": {
        "form": None,   # "powder", "liquid", "tablet", "capsule", "gummy"
        "grade": None,   # "food", "supplement", "pharma"
    },
}

_RECALL_TEMPLATE = {
    "reason": None,
    "classification": None,
    "date": None,
}


def _normalize_dict(raw: Any, template: dict) -> dict:
    """Overlay raw dict onto template, keeping only template keys."""
    if not isinstance(raw, dict):
        return {k: v for k, v in template.items()}
    result = {}
    for key, default in template.items():
        result[key] = raw.get(key, default)
    return result


def normalize_product_value(prop: str, raw: Any) -> Any:
    """Coerce a raw handler value to match the strict product template shape."""
    template = PRODUCT_PROPERTY_TEMPLATES.get(prop)

    if raw is None:
        return None

    if template is None:
        return raw

    result = _normalize_dict(raw, template)

    if prop == "regulatory_status" and isinstance(result.get("recalls"), list):
        result["recalls"] = [
            _normalize_dict(item, _RECALL_TEMPLATE)
            for item in result["recalls"]
        ]

    return result
