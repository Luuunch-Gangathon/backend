"""Tests for search engine configuration."""

from __future__ import annotations


def test_properties_is_list_of_strings():
    from app.agents.searchEngine.config import PROPERTIES

    assert isinstance(PROPERTIES, list)
    assert len(PROPERTIES) == 8
    assert all(isinstance(p, str) for p in PROPERTIES)


def test_properties_contains_expected():
    from app.agents.searchEngine.config import PROPERTIES

    expected = [
        "functional_role",
        "source_origin",
        "dietary_flags",
        "allergens",
        "certifications",
        "regulatory_status",
        "form_grade",
        "price",
    ]
    assert PROPERTIES == expected


def test_trust_tiers_order():
    from app.agents.searchEngine.config import TRUST_TIERS

    assert TRUST_TIERS == ["verified", "probable", "inferred", "speculative"]


def test_sources_have_required_fields():
    from app.agents.searchEngine.config import SOURCES

    for source in SOURCES:
        assert "name" in source
        assert "trust_tier" in source
        assert "provides" in source
        assert source["trust_tier"] in ("verified", "probable", "inferred", "speculative")
        assert isinstance(source["provides"], list)


def test_sources_trust_tiers_are_valid():
    from app.agents.searchEngine.config import SOURCES, TRUST_TIERS

    for source in SOURCES:
        assert source["trust_tier"] in TRUST_TIERS


def test_wildcard_sources_exist():
    from app.agents.searchEngine.config import SOURCES

    wildcard = [s for s in SOURCES if "*" in s["provides"]]
    assert len(wildcard) >= 1, "At least one source should provide '*'"


def test_every_property_has_at_least_one_source():
    from app.agents.searchEngine.config import PROPERTIES, SOURCES

    for prop in PROPERTIES:
        providers = [
            s for s in SOURCES if prop in s["provides"] or "*" in s["provides"]
        ]
        assert len(providers) >= 1, f"No source provides '{prop}'"
