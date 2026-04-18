"""Tests for the FooDB source handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code: int, json_body=None) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = Exception("no body")

    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    else:
        resp.raise_for_status = MagicMock()

    return resp


# ---------------------------------------------------------------------------
# Fake API responses
# ---------------------------------------------------------------------------

_PLANT_COMPOUND_RESPONSE = {
    "data": [
        {
            "id": 12345,
            "public_id": "FDB012345",
            "name": "Quercetin",
            "kingdom": "Organic compounds",
            "direct_parent": "Flavonoids",
            "food_sources": [
                {"name": "spinach"},
                {"name": "kale"},
                {"name": "broccoli"},
                {"name": "apple fruit"},
                {"name": "onion"},
            ],
        }
    ]
}

_ANIMAL_COMPOUND_RESPONSE = {
    "data": [
        {
            "id": 99001,
            "public_id": "FDB099001",
            "name": "Taurine",
            "kingdom": "Organic compounds",
            "food_sources": [
                {"name": "beef meat"},
                {"name": "chicken"},
                {"name": "fish"},
                {"name": "milk dairy"},
            ],
        }
    ]
}

_MINERAL_COMPOUND_RESPONSE = {
    "data": [
        {
            "id": 55001,
            "public_id": "FDB055001",
            "name": "Magnesium stearate",
            "kingdom": "Inorganic compounds",
            "food_sources": [
                {"name": "magnesium mineral"},
                {"name": "calcium salt"},
            ],
        }
    ]
}

_EMPTY_RESPONSE = {"data": []}

_LIST_RESPONSE_PLANT = [
    {
        "id": 777,
        "public_id": "FDB000777",
        "name": "Chlorophyll",
        "food_sources": [
            {"name": "spinach leaf"},
            {"name": "herb plant"},
        ],
    }
]


# ---------------------------------------------------------------------------
# _classify_origin unit tests
# ---------------------------------------------------------------------------

def test_classify_origin_plant():
    from app.api.search_engine.sources.foodb import _classify_origin

    result = _classify_origin(["spinach", "kale", "broccoli", "apple fruit"])
    assert result == "plant"


def test_classify_origin_animal():
    from app.api.search_engine.sources.foodb import _classify_origin

    result = _classify_origin(["beef meat", "chicken", "fish"])
    assert result == "animal"


def test_classify_origin_mineral():
    from app.api.search_engine.sources.foodb import _classify_origin

    result = _classify_origin(["salt mineral", "calcium rock"])
    assert result == "mineral"


def test_classify_origin_empty_returns_none():
    from app.api.search_engine.sources.foodb import _classify_origin

    assert _classify_origin([]) is None


def test_classify_origin_no_keywords_returns_none():
    from app.api.search_engine.sources.foodb import _classify_origin

    # Names that match none of the keyword lists
    assert _classify_origin(["XYZ compound", "unknown substance"]) is None


def test_classify_origin_majority_wins():
    from app.api.search_engine.sources.foodb import _classify_origin

    # 3 plant vs 1 animal
    result = _classify_origin(["spinach", "kale", "broccoli", "beef"])
    assert result == "plant"


# ---------------------------------------------------------------------------
# foodb_enrich — successful classification
# ---------------------------------------------------------------------------

def test_foodb_enrich_plant_origin():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(200, _PLANT_COMPOUND_RESPONSE)):
        results = foodb_enrich("quercetin", {})

    assert len(results) == 1
    r = results[0]
    assert r["property"] == "source_origin"
    assert r["value"] == "plant"
    assert r["source_url"] == "https://foodb.ca/compounds/FDB012345"
    assert r["raw_excerpt"] is not None
    assert "plant" in r["raw_excerpt"]


def test_foodb_enrich_animal_origin():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(200, _ANIMAL_COMPOUND_RESPONSE)):
        results = foodb_enrich("taurine", {})

    assert len(results) == 1
    assert results[0]["value"] == "animal"
    assert results[0]["source_url"] == "https://foodb.ca/compounds/FDB099001"


def test_foodb_enrich_mineral_origin():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(200, _MINERAL_COMPOUND_RESPONSE)):
        results = foodb_enrich("magnesium stearate", {})

    assert len(results) == 1
    assert results[0]["value"] == "mineral"


def test_foodb_enrich_list_response_format():
    """Handler works when API returns a list directly (not wrapped in 'data')."""
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(200, _LIST_RESPONSE_PLANT)):
        results = foodb_enrich("chlorophyll", {})

    assert len(results) == 1
    assert results[0]["value"] == "plant"
    assert results[0]["source_url"] == "https://foodb.ca/compounds/FDB000777"


def test_foodb_enrich_source_url_falls_back_to_numeric_id():
    """If no public_id but numeric id present, URL uses numeric id."""
    from app.api.search_engine.sources.foodb import foodb_enrich

    response = {
        "data": [
            {
                "id": 42,
                "name": "Beta-carotene",
                "food_sources": [
                    {"name": "carrot vegetable"},
                    {"name": "spinach leaf"},
                ],
            }
        ]
    }

    with patch("httpx.get", return_value=_make_response(200, response)):
        results = foodb_enrich("beta-carotene", {})

    assert len(results) == 1
    assert results[0]["source_url"] == "https://foodb.ca/compounds/42"


def test_foodb_enrich_raw_excerpt_contains_food_names():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(200, _PLANT_COMPOUND_RESPONSE)):
        results = foodb_enrich("quercetin", {})

    excerpt = results[0]["raw_excerpt"]
    # Should mention at least one of the food source names
    assert any(
        food in excerpt for food in ["spinach", "kale", "broccoli", "apple", "onion"]
    )


# ---------------------------------------------------------------------------
# foodb_enrich — no results / not found
# ---------------------------------------------------------------------------

def test_foodb_enrich_empty_data_returns_empty():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(200, _EMPTY_RESPONSE)):
        results = foodb_enrich("nonexistent compound xyz", {})

    assert results == []


def test_foodb_enrich_404_returns_empty():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(404)):
        results = foodb_enrich("ghost compound", {})

    assert results == []


def test_foodb_enrich_no_classifiable_sources_returns_empty():
    """Compound found but food sources don't match any keyword category."""
    from app.api.search_engine.sources.foodb import foodb_enrich

    response = {
        "data": [
            {
                "id": 9999,
                "name": "Unknown stuff",
                "food_sources": [
                    {"name": "XYZ synthetic matrix"},
                ],
            }
        ]
    }

    with patch("httpx.get", return_value=_make_response(200, response)):
        results = foodb_enrich("unknown stuff", {})

    assert results == []


# ---------------------------------------------------------------------------
# foodb_enrich — API errors / unavailability
# ---------------------------------------------------------------------------

def test_foodb_enrich_request_error_returns_empty():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", side_effect=httpx.RequestError("Connection refused", request=MagicMock())):
        results = foodb_enrich("quercetin", {})

    assert results == []


def test_foodb_enrich_http_500_returns_empty():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", return_value=_make_response(500)):
        results = foodb_enrich("quercetin", {})

    assert results == []


def test_foodb_enrich_timeout_returns_empty():
    from app.api.search_engine.sources.foodb import foodb_enrich

    with patch("httpx.get", side_effect=httpx.TimeoutException("timeout", request=MagicMock())):
        results = foodb_enrich("quercetin", {})

    assert results == []


def test_foodb_enrich_malformed_json_returns_empty():
    """If the response body can't be parsed as JSON, return empty list."""
    from app.api.search_engine.sources.foodb import foodb_enrich

    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.side_effect = ValueError("No JSON object could be decoded")

    with patch("httpx.get", return_value=resp):
        results = foodb_enrich("quercetin", {})

    assert results == []


# ---------------------------------------------------------------------------
# foodb_enrich — FOODB_API_KEY env var is passed as header
# ---------------------------------------------------------------------------

def test_foodb_enrich_sends_api_key_when_env_set():
    from app.api.search_engine.sources.foodb import foodb_enrich

    captured_kwargs: dict = {}

    def fake_get(url, **kwargs):
        captured_kwargs.update(kwargs)
        return _make_response(200, _PLANT_COMPOUND_RESPONSE)

    with patch.dict("os.environ", {"FOODB_API_KEY": "test-secret"}):
        with patch("httpx.get", side_effect=fake_get):
            foodb_enrich("quercetin", {})

    headers = captured_kwargs.get("headers", {})
    assert headers.get("Authorization") == "Bearer test-secret"


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def test_foodb_handler_is_registered_in_handlers():
    from app.api.search_engine.handlers import SOURCE_HANDLERS

    assert "foodb" in SOURCE_HANDLERS
