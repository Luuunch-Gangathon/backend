"""Tests for enrichment data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_property_result_valid():
    from app.agents.searchEngine.models import PropertyResult

    pr = PropertyResult(
        value={"cas_number": "557-04-0", "synonyms": ["magnesium octadecanoate"]},
        confidence="verified",
        source_name="pubchem",
        source_url_or_reasoning="https://pubchem.ncbi.nlm.nih.gov/compound/11177",
    )
    assert pr.confidence == "verified"
    assert pr.source_name == "pubchem"


def test_property_result_unknown():
    from app.agents.searchEngine.models import PropertyResult

    pr = PropertyResult(
        value=None,
        confidence="unknown",
        source_name=None,
        source_url_or_reasoning=None,
    )
    assert pr.confidence == "unknown"
    assert pr.value is None


def test_property_result_invalid_confidence():
    from app.agents.searchEngine.models import PropertyResult

    with pytest.raises(ValidationError):
        PropertyResult(
            value="something",
            confidence="super_trusted",
            source_name="test",
            source_url_or_reasoning=None,
            )


def test_enrichment_result_valid():
    from app.agents.searchEngine.models import EnrichmentResult, PropertyResult

    pr = PropertyResult(
        value=True,
        confidence="verified",
        source_name="pubchem",
        source_url_or_reasoning="https://example.com",
    )
    er = EnrichmentResult(
        material_id="ing_db_42",
        raw_sku="RM-C5-magnesium-stearate-c3a91d20",
        normalized_name="magnesium stearate",
        company_id="co_db_5",
        supplier_ids=["sup_db_12"],
        enriched_at="2026-04-18T02:30:00Z",
        completeness=1,
        total_properties=9,
        properties={"chemical_identity": pr},
    )
    assert er.material_id == "ing_db_42"
    assert er.completeness == 1
    assert "chemical_identity" in er.properties


def test_enrichment_result_empty_properties():
    from app.agents.searchEngine.models import EnrichmentResult

    er = EnrichmentResult(
        material_id="ing_db_1",
        raw_sku="RM-C1-test-abc12345",
        normalized_name="test",
        company_id="co_db_1",
        supplier_ids=[],
        enriched_at="2026-04-18T00:00:00Z",
        completeness=0,
        total_properties=9,
        properties={},
    )
    assert er.completeness == 0
    assert er.properties == {}
