"""Integration test — full pipeline from raw DB fields to stored result."""

from __future__ import annotations

from unittest.mock import patch


def _fake_foodb(name: str, context: dict) -> list[dict]:
    return [
        {
            "property": "source_origin",
            "value": "plant",
            "source_url": "https://foodb.ca/compounds/FDB001234",
            "raw_excerpt": "plant-derived",
        }
    ]


def _fake_empty(name: str, context: dict) -> list[dict]:
    return []


def test_full_pipeline():
    from app.agents.searchEngine import enrich

    fake_handlers = {s: _fake_empty for s in [
        "supplier_website", "pubchem", "chebi", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge", "llm_general_fallback",
    ]}
    fake_handlers["foodb"] = _fake_foodb

    raw_fields = {
        "Id": 42,
        "SKU": "RM-C52-magnesium-stearate-c3a91d20",
        "CompanyId": 52,
        "SupplierIds": [12, 7],
    }

    with patch("app.agents.searchEngine.engine.SOURCE_HANDLERS", fake_handlers):
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

    fake_handlers = {s: _fake_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge",
    ]}

    raw_fields = {
        "Id": 999,
        "SKU": "RM-C1-mystery-compound-00000000",
        "CompanyId": 1,
    }

    with patch("app.agents.searchEngine.engine.SOURCE_HANDLERS", fake_handlers):
        result = enrich(raw_fields)

    assert result.completeness == 0
    assert all(
        p.confidence == "unknown" for p in result.properties.values()
    )
