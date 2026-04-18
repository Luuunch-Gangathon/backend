"""Tests for the Open Food Facts source handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(products: list[dict], status_code: int = 200) -> MagicMock:
    """Return a mock httpx.Response that yields the given products JSON."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {"products": products, "count": len(products)}
    mock_resp.raise_for_status = MagicMock()  # no-op for 200
    return mock_resp


def _make_error_response(status_code: int = 500) -> MagicMock:
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_resp
    )
    return mock_resp


# ---------------------------------------------------------------------------
# _clean_tag
# ---------------------------------------------------------------------------

def test_clean_tag_strips_prefix_and_formats():
    from app.api.search_engine.sources.open_food_facts import _clean_tag

    assert _clean_tag("en:gluten-free") == "Gluten Free"
    assert _clean_tag("en:organic") == "Organic"
    assert _clean_tag("fr:sans-gluten") == "Sans Gluten"


def test_clean_tag_no_prefix():
    from app.api.search_engine.sources.open_food_facts import _clean_tag

    assert _clean_tag("non-gmo") == "Non Gmo"


def test_clean_tag_no_hyphens():
    from app.api.search_engine.sources.open_food_facts import _clean_tag

    assert _clean_tag("en:vegan") == "Vegan"


# ---------------------------------------------------------------------------
# _aggregate
# ---------------------------------------------------------------------------

def test_aggregate_extracts_allergens():
    from app.api.search_engine.sources.open_food_facts import _aggregate

    products = [
        {"allergens_tags": ["en:gluten", "en:milk"], "labels_tags": []},
        {"allergens_tags": ["en:gluten"], "labels_tags": []},  # duplicate — should dedup
    ]
    result = _aggregate(products)
    assert "Gluten" in result["allergens"]
    assert "Milk" in result["allergens"]
    assert len(result["allergens"]) == 2  # deduped


def test_aggregate_extracts_dietary_flags():
    from app.api.search_engine.sources.open_food_facts import _aggregate

    products = [
        {"allergens_tags": [], "labels_tags": ["en:vegan", "en:organic"]},
        {"allergens_tags": [], "labels_tags": ["en:vegetarian"]},
    ]
    result = _aggregate(products)
    assert result["dietary_flags"].get("vegan") is True
    assert result["dietary_flags"].get("vegetarian") is True
    # organic is a certification, not dietary
    assert "organic" not in result["dietary_flags"]


def test_aggregate_extracts_certifications():
    from app.api.search_engine.sources.open_food_facts import _aggregate

    products = [
        {"allergens_tags": [], "labels_tags": ["en:organic", "en:non-gmo"]},
    ]
    result = _aggregate(products)
    assert "Organic" in result["certifications"]
    assert "Non Gmo" in result["certifications"]


def test_aggregate_empty_products():
    from app.api.search_engine.sources.open_food_facts import _aggregate

    result = _aggregate([])
    assert result["allergens"] == []
    assert result["dietary_flags"] == {}
    assert result["certifications"] == []


# ---------------------------------------------------------------------------
# open_food_facts_enrich — success with all 3 properties
# ---------------------------------------------------------------------------

def test_enrich_returns_all_three_properties():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    products = [
        {
            "allergens_tags": ["en:gluten", "en:milk"],
            "labels_tags": ["en:vegan", "en:organic", "en:halal"],
        },
        {
            "allergens_tags": ["en:gluten"],
            "labels_tags": ["en:vegetarian", "en:non-gmo"],
        },
    ]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("oat flour", {})

    property_names = [r["property"] for r in results]
    assert "allergens" in property_names
    assert "dietary_flags" in property_names
    assert "certifications" in property_names
    assert len(results) == 3


def test_enrich_allergens_structure():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    products = [{"allergens_tags": ["en:gluten", "en:milk"], "labels_tags": []}]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("wheat flour", {})

    allergen_result = next(r for r in results if r["property"] == "allergens")
    value = allergen_result["value"]
    assert "contains" in value
    assert "free_from" in value
    assert "Gluten" in value["contains"]
    assert "Milk" in value["contains"]
    assert value["free_from"] == []


def test_enrich_dietary_flags_structure():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    products = [{"allergens_tags": [], "labels_tags": ["en:vegan", "en:halal"]}]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("chickpea flour", {})

    dietary_result = next(r for r in results if r["property"] == "dietary_flags")
    value = dietary_result["value"]
    assert value.get("vegan") is True
    assert value.get("halal") is True


def test_enrich_certifications_structure():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    products = [{"allergens_tags": [], "labels_tags": ["en:organic", "en:non-gmo"]}]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("sunflower oil", {})

    cert_result = next(r for r in results if r["property"] == "certifications")
    value = cert_result["value"]
    assert "Organic" in value
    assert "Non Gmo" in value


def test_enrich_source_url_present():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    products = [{"allergens_tags": ["en:gluten"], "labels_tags": []}]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("bread", {})

    for r in results:
        assert r["source_url"] is not None
        assert "openfoodfacts" in r["source_url"]


# ---------------------------------------------------------------------------
# open_food_facts_enrich — no products found
# ---------------------------------------------------------------------------

def test_enrich_no_products_returns_empty():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    mock_resp = _make_response([])

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("xanthan gum", {})

    assert results == []


# ---------------------------------------------------------------------------
# open_food_facts_enrich — API error
# ---------------------------------------------------------------------------

def test_enrich_api_error_returns_empty():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    with patch("httpx.get", side_effect=httpx.RequestError("Connection refused", request=MagicMock())):
        results = open_food_facts_enrich("guar gum", {})

    assert results == []


def test_enrich_http_status_error_returns_empty():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    mock_resp = _make_error_response(500)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("lecithin", {})

    assert results == []


# ---------------------------------------------------------------------------
# open_food_facts_enrich — partial data (only some properties present)
# ---------------------------------------------------------------------------

def test_enrich_only_allergens_no_labels():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    products = [{"allergens_tags": ["en:soy"], "labels_tags": []}]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("soy flour", {})

    property_names = [r["property"] for r in results]
    assert "allergens" in property_names
    assert "dietary_flags" not in property_names
    assert "certifications" not in property_names


def test_enrich_only_labels_no_allergens():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    products = [{"allergens_tags": [], "labels_tags": ["en:kosher", "en:organic"]}]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("sugar", {})

    property_names = [r["property"] for r in results]
    assert "allergens" not in property_names
    assert "dietary_flags" in property_names
    assert "certifications" in property_names


def test_enrich_products_with_no_relevant_tags():
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    # Products exist but carry no useful tag data
    products = [{"allergens_tags": [], "labels_tags": []}]
    mock_resp = _make_response(products)

    with patch("httpx.get", return_value=mock_resp):
        results = open_food_facts_enrich("water", {})

    assert results == []


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def test_handler_is_registered():
    from app.api.search_engine.handlers import SOURCE_HANDLERS
    from app.api.search_engine.sources.open_food_facts import open_food_facts_enrich

    # The stub in handlers.py delegates to this real impl once wired.
    # For now we just verify the key exists.
    assert "open_food_facts" in SOURCE_HANDLERS
