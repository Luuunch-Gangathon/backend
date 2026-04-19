"""Product search engine configuration — properties and sources for finished goods.

Same pattern as config.py but for finished products (e.g. "Centrum Silver",
"Liquid I.V. Hydration Multiplier"). Uses a different property set and
different source handlers.
"""

from __future__ import annotations

from app.agents.searchEngine.product_property_schema import PRODUCT_PROPERTY_TEMPLATES

PRODUCT_PROPERTIES: list[str] = list(PRODUCT_PROPERTY_TEMPLATES.keys())

PRODUCT_SOURCES: list[dict] = [
    {
        "name": "open_food_facts_product",
        "trust_tier": "verified",
        "provides": ["dietary_flags", "allergens", "certifications", "form_grade"],
    },
    {
        "name": "openfda_product",
        "trust_tier": "verified",
        "provides": ["regulatory_status"],
    },
    {
        "name": "llm_knowledge_product",
        "trust_tier": "inferred",
        "provides": ["*"],
    },
    {
        "name": "llm_general_fallback_product",
        "trust_tier": "speculative",
        "provides": ["*"],
    },
]
