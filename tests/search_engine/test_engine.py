"""Tests for the enrichment engine waterfall loop."""

from __future__ import annotations

from unittest.mock import patch



# Active SOURCES (from config): supplier_website (verified/*), llm_knowledge (inferred/*), llm_general_fallback (speculative/*)

def _fake_supplier_website(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "source_origin",
                "value": "plant",
                "source_url": "https://purebulk.com/products/magnesium-stearate",
                "raw_excerpt": "plant-derived",
            }
        ]
    return []


def _fake_llm_knowledge(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "functional_role",
                "value": ["lubricant", "flow agent"],
                "source_url": None,
                "raw_excerpt": "LLM knowledge",
            }
        ]
    return []


def _fake_handler_empty(name: str, context: dict) -> list[dict]:
    return []


def test_engine_fills_properties_from_multiple_sources():
    from app.agents.searchEngine.engine import run_enrichment

    # supplier_website (verified/*) fills source_origin
    # llm_knowledge (inferred/*) fills functional_role
    fake_handlers = {
        "supplier_website": _fake_supplier_website,
        "llm_knowledge": _fake_llm_knowledge,
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

    assert result.properties["source_origin"].confidence == "verified"
    assert result.properties["source_origin"].source_name == "supplier_website"

    assert result.properties["functional_role"].confidence == "inferred"
    assert result.properties["functional_role"].source_name == "llm_knowledge"

    assert result.completeness == 2


def test_engine_skips_property_already_filled():
    """Verified source fills property; inferred source must not overwrite it."""
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
        "supplier_website": _fake_supplier_website,   # verified — fills source_origin = "plant"
        "llm_knowledge": _logging_llm_handler,        # inferred — also returns source_origin
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

    # supplier_website (verified) filled source_origin; llm_knowledge must not overwrite
    assert result.properties["source_origin"].source_name == "supplier_website"
    assert result.properties["source_origin"].value == "plant"
    assert result.properties["source_origin"].confidence == "verified"


def test_engine_unfilled_properties_are_unknown():
    from app.agents.searchEngine.engine import run_enrichment

    fake_handlers = {
        "supplier_website": _fake_handler_empty,
        "llm_knowledge": _fake_handler_empty,
        "llm_general_fallback": _fake_handler_empty,
    }

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
    """Inferred source fills when no verified source has the property."""
    from app.agents.searchEngine.engine import run_enrichment

    def _llm_handler(name: str, context: dict) -> list[dict]:
        return [
            {
                "property": "source_origin",
                "value": "mineral",
                "source_url": None,
                "raw_excerpt": "LLM inferred",
            }
        ]

    fake_handlers = {
        "supplier_website": _fake_handler_empty,   # verified — returns nothing
        "llm_knowledge": _llm_handler,             # inferred — fills source_origin
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

    # llm_knowledge (inferred) filled since supplier_website (verified) had nothing
    assert result.properties["source_origin"].confidence == "inferred"
    assert result.properties["source_origin"].source_name == "llm_knowledge"
