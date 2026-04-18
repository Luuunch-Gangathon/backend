"""Search engine configuration — properties, sources, trust tiers.

To adapt to a new domain (e.g. packaging materials), change PROPERTIES
and SOURCES here. The engine and handlers do not need modification.
"""

from __future__ import annotations

from app.api.search_engine.property_schema import PROPERTY_TEMPLATES

PROPERTIES: list[str] = list(PROPERTY_TEMPLATES.keys())

TRUST_TIERS: list[str] = ["verified", "probable", "inferred", "speculative"]

SOURCES: list[dict] = [
    {
        "name": "supplier_website",
        "trust_tier": "verified",
        "provides": ["*"],
    },
    # {
    #     "name": "pubchem",
    #     "trust_tier": "verified",
    #     "provides": ["chemical_identity"],
    # },
    {
        "name": "chebi",
        "trust_tier": "verified",
        "provides": ["functional_role"],
    },
    {
        "name": "foodb",
        "trust_tier": "verified",
        "provides": ["source_origin"],
    },
    {
        "name": "open_food_facts",
        "trust_tier": "verified",
        "provides": ["allergens", "dietary_flags", "certifications"],
    },
    {
        "name": "nih_dsld",
        "trust_tier": "verified",
        "provides": ["dietary_flags", "certifications"],
    },
    {
        "name": "openfda",
        "trust_tier": "verified",
        "provides": ["regulatory_status"],
    },
    {
        "name": "fda_eafus",
        "trust_tier": "verified",
        "provides": ["regulatory_status"],
    },
    {
        "name": "efsa",
        "trust_tier": "verified",
        "provides": ["regulatory_status"],
    },
    {
        "name": "retail_page",
        "trust_tier": "probable",
        "provides": ["*"],
    },
    # {
    #     "name": "web_search",  # temporarily excluded — needs fine-tuning (picks irrelevant pages, truncated content)
    #     "trust_tier": "inferred",
    #     "provides": ["*"],
    # },
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
