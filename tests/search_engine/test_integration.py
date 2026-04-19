"""Integration test — full pipeline from raw DB fields to stored result."""

from __future__ import annotations

from unittest.mock import patch


def _fake_foodb(name: str, context: dict) -> list[dict]:
    return [
        {
            "property": "source_origin",
            "value": "plant",
            "source_url": "https://foodb.ca/compounds/FDB001234",
        }
    ]


def _fake_empty(name: str, context: dict) -> list[dict]:
    return []


_ALL_SOURCE_NAMES = [
    "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
    "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
    "web_search", "llm_knowledge", "llm_general_fallback", "llm_enrichment",
]

_TEST_SOURCES = [
    {"name": "supplier_website", "trust_tier": "verified", "provides": ["*"]},
    {"name": "chebi", "trust_tier": "verified", "provides": ["functional_role"]},
    {"name": "foodb", "trust_tier": "verified", "provides": ["source_origin"]},
    {"name": "open_food_facts", "trust_tier": "verified", "provides": ["allergens", "dietary_flags", "certifications"]},
    {"name": "nih_dsld", "trust_tier": "verified", "provides": ["dietary_flags", "certifications"]},
    {"name": "openfda", "trust_tier": "verified", "provides": ["regulatory_status"]},
    {"name": "fda_eafus", "trust_tier": "verified", "provides": ["regulatory_status"]},
    {"name": "efsa", "trust_tier": "verified", "provides": ["regulatory_status"]},
    {"name": "retail_page", "trust_tier": "probable", "provides": ["*"]},
    {"name": "llm_knowledge", "trust_tier": "inferred", "provides": ["*"]},
    {"name": "llm_general_fallback", "trust_tier": "speculative", "provides": ["*"]},
]


def test_full_pipeline():
    from app.agents.searchEngine import enrich

    fake_handlers = {s: _fake_empty for s in _ALL_SOURCE_NAMES}
    fake_handlers["foodb"] = _fake_foodb

    raw_fields = {
        "Id": 42,
        "SKU": "RM-C52-magnesium-stearate-c3a91d20",
        "CompanyId": 52,
        "SupplierIds": [12, 7],
    }

    with patch("app.agents.searchEngine.handlers.SOURCE_HANDLERS", fake_handlers), \
         patch("app.agents.searchEngine.shortened_config.SHORTENED_MATERIAL_SOURCES", _TEST_SOURCES):
        result = enrich(raw_fields)

    assert result.material_id == "ing_db_42"
    assert result.normalized_name == "magnesium stearate"
    assert result.company_id == "co_db_52"
    assert result.supplier_ids == ["sup_db_12", "sup_db_7"]
    assert result.completeness == 1
    assert result.properties["source_origin"].source_name == "foodb"
    assert result.properties["source_origin"].confidence == "verified"


def test_full_pipeline_unknown_material():
    from app.agents.searchEngine import enrich

    fake_handlers = {s: _fake_empty for s in _ALL_SOURCE_NAMES}

    raw_fields = {
        "Id": 999,
        "SKU": "RM-C1-mystery-compound-00000000",
        "CompanyId": 1,
    }

    with patch("app.agents.searchEngine.handlers.SOURCE_HANDLERS", fake_handlers), \
         patch("app.agents.searchEngine.shortened_config.SHORTENED_MATERIAL_SOURCES", _TEST_SOURCES):
        result = enrich(raw_fields)

    assert result.completeness == 0
    assert all(
        p.confidence == "unknown" for p in result.properties.values()
    )
