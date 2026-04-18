"""Integration test — full pipeline from raw DB fields to stored result."""

from __future__ import annotations

from unittest.mock import patch


def _fake_pubchem(name: str, context: dict) -> list[dict]:
    return [
        {
            "property": "chemical_identity",
            "value": {"cas_number": "557-04-0", "synonyms": ["magnesium octadecanoate"]},
            "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/11177",
            "raw_excerpt": "CAS 557-04-0",
        }
    ]


def _fake_empty(name: str, context: dict) -> list[dict]:
    return []


def test_full_pipeline():
    from app.api.search_engine import enrich
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()

    fake_handlers = {s: _fake_empty for s in [
        "supplier_website", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge",
    ]}
    fake_handlers["pubchem"] = _fake_pubchem

    raw_fields = {
        "Id": 42,
        "SKU": "RM-C52-magnesium-stearate-c3a91d20",
        "CompanyId": 52,
        "SupplierIds": [12, 7],
    }

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = enrich(raw_fields, store=store)

    # Check the result
    assert result.material_id == "ing_db_42"
    assert result.normalized_name == "magnesium stearate"
    assert result.company_id == "co_db_52"
    assert result.supplier_ids == ["sup_db_12", "sup_db_7"]
    assert result.completeness == 1
    assert result.properties["chemical_identity"].source_name == "pubchem"
    assert result.properties["chemical_identity"].confidence == "verified"

    # Check it was persisted
    stored = store.get("ing_db_42")
    assert stored is not None
    assert stored["material_id"] == "ing_db_42"


def test_full_pipeline_unknown_material():
    from app.api.search_engine import enrich
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()

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

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = enrich(raw_fields, store=store)

    assert result.completeness == 0
    assert all(
        p.confidence == "unknown" for p in result.properties.values()
    )
