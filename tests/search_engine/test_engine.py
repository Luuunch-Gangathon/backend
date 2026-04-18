"""Tests for the enrichment engine waterfall loop."""

from __future__ import annotations

from unittest.mock import patch


def _fake_handler_pubchem(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "chemical_identity",
                "value": {"cas_number": "557-04-0"},
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/11177",
                "raw_excerpt": "CAS 557-04-0",
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
    from app.api.search_engine.engine import run_enrichment

    fake_handlers = {
        "supplier_website": _fake_handler_empty,
        "pubchem": _fake_handler_pubchem,
        "chebi": _fake_handler_chebi,
        "foodb": _fake_handler_empty,
        "open_food_facts": _fake_handler_empty,
        "nih_dsld": _fake_handler_empty,
        "openfda": _fake_handler_empty,
        "fda_eafus": _fake_handler_empty,
        "efsa": _fake_handler_empty,
        "retail_page": _fake_handler_empty,
        "web_search": _fake_handler_empty,
        "llm_knowledge": _fake_handler_empty,
    }

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    assert "chemical_identity" in result.properties
    assert result.properties["chemical_identity"].confidence == "verified"
    assert result.properties["chemical_identity"].source_name == "pubchem"

    assert "functional_role" in result.properties
    assert result.properties["functional_role"].source_name == "chebi"

    assert result.completeness == 2


def test_engine_skips_property_already_filled():
    """If a higher-trust source already filled a property, lower sources are not tried."""
    from app.api.search_engine.engine import run_enrichment

    call_log = []

    def _logging_handler(name: str, context: dict) -> list[dict]:
        call_log.append("web_search")
        return [
            {
                "property": "chemical_identity",
                "value": {"cas_number": "000-00-0"},
                "source_url": "https://blog.example.com",
                "raw_excerpt": "some blog",
            }
        ]

    fake_handlers = {
        "supplier_website": _fake_handler_empty,
        "pubchem": _fake_handler_pubchem,
        "chebi": _fake_handler_empty,
        "foodb": _fake_handler_empty,
        "open_food_facts": _fake_handler_empty,
        "nih_dsld": _fake_handler_empty,
        "openfda": _fake_handler_empty,
        "fda_eafus": _fake_handler_empty,
        "efsa": _fake_handler_empty,
        "retail_page": _fake_handler_empty,
        "web_search": _logging_handler,
        "llm_knowledge": _fake_handler_empty,
    }

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    # pubchem (verified) filled chemical_identity, so web_search should not
    # have been called for chemical_identity
    assert result.properties["chemical_identity"].source_name == "pubchem"
    # web_search provides "*" so it COULD be called for other unfilled properties,
    # but it must not have overwritten chemical_identity
    assert result.properties["chemical_identity"].value == {"cas_number": "557-04-0"}


def test_engine_unfilled_properties_are_unknown():
    from app.api.search_engine.engine import run_enrichment

    fake_handlers = {s: _fake_handler_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge",
    ]}

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
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
    from app.api.search_engine.engine import run_enrichment

    def _retail_handler(name: str, context: dict) -> list[dict]:
        return [
            {
                "property": "chemical_identity",
                "value": {"cas_number": "999-99-9"},
                "source_url": "https://iherb.com/product",
                "raw_excerpt": "from retail",
            }
        ]

    fake_handlers = {s: _fake_handler_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa",
        "web_search", "llm_knowledge",
    ]}
    fake_handlers["retail_page"] = _retail_handler

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
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
    assert result.properties["chemical_identity"].confidence == "probable"
    assert result.properties["chemical_identity"].source_name == "retail_page"
