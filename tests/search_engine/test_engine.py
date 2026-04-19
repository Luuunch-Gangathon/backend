"""Tests for the enrichment engine waterfall loop."""

from __future__ import annotations


def _fake_handler_foodb(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "source_origin",
                "value": "plant",
                "source_url": "https://foodb.ca/compounds/FDB001234",
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
            }
        ]
    return []


def _fake_handler_empty(name: str, context: dict) -> list[dict]:
    return []


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

_TEST_PROPERTIES = [
    "functional_role", "source_origin", "dietary_flags", "allergens",
    "certifications", "regulatory_status", "form_grade", "price",
]

_CONTEXT = {
    "material_id": "ing_db_42",
    "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
    "company_id": "co_db_52",
    "supplier_ids": [],
}


def test_engine_fills_properties_from_multiple_sources():
    from app.agents.searchEngine.engine import run_enrichment

    fake_handlers = {s["name"]: _fake_handler_empty for s in _TEST_SOURCES}
    fake_handlers["chebi"] = _fake_handler_chebi
    fake_handlers["foodb"] = _fake_handler_foodb

    result = run_enrichment(
        "magnesium stearate",
        _CONTEXT,
        properties=_TEST_PROPERTIES,
        sources=_TEST_SOURCES,
        handlers=fake_handlers,
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
            }
        ]

    fake_handlers = {s["name"]: _fake_handler_empty for s in _TEST_SOURCES}
    fake_handlers["foodb"] = _fake_handler_foodb
    fake_handlers["llm_knowledge"] = _logging_llm_handler

    result = run_enrichment(
        "magnesium stearate",
        _CONTEXT,
        properties=_TEST_PROPERTIES,
        sources=_TEST_SOURCES,
        handlers=fake_handlers,
    )

    assert result.properties["source_origin"].source_name == "foodb"
    assert result.properties["source_origin"].value == "plant"


def test_engine_unfilled_properties_are_unknown():
    from app.agents.searchEngine.engine import run_enrichment

    fake_handlers = {s["name"]: _fake_handler_empty for s in _TEST_SOURCES}

    result = run_enrichment(
        "unknown material",
        {
            "material_id": "ing_db_999",
            "raw_sku": "RM-C1-unknown-material-00000000",
            "company_id": "co_db_1",
            "supplier_ids": [],
        },
        properties=_TEST_PROPERTIES,
        sources=_TEST_SOURCES,
        handlers=fake_handlers,
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
            }
        ]

    fake_handlers = {s["name"]: _fake_handler_empty for s in _TEST_SOURCES}
    fake_handlers["retail_page"] = _retail_handler

    result = run_enrichment(
        "magnesium stearate",
        _CONTEXT,
        properties=_TEST_PROPERTIES,
        sources=_TEST_SOURCES,
        handlers=fake_handlers,
    )

    assert result.properties["source_origin"].confidence == "probable"
    assert result.properties["source_origin"].source_name == "retail_page"
