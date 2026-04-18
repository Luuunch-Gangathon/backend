"""Tests for supplier website handler."""

from __future__ import annotations


def test_material_properties_schema():
    from app.api.search_engine.sources.supplier_website import MaterialProperties

    props = MaterialProperties(
        is_correct_material=True,
        chemical_identity={"cas_number": "557-04-0"},
        functional_role=["lubricant"],
        source_origin="plant",
        dietary_flags={"vegan": True},
        allergens={"contains": [], "free_from": ["soy"]},
        certifications=["Non-GMO"],
        regulatory_status={"gras": True},
        form_grade={"form": "powder"},
        price="$25/kg",
    )
    assert props.is_correct_material is True
    assert props.chemical_identity == {"cas_number": "557-04-0"}


def test_material_properties_all_none():
    from app.api.search_engine.sources.supplier_website import MaterialProperties

    props = MaterialProperties(is_correct_material=False)
    assert props.chemical_identity is None
    assert props.allergens is None


def test_convert_to_handler_results():
    from app.api.search_engine.sources.supplier_website import (
        MaterialProperties,
        convert_to_handler_results,
    )

    props = MaterialProperties(
        is_correct_material=True,
        chemical_identity={"cas_number": "557-04-0"},
        functional_role=["lubricant"],
        source_origin=None,
        dietary_flags=None,
        allergens={"contains": [], "free_from": ["soy"]},
        certifications=None,
        regulatory_status=None,
        form_grade=None,
        price=None,
    )

    results = convert_to_handler_results(props, source_url="https://purebulk.com/products/mag", raw_markdown="page text")

    property_names = [r["property"] for r in results]
    assert "chemical_identity" in property_names
    assert "functional_role" in property_names
    assert "allergens" in property_names
    assert "source_origin" not in property_names
    assert "price" not in property_names

    chem = next(r for r in results if r["property"] == "chemical_identity")
    assert chem["value"] == {"cas_number": "557-04-0"}
    assert chem["source_url"] == "https://purebulk.com/products/mag"
    assert chem["raw_excerpt"] == "page text"


def test_convert_to_handler_results_wrong_material():
    from app.api.search_engine.sources.supplier_website import (
        MaterialProperties,
        convert_to_handler_results,
    )

    props = MaterialProperties(
        is_correct_material=False,
        chemical_identity={"cas_number": "999-99-9"},
    )

    results = convert_to_handler_results(props, source_url="https://example.com", raw_markdown="wrong page")
    assert results == []
