"""Unit tests for web_search_enrich tool — mocks OpenAI and rag.store_embedding."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

CANNED_ALTERNATIVES = [
    {
        "normalized_name": "pea-protein-isolate",
        "properties": {
            "chemical_identity": {"value": {"synonyms": ["pea protein"]}, "confidence": "high"},
            "functional_role": {"value": ["protein source", "emulsifier"], "confidence": "high"},
            "source_origin": {"value": "plant-based", "confidence": "high"},
            "dietary_flags": {"value": {"vegan": True, "vegetarian": True, "halal": True, "kosher": False, "gluten_free": True}, "confidence": "high"},
            "allergens": {"value": {"contains": [], "free_from": ["dairy", "egg", "soy"]}, "confidence": "high"},
            "certifications": {"value": ["non-gmo"], "confidence": "medium"},
            "regulatory_status": {"value": {"gras": True, "eu_approved": True}, "confidence": "high"},
            "form_grade": {"value": {"form": "powder", "grade": "food"}, "confidence": "high"},
        },
    },
    {
        "normalized_name": "rice-protein-concentrate",
        "properties": {
            "chemical_identity": {"value": {"synonyms": ["brown rice protein"]}, "confidence": "high"},
            "functional_role": {"value": ["protein source"], "confidence": "high"},
            "source_origin": {"value": "plant-based", "confidence": "high"},
            "dietary_flags": {"value": {"vegan": True, "vegetarian": True, "halal": True, "kosher": True, "gluten_free": True}, "confidence": "high"},
            "allergens": {"value": {"contains": [], "free_from": ["dairy", "egg", "soy", "gluten"]}, "confidence": "high"},
            "certifications": {"value": ["organic", "non-gmo"], "confidence": "medium"},
            "regulatory_status": {"value": {"gras": True, "eu_approved": True}, "confidence": "high"},
            "form_grade": {"value": {"form": "powder", "grade": "food"}, "confidence": "high"},
        },
    },
]

CANNED_RESPONSE_TEXT = json.dumps({"alternatives": CANNED_ALTERNATIVES})


def _make_mock_response(text: str):
    """Build a mock OpenAI Responses API response with output_text."""
    mock = MagicMock()
    mock.output_text = text
    return mock


@pytest.mark.asyncio
async def test_discover_alternatives_returns_valid_dicts():
    """discover_alternatives should parse and validate canned LLM response."""
    mock_response = _make_mock_response(CANNED_RESPONSE_TEXT)

    with patch("app.services.web_search._openai") as mock_client:
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        from app.services.web_search import discover_alternatives
        results = await discover_alternatives("vegan collagen peptides", limit=2)

    assert len(results) == 2
    assert results[0]["normalized_name"] == "pea-protein-isolate"
    assert results[1]["normalized_name"] == "rice-protein-concentrate"
    # Verify nested properties structure is preserved
    assert results[0]["properties"]["functional_role"]["value"] == ["protein source", "emulsifier"]


@pytest.mark.asyncio
async def test_discover_alternatives_skips_empty_names():
    """Items with empty normalized_name should be silently dropped."""
    bad_response = json.dumps({
        "alternatives": [
            {"normalized_name": "", "properties": {}},
            {"normalized_name": "hemp-protein", "properties": {}},
        ]
    })
    mock_response = _make_mock_response(bad_response)

    with patch("app.services.web_search._openai") as mock_client:
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        from app.services.web_search import discover_alternatives
        results = await discover_alternatives("vegan collagen peptides", limit=5)

    assert len(results) == 1
    assert results[0]["normalized_name"] == "hemp-protein"


@pytest.mark.asyncio
async def test_web_search_enrich_calls_store_embedding_and_returns_names():
    """web_search_enrich should call rag.store_embedding once per candidate
    and return the list of normalized names."""
    mock_response = _make_mock_response(CANNED_RESPONSE_TEXT)

    with (
        patch("app.services.web_search._openai") as mock_client,
        patch("app.agents.tools.web_search_enrich.rag") as mock_rag,
    ):
        mock_client.responses.create = AsyncMock(return_value=mock_response)
        mock_rag.store_embedding = AsyncMock()

        from app.agents.tools.web_search_enrich import web_search_enrich
        added = await web_search_enrich("vegan collagen peptides", limit=2)

    assert added == ["pea-protein-isolate", "rice-protein-concentrate"]
    assert mock_rag.store_embedding.call_count == 2

    # Verify the first call was passed the full enriched dict
    first_call_arg = mock_rag.store_embedding.call_args_list[0][0][0]
    assert first_call_arg["normalized_name"] == "pea-protein-isolate"
    assert "properties" in first_call_arg


@pytest.mark.asyncio
async def test_web_search_enrich_continues_on_store_failure():
    """A store_embedding failure on one item should not abort the rest."""
    mock_response = _make_mock_response(CANNED_RESPONSE_TEXT)

    with (
        patch("app.services.web_search._openai") as mock_client,
        patch("app.agents.tools.web_search_enrich.rag") as mock_rag,
    ):
        mock_client.responses.create = AsyncMock(return_value=mock_response)
        # First call raises, second succeeds
        mock_rag.store_embedding = AsyncMock(side_effect=[Exception("DB error"), None])

        from app.agents.tools.web_search_enrich import web_search_enrich
        added = await web_search_enrich("vegan collagen peptides", limit=2)

    assert added == ["rice-protein-concentrate"]
    assert mock_rag.store_embedding.call_count == 2


@pytest.mark.asyncio
async def test_discover_alternatives_handles_empty_response():
    """An empty LLM response should return an empty list without raising."""
    mock_response = _make_mock_response("")

    with patch("app.services.web_search._openai") as mock_client:
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        from app.services.web_search import discover_alternatives
        results = await discover_alternatives("some ingredient", limit=5)

    assert results == []
