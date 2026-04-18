"""Tests for the web_search enrichment handler."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

# Module-level patch paths (all symbols imported at web_search module scope)
_MOD = "app.api.search_engine.sources.web_search"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_anthropic_response(json_payload: dict) -> MagicMock:
    """Build a fake Anthropic response object."""
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps(json_payload))]
    response.usage = MagicMock(input_tokens=100, output_tokens=50)
    return response


def _search_result(url: str) -> dict:
    return {"title": "Some page", "url": url, "snippet": "A relevant snippet."}


# ---------------------------------------------------------------------------
# Successful extraction
# ---------------------------------------------------------------------------

def test_successful_extraction_returns_properties():
    from app.api.search_engine.sources.web_search import web_search_enrich

    extracted = {
        "allergens": {"contains": [], "free_from": ["gluten"]},
        "source_origin": "plant",
        "certifications": ["Non-GMO", "Organic"],
    }

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example-ingredients.com/magnesium-stearate")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example-ingredients.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value="# Magnesium Stearate\nVegan certified, Non-GMO, gluten free.",
                                 ), patch(f"{_MOD}._extract_properties_from_page",
                                          return_value=extracted,
                                          ):
        results = web_search_enrich("magnesium stearate", {})

    assert len(results) == 3
    props = {r["property"] for r in results}
    assert props == {"allergens", "source_origin", "certifications"}

    # Verify result structure
    allergens_result = next(r for r in results if r["property"] == "allergens")
    assert allergens_result["value"] == {"contains": [], "free_from": ["gluten"]}
    assert allergens_result["source_url"] == "https://example-ingredients.com/magnesium-stearate"
    assert allergens_result["raw_excerpt"] is not None


def test_result_has_all_required_keys():
    from app.api.search_engine.sources.web_search import web_search_enrich

    extracted = {"price": "$25/kg"}

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://chemco.com/products/stearate")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="chemco.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value="Price: $25/kg for 25kg bag.",
                                 ), patch(f"{_MOD}._extract_properties_from_page",
                                          return_value=extracted,
                                          ):
        results = web_search_enrich("magnesium stearate", {})

    assert len(results) == 1
    r = results[0]
    assert "property" in r
    assert "value" in r
    assert "source_url" in r
    assert "raw_excerpt" in r


# ---------------------------------------------------------------------------
# Empty / failure paths
# ---------------------------------------------------------------------------

def test_no_search_results_returns_empty():
    from app.api.search_engine.sources.web_search import web_search_enrich

    with patch(f"{_MOD}.search", return_value=[]):
        results = web_search_enrich("magnesium stearate", {})

    assert results == []


def test_crawl_failure_returns_empty():
    from app.api.search_engine.sources.web_search import web_search_enrich

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example-ingredients.com/product")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example-ingredients.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value=None,  # crawl returned nothing
                                 ):
        results = web_search_enrich("magnesium stearate", {})

    assert results == []


def test_crawl_raises_exception_returns_empty():
    from app.api.search_engine.sources.web_search import web_search_enrich

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example-ingredients.com/product")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example-ingredients.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 side_effect=RuntimeError("network error"),
                                 ):
        results = web_search_enrich("magnesium stearate", {})

    assert results == []


def test_llm_returns_no_useful_properties_returns_empty():
    from app.api.search_engine.sources.web_search import web_search_enrich

    # All extracted values are null/None — handler should return nothing
    extracted = {
        "chemical_identity": None,
        "allergens": None,
        "source_origin": None,
    }

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example-ingredients.com/product")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example-ingredients.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value="Some page content without relevant properties.",
                                 ), patch(f"{_MOD}._extract_properties_from_page",
                                          return_value=extracted,
                                          ):
        results = web_search_enrich("magnesium stearate", {})

    assert results == []


def test_llm_extraction_returns_none_returns_empty():
    from app.api.search_engine.sources.web_search import web_search_enrich

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example-ingredients.com/product")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example-ingredients.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value="Some page content.",
                                 ), patch(f"{_MOD}._extract_properties_from_page",
                                          return_value=None,
                                          ):
        results = web_search_enrich("magnesium stearate", {})

    assert results == []


# ---------------------------------------------------------------------------
# Blocklist
# ---------------------------------------------------------------------------

def test_blocklisted_domain_is_skipped():
    from app.api.search_engine.sources.web_search import web_search_enrich

    # All results are blocklisted; handler should return empty
    search_results = [
        _search_result("https://wikipedia.org/wiki/Magnesium_stearate"),
        _search_result("https://reddit.com/r/chemistry/post"),
        _search_result("https://youtube.com/watch?v=abc"),
    ]

    with patch(f"{_MOD}.search",
               return_value=search_results,
               ), patch(f"{_MOD}.extract_domain",
                        side_effect=["wikipedia.org", "reddit.com", "youtube.com"],
                        ):
        results = web_search_enrich("magnesium stearate", {})

    assert results == []


def test_blocklisted_domain_skipped_uses_next_result():
    """When the first result is blocklisted, the handler moves to the next."""
    from app.api.search_engine.sources.web_search import web_search_enrich

    search_results = [
        _search_result("https://wikipedia.org/wiki/Magnesium_stearate"),
        _search_result("https://purechem.com/products/magnesium-stearate"),
    ]

    extracted = {"source_origin": "plant"}

    with patch(f"{_MOD}.search",
               return_value=search_results,
               ), patch(f"{_MOD}.extract_domain",
                        side_effect=["wikipedia.org", "purechem.com"],
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value="Magnesium stearate is derived from plant sources.",
                                 ), patch(f"{_MOD}._extract_properties_from_page",
                                          return_value=extracted,
                                          ):
        results = web_search_enrich("magnesium stearate", {})

    assert len(results) == 1
    assert results[0]["property"] == "source_origin"
    assert results[0]["source_url"] == "https://purechem.com/products/magnesium-stearate"


# ---------------------------------------------------------------------------
# No API key
# ---------------------------------------------------------------------------

def test_no_api_key_returns_none(monkeypatch):
    from app.api.search_engine.sources.web_search import _extract_properties_from_page

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = _extract_properties_from_page("page content about magnesium stearate", "magnesium stearate")
    assert result is None


def test_web_search_enrich_no_api_key_returns_empty(monkeypatch):
    from app.api.search_engine.sources.web_search import web_search_enrich

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example-ingredients.com/product")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example-ingredients.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value="Some useful page content about the material.",
                                 ):
        results = web_search_enrich("magnesium stearate", {})

    assert results == []


# ---------------------------------------------------------------------------
# Raw excerpt length
# ---------------------------------------------------------------------------

def test_raw_excerpt_is_max_200_chars():
    from app.api.search_engine.sources.web_search import web_search_enrich

    long_markdown = "A" * 500
    extracted = {"source_origin": "plant"}

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example.com/product")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value=long_markdown,
                                 ), patch(f"{_MOD}._extract_properties_from_page",
                                          return_value=extracted,
                                          ):
        results = web_search_enrich("magnesium stearate", {})

    assert len(results) == 1
    assert len(results[0]["raw_excerpt"]) == 200


# ---------------------------------------------------------------------------
# _extract_properties_from_page unit tests (with mock Anthropic)
# ---------------------------------------------------------------------------

def test_extract_properties_parses_json():
    from app.api.search_engine.sources.web_search import _extract_properties_from_page

    payload = {
        "source_origin": "plant",
        "certifications": ["Non-GMO"],
        "allergens": None,
    }
    mock_response = _make_anthropic_response(payload)

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}), \
         patch(f"{_MOD}.anthropic.Anthropic") as MockClient, \
         patch(f"{_MOD}.track_usage"):
        mock_client_instance = MockClient.return_value
        mock_client_instance.messages.create.return_value = mock_response

        result = _extract_properties_from_page("some page content", "magnesium stearate")

    assert result is not None
    assert result["source_origin"] == "plant"
    assert result["certifications"] == ["Non-GMO"]
    assert result["allergens"] is None


def test_extract_properties_handles_markdown_code_fence():
    from app.api.search_engine.sources.web_search import _extract_properties_from_page

    payload = {"price": "$30/kg"}
    raw_text = "```json\n" + json.dumps(payload) + "\n```"

    response = MagicMock()
    response.content = [MagicMock(text=raw_text)]
    response.usage = MagicMock(input_tokens=80, output_tokens=20)

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}), \
         patch(f"{_MOD}.anthropic.Anthropic") as MockClient, \
         patch(f"{_MOD}.track_usage"):
        mock_client_instance = MockClient.return_value
        mock_client_instance.messages.create.return_value = response

        result = _extract_properties_from_page("price info page", "magnesium stearate")

    assert result is not None
    assert result["price"] == "$30/kg"


def test_extract_properties_returns_none_on_invalid_json():
    from app.api.search_engine.sources.web_search import _extract_properties_from_page

    response = MagicMock()
    response.content = [MagicMock(text="not valid json at all!!!")]
    response.usage = MagicMock(input_tokens=50, output_tokens=10)

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}), \
         patch(f"{_MOD}.anthropic.Anthropic") as MockClient, \
         patch(f"{_MOD}.track_usage"):
        mock_client_instance = MockClient.return_value
        mock_client_instance.messages.create.return_value = response

        result = _extract_properties_from_page("some page content", "magnesium stearate")

    assert result is None


def test_extract_properties_returns_none_on_api_error():
    from app.api.search_engine.sources.web_search import _extract_properties_from_page

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}), \
         patch(f"{_MOD}.anthropic.Anthropic") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.messages.create.side_effect = Exception("API error")

        result = _extract_properties_from_page("some page content", "magnesium stearate")

    assert result is None


# ---------------------------------------------------------------------------
# Only known properties are included in results
# ---------------------------------------------------------------------------

def test_only_known_properties_returned():
    """LLM may return extra keys; only the 9 known property fields should appear."""
    from app.api.search_engine.sources.web_search import web_search_enrich

    extracted = {
        "source_origin": "plant",
        "unknown_field": "should be ignored",
        "another_extra": 42,
    }

    with patch(f"{_MOD}.search",
               return_value=[_search_result("https://example.com/product")],
               ), patch(f"{_MOD}.extract_domain",
                        return_value="example.com",
                        ), patch(f"{_MOD}.asyncio.run",
                                 return_value="Page about plant-based magnesium stearate.",
                                 ), patch(f"{_MOD}._extract_properties_from_page",
                                          return_value=extracted,
                                          ):
        results = web_search_enrich("magnesium stearate", {})

    props = [r["property"] for r in results]
    assert "source_origin" in props
    assert "unknown_field" not in props
    assert "another_extra" not in props
