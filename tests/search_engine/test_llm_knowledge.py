"""Tests for the llm_knowledge source handler."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(content_text: str, input_tokens: int = 100, output_tokens: int = 80):
    """Build a fake Anthropic response object."""
    response = MagicMock()
    response.content = [MagicMock(text=content_text)]
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


def _valid_llm_json(**overrides) -> str:
    """Return a JSON string resembling a valid LLM response."""
    data = {
        "functional_role": ["lubricant", "flow agent"],
        "source_origin": "plant",
        "dietary_flags": {"vegan": True, "vegetarian": True, "halal": True, "kosher": True},
        "allergens": {"contains": [], "free_from": ["soy", "gluten"]},
        "certifications": ["Non-GMO"],
        "regulatory_status": {"gras": True},
        "form_grade": {"form": "powder", "grade": "pharmaceutical"},
        "price": None,
    }
    data.update(overrides)
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_successful_extraction_returns_properties():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    fake_resp = _make_response(_valid_llm_json())

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("magnesium stearate", {})

    property_names = {r["property"] for r in results}
    assert "functional_role" in property_names
    assert "source_origin" in property_names
    assert "dietary_flags" in property_names
    assert "allergens" in property_names
    assert "certifications" in property_names
    assert "regulatory_status" in property_names
    assert "form_grade" in property_names


def test_source_url_is_always_none():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    fake_resp = _make_response(_valid_llm_json())

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("magnesium stearate", {})

    assert len(results) > 0
    for r in results:
        assert r["source_url"] is None


def test_raw_excerpt_is_always_llm_knowledge_string():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    fake_resp = _make_response(_valid_llm_json())

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("magnesium stearate", {})

    assert len(results) > 0
    for r in results:
        assert r["raw_excerpt"] == "LLM knowledge (no external source)"


# ---------------------------------------------------------------------------
# Price is always excluded
# ---------------------------------------------------------------------------

def test_price_is_excluded_even_if_llm_returns_it():
    """price should never appear in results even when LLM mistakenly provides it."""
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    payload = _valid_llm_json(price="$25/kg")
    fake_resp = _make_response(payload)

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("magnesium stearate", {})

    property_names = {r["property"] for r in results}
    assert "price" not in property_names


def test_price_null_produces_no_entry():
    """When price is null the key should not appear in results at all."""
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    fake_resp = _make_response(_valid_llm_json(price=None))

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("magnesium stearate", {})

    property_names = {r["property"] for r in results}
    assert "price" not in property_names


# ---------------------------------------------------------------------------
# No API key
# ---------------------------------------------------------------------------

def test_no_api_key_returns_empty_list():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    with patch.dict("os.environ", {}, clear=True):
        # ensure key is absent
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        results = llm_knowledge_enrich("gelatin", {})

    assert results == []


# ---------------------------------------------------------------------------
# LLM error
# ---------------------------------------------------------------------------

def test_llm_error_returns_empty_list():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = RuntimeError("API failure")
        results = llm_knowledge_enrich("gelatin", {})

    assert results == []


# ---------------------------------------------------------------------------
# JSON in code blocks
# ---------------------------------------------------------------------------

def test_json_parsing_handles_json_code_blocks():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    body = _valid_llm_json(
        functional_role=["gelling agent"],
        source_origin="animal",
    )
    wrapped = f"```json\n{body}\n```"
    fake_resp = _make_response(wrapped)

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("gelatin", {})

    property_names = {r["property"] for r in results}
    assert "source_origin" in property_names

    origin = next(r for r in results if r["property"] == "source_origin")
    assert origin["value"] == "animal"


def test_json_parsing_handles_plain_code_blocks():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    body = _valid_llm_json(source_origin="synthetic")
    wrapped = f"```\n{body}\n```"
    fake_resp = _make_response(wrapped)

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("titanium dioxide", {})

    origin = next((r for r in results if r["property"] == "source_origin"), None)
    assert origin is not None
    assert origin["value"] == "synthetic"


# ---------------------------------------------------------------------------
# Partial / null properties
# ---------------------------------------------------------------------------

def test_null_properties_are_omitted():
    """Only non-null properties should appear in results."""
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    sparse = json.dumps({
        "chemical_identity": None,
        "functional_role": None,
        "source_origin": "mineral",
        "dietary_flags": None,
        "allergens": None,
        "certifications": None,
        "regulatory_status": None,
        "form_grade": None,
        "price": None,
    })
    fake_resp = _make_response(sparse)

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        MockClient.return_value.messages.create.return_value = fake_resp
        results = llm_knowledge_enrich("calcium carbonate", {})

    assert len(results) == 1
    assert results[0]["property"] == "source_origin"
    assert results[0]["value"] == "mineral"


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

def test_track_usage_is_called():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    fake_resp = _make_response(_valid_llm_json())

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage") as mock_track:
        MockClient.return_value.messages.create.return_value = fake_resp
        llm_knowledge_enrich("magnesium stearate", {})

    mock_track.assert_called_once()
    _resp_arg, model_arg, purpose_arg = mock_track.call_args[0]
    assert model_arg == "claude-haiku-4-5-20251001"
    assert purpose_arg == "llm_knowledge"


def test_correct_model_is_used():
    from app.agents.searchEngine.sources.llm_knowledge import llm_knowledge_enrich

    fake_resp = _make_response(_valid_llm_json())

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch("app.agents.searchEngine.sources.llm_knowledge.anthropic.Anthropic") as MockClient, \
         patch("app.agents.searchEngine.sources.llm_knowledge.track_usage"):
        mock_create = MockClient.return_value.messages.create
        mock_create.return_value = fake_resp
        llm_knowledge_enrich("magnesium stearate", {})

    call_kwargs = mock_create.call_args[1] if mock_create.call_args[1] else {}
    call_args = mock_create.call_args[0] if mock_create.call_args[0] else {}
    # model can be positional or keyword
    model_used = call_kwargs.get("model") or call_args[0] if call_args else call_kwargs.get("model")
    assert model_used == "claude-haiku-4-5-20251001"
