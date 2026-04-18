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


import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_crawl_and_extract_success():
    from app.api.search_engine.sources.supplier_website import _crawl_and_extract

    fake_extracted = json.dumps([{
        "is_correct_material": True,
        "chemical_identity": {"cas_number": "557-04-0"},
        "functional_role": ["lubricant"],
        "source_origin": "plant",
        "dietary_flags": None,
        "allergens": None,
        "certifications": ["Non-GMO"],
        "regulatory_status": None,
        "form_grade": None,
        "price": None,
    }])

    mock_result = MagicMock()
    mock_result.extracted_content = fake_extracted
    mock_result.markdown = "# Magnesium Stearate\nCAS: 557-04-0"

    mock_crawler = AsyncMock()
    mock_crawler.arun.return_value = mock_result
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.search_engine.sources.supplier_website.AsyncWebCrawler", return_value=mock_crawler):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = await _crawl_and_extract("https://purebulk.com/products/mag", "magnesium stearate")

    assert result is not None
    props, markdown = result
    assert props.is_correct_material is True
    assert props.chemical_identity == {"cas_number": "557-04-0"}
    assert "Magnesium Stearate" in markdown


@pytest.mark.asyncio
async def test_crawl_and_extract_wrong_material():
    from app.api.search_engine.sources.supplier_website import _crawl_and_extract

    fake_extracted = json.dumps([{
        "is_correct_material": False,
    }])

    mock_result = MagicMock()
    mock_result.extracted_content = fake_extracted
    mock_result.markdown = "# Some Other Product"

    mock_crawler = AsyncMock()
    mock_crawler.arun.return_value = mock_result
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.search_engine.sources.supplier_website.AsyncWebCrawler", return_value=mock_crawler):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = await _crawl_and_extract("https://example.com/wrong", "magnesium stearate")

    assert result is not None
    props, markdown = result
    assert props.is_correct_material is False


@pytest.mark.asyncio
async def test_crawl_and_extract_returns_none_on_error():
    from app.api.search_engine.sources.supplier_website import _crawl_and_extract

    mock_crawler = AsyncMock()
    mock_crawler.arun.side_effect = Exception("connection timeout")
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.search_engine.sources.supplier_website.AsyncWebCrawler", return_value=mock_crawler):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = await _crawl_and_extract("https://example.com", "magnesium stearate")

    assert result is None


@pytest.mark.asyncio
async def test_crawl_and_extract_returns_none_without_api_key():
    from app.api.search_engine.sources.supplier_website import _crawl_and_extract

    with patch.dict("os.environ", {}, clear=True):
        # Ensure ANTHROPIC_API_KEY is not set
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        result = await _crawl_and_extract("https://example.com", "magnesium stearate")

    assert result is None
