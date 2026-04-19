"""Search engine configuration — properties, sources, trust tiers.

To adapt to a new domain (e.g. packaging materials), change PROPERTIES
and SOURCES here. The engine and handlers do not need modification.
"""

from __future__ import annotations

from app.agents.searchEngine.property_schema import PROPERTY_TEMPLATES

PROPERTIES: list[str] = list(PROPERTY_TEMPLATES.keys())

TRUST_TIERS: list[str] = ["verified", "probable", "inferred", "speculative"]

SOURCES: list[dict] = [
    {
        "name": "supplier_website",
        "trust_tier": "verified",
        "provides": ["*"],
    },
    # {
    #     "name": "chebi",  # only finds pure chemicals, misses ingredient trade names
    #     "trust_tier": "verified",
    #     "provides": ["functional_role"],
    # },
    # {
    #     "name": "open_food_facts",  # product DB, not ingredient DB — returns misleading data for raw materials
    #     "trust_tier": "verified",
    #     "provides": ["allergens", "dietary_flags", "certifications"],
    # },
    # {
    #     "name": "openfda",  # returns recalls for products containing the ingredient, not about the ingredient itself
    #     "trust_tier": "verified",
    #     "provides": ["regulatory_status"],
    # },
    # {
    #     "name": "pubchem",
    #     "trust_tier": "verified",
    #     "provides": ["chemical_identity"],
    # },
    # {
    #     "name": "foodb",  # API availability uncertain
    #     "trust_tier": "verified",
    #     "provides": ["source_origin"],
    # },
    # {
    #     "name": "nih_dsld",  # Cloudflare blocked
    #     "trust_tier": "verified",
    #     "provides": ["dietary_flags", "certifications"],
    # },
    # {
    #     "name": "fda_eafus",  # not implemented — CSV download TODO
    #     "trust_tier": "verified",
    #     "provides": ["regulatory_status"],
    # },
    # {
    #     "name": "efsa",  # not implemented
    #     "trust_tier": "verified",
    #     "provides": ["regulatory_status"],
    # },
    # {
    #     "name": "retail_page",  # not implemented
    #     "trust_tier": "probable",
    #     "provides": ["*"],
    # },
    # {
    #     "name": "web_search",  # picks irrelevant pages, needs fine-tuning
    #     "trust_tier": "inferred",
    #     "provides": ["*"],
    # },
    # {
    #     "name": "llm_knowledge",  # replaced by llm_enrichment
    #     "trust_tier": "inferred",
    #     "provides": ["*"],
    # },
    # {
    #     "name": "llm_general_fallback",  # replaced by llm_enrichment
    #     "trust_tier": "speculative",
    #     "provides": ["*"],
    # },
    {
        "name": "llm_enrichment",
        "trust_tier": "inferred",  # individual properties may be downgraded to speculative based on self-assessed confidence
        "provides": ["*"],
    },
]
