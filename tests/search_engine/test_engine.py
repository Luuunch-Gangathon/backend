"""Tests for the enrichment engine waterfall loop."""

from __future__ import annotations

from unittest.mock import patch


def _fake_handler_foodb(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "source_origin",
                "value": "plant",
                "source_url": "https://foodb.ca/compounds/FDB001234",
                "raw_excerpt": "plant-derived",
            }
        ]
    return []


def _fake_handler_chebi(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "functional_role",
                "value": ["lubricant", "flow agent"],
                "source_url": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=9243",
                "raw_excerpt": "Role: lubricant",
            }
        ]
    return []


def _fake_handler_empty(name: str, context: dict) -> list[dict]:
    return []


def test_engine_fills_properties_from_multiple_sources():
    from app.agents.searchEngine.engine import run_enrichment

    fake_handlers = {
        "supplier_website": _fake_handler_empty,
        "pubchem": _fake_handler_empty,
        "chebi": _fake_handler_chebi,
        "foodb": _fake_handler_foodb,
        "open_food_facts": _fake_handler_empty,
        "nih_dsld": _fake_handler_empty,
        "openfda": _fake_handler_empty,
        "fda_eafus": _fake_handler_empty,
        "efsa": _fake_handler_empty,
        "retail_page": _fake_handler_empty,
        "web_search": _fake_handler_empty,
        "llm_knowledge": _fake_handler_empty,
        "llm_general_fallback": _fake_handler_empty,
    }

    with patch("app.agents.searchEngine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    assert "source_origin" in result.properties
    assert result.properties["source_origin"].confidence == "verified"
    assert result.properties["source_origin"].source_name == "foodb"

    assert "functional_role" in result.properties
    assert result.properties["functional_role"].source_name == "chebi"

    assert result.completeness == 2


def test_engine_skips_property_already_filled():
    """If a higher-trust source already filled a property, lower sources are not tried."""
    from app.agents.searchEngine.engine import run_enrichment

    call_log = []

    def _logging_llm_handler(name: str, context: dict) -> list[dict]:
        call_log.append("llm_knowledge")
        return [
            {
                "property": "source_origin",
                "value": "synthetic",
                "source_url": None,
                "raw_excerpt": "LLM guess",
            }
        ]

    fake_handlers = {
        "supplier_website": _fake_handler_empty,
        "pubchem": _fake_handler_empty,
        "chebi": _fake_handler_empty,
        "foodb": _fake_handler_foodb,
        "open_food_facts": _fake_handler_empty,
        "nih_dsld": _fake_handler_empty,
        "openfda": _fake_handler_empty,
        "fda_eafus": _fake_handler_empty,
        "efsa": _fake_handler_empty,
        "retail_page": _fake_handler_empty,
        "web_search": _fake_handler_empty,
        "llm_knowledge": _logging_llm_handler,
        "llm_general_fallback": _fake_handler_empty,
    }

    with patch("app.agents.searchEngine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    # foodb (verified) filled source_origin, so llm_knowledge must not overwrite it
    assert result.properties["source_origin"].source_name == "foodb"
    assert result.properties["source_origin"].value == "plant"


def test_engine_unfilled_properties_are_unknown():
    from app.agents.searchEngine.engine import run_enrichment

    fake_handlers = {s: _fake_handler_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge",
    ]}

    with patch("app.agents.searchEngine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "unknown material",
            {
                "material_id": "ing_db_999",
                "raw_sku": "RM-C1-unknown-material-00000000",
                "company_id": "co_db_1",
                "supplier_ids": [],
            },
        )

    assert result.completeness == 0
    for prop_name in result.properties:
        assert result.properties[prop_name].confidence == "unknown"


def test_engine_respects_trust_tier_order():
    """A 'probable' source should only fill if no 'verified' source did."""
    from app.agents.searchEngine.engine import run_enrichment

    def _retail_handler(name: str, context: dict) -> list[dict]:
        return [
            {
                "property": "source_origin",
                "value": "mineral",
                "source_url": "https://iherb.com/product",
                "raw_excerpt": "from retail",
            }
        ]

    fake_handlers = {s: _fake_handler_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa",
        "web_search", "llm_knowledge", "llm_general_fallback",
    ]}
    fake_handlers["retail_page"] = _retail_handler

    with patch("app.agents.searchEngine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    # retail_page is "probable" — should still fill since no verified source had it
    assert result.properties["source_origin"].confidence == "probable"
    assert result.properties["source_origin"].source_name == "retail_page"
