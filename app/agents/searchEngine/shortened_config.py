"""Demo search engine configuration — limited sources for fast enrichment.

Uses only supplier_website scraping and LLM fallbacks.
Skips slow/unreliable public APIs (ChEBI, FooDB, NIH DSLD, openFDA, OFF, etc.)
"""

from __future__ import annotations

from app.agents.searchEngine.property_schema import PROPERTY_TEMPLATES
from app.agents.searchEngine.product_property_schema import PRODUCT_PROPERTY_TEMPLATES

SHORTENED_MATERIAL_PROPERTIES: list[str] = list(PROPERTY_TEMPLATES.keys())

SHORTENED_MATERIAL_SOURCES: list[dict] = [
    {
        "name": "supplier_website",
        "trust_tier": "verified",
        "provides": ["*"],
    },
    {
        "name": "llm_knowledge",
        "trust_tier": "inferred",
        "provides": ["*"],
    },
    {
        "name": "llm_general_fallback",
        "trust_tier": "speculative",
        "provides": ["*"],
    },
]

SHORTENED_PRODUCT_PROPERTIES: list[str] = list(PRODUCT_PROPERTY_TEMPLATES.keys())

SHORTENED_PRODUCT_SOURCES: list[dict] = [
    {
        "name": "open_food_facts_product",
        "trust_tier": "verified",
        "provides": ["dietary_flags", "allergens", "certifications", "form_grade"],
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
