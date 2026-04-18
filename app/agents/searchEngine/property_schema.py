"""Strict property schemas for enrichment output.

PROPERTY_TEMPLATES defines the exact shape of every property value.
normalize_value() coerces raw handler output to match the template.

Rules:
- null for absent/unknown values
- null for lists never returned by any source
- [] for lists returned empty by a source
- Unexpected keys are dropped
- Missing keys are filled from the template default
"""

from __future__ import annotations

from typing import Any

PROPERTY_TEMPLATES: dict[str, Any] = {
    "functional_role": None,  # list[str] | None
    "source_origin": None,  # str | None
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
        "form": None,
        "grade": None,
    },
    "price": None,  # str | None
}

# Strict shape for each item in regulatory_status.recalls
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


def normalize_value(prop: str, raw: Any) -> Any:
    """Coerce a raw handler value to match the strict template shape.

    Returns the normalized value, or None if raw is None.
    """
    template = PROPERTY_TEMPLATES.get(prop)

    if raw is None:
        return None

    # Template is None → primitive or list, pass through
    if template is None:
        return raw

    # Template is a dict → enforce shape
    result = _normalize_dict(raw, template)

    # Special handling: normalize each recall item
    if prop == "regulatory_status" and isinstance(result.get("recalls"), list):
        result["recalls"] = [
            _normalize_dict(item, _RECALL_TEMPLATE)
            for item in result["recalls"]
        ]

    return result
