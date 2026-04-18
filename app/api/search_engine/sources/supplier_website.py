"""Supplier website handler — crawl supplier product pages and extract properties.

Uses crawl4ai for page crawling and LLM-powered structured extraction.
Uses DuckDuckGo for URL discovery.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

EXTRACTION_INSTRUCTION = """
Extract material properties from this product page for the material "{material_name}".

Rules:
- Set is_correct_material to false if this page is NOT about "{material_name}"
- Only extract what is explicitly stated on the page — do not infer or guess
- Leave fields as null if the information is not present
- For allergens, list what the page explicitly says under "contains" and "free_from"
- For dietary_flags, look for vegan, vegetarian, halal, kosher mentions
- For certifications, look for Non-GMO, Organic, GMP, BSE/TSE Free, etc.
- For price, include the unit (e.g. "$25/kg")
"""


class MaterialProperties(BaseModel):
    """Schema for LLM extraction from supplier product pages."""

    is_correct_material: bool
    chemical_identity: Optional[dict[str, Any]] = None
    functional_role: Optional[list[str]] = None
    source_origin: Optional[str] = None
    dietary_flags: Optional[dict[str, Any]] = None
    allergens: Optional[dict[str, Any]] = None
    certifications: Optional[list[str]] = None
    regulatory_status: Optional[dict[str, Any]] = None
    form_grade: Optional[dict[str, Any]] = None
    price: Optional[str] = None


_PROPERTY_FIELDS = [
    "chemical_identity",
    "functional_role",
    "source_origin",
    "dietary_flags",
    "allergens",
    "certifications",
    "regulatory_status",
    "form_grade",
    "price",
]


def convert_to_handler_results(
    props: MaterialProperties,
    source_url: str,
    raw_markdown: str,
) -> list[dict]:
    """Convert MaterialProperties to the handler result format.

    Returns empty list if is_correct_material is False.
    Only includes properties that have non-None values.
    """
    if not props.is_correct_material:
        return []

    results = []
    for field_name in _PROPERTY_FIELDS:
        value = getattr(props, field_name)
        if value is not None:
            results.append(
                {
                    "property": field_name,
                    "value": value,
                    "source_url": source_url,
                    "raw_excerpt": raw_markdown[:500] if raw_markdown else None,
                }
            )
    return results
