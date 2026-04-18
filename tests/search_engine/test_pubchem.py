"""Tests for PubChem source handler."""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures — fake API responses
# ---------------------------------------------------------------------------

COMPOUND_JSON = {
    "PC_Compounds": [
        {
            "id": {"id": {"cid": 11177}},
            "props": [
                {
                    "urn": {"label": "Molecular Formula", "name": ""},
                    "value": {"sval": "C36H70MgO4"},
                },
                {
                    "urn": {"label": "Molecular Weight", "name": ""},
                    "value": {"fval": 591.3},
                },
                {
                    "urn": {"label": "IUPAC Name", "name": "Preferred"},
                    "value": {"sval": "magnesium;octadecanoate"},
                },
            ],
        }
    ]
}

SYNONYMS_JSON = {
    "InformationList": {
        "Information": [
            {
                "CID": 11177,
                "Synonym": [
                    "magnesium stearate",
                    "557-04-0",
                    "Magnesium distearate",
                    "Magnesium octadecanoate",
                ],
            }
        ]
    }
}


def _make_response(status_code: int, json_body: dict | None = None) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = Exception("no body")
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pubchem_enrich_success():
    """Successful lookup returns a single chemical_identity result with all fields."""
    from app.agents.searchEngine.sources.pubchem import pubchem_enrich

    with patch("httpx.get") as mock_get:
        mock_get.side_effect = [
            _make_response(200, COMPOUND_JSON),
            _make_response(200, SYNONYMS_JSON),
        ]
        results = pubchem_enrich("magnesium stearate", {})

    assert len(results) == 1
    r = results[0]
    assert r["property"] == "chemical_identity"
    assert r["source_url"] == "https://pubchem.ncbi.nlm.nih.gov/compound/11177"
    assert r["raw_excerpt"] == "PubChem CID 11177, MF: C36H70MgO4, MW: 591.3"

    v = r["value"]
    assert v["pubchem_cid"] == 11177
    assert v["formula"] == "C36H70MgO4"
    assert v["molecular_weight"] == 591.3
    assert v["iupac_name"] == "magnesium;octadecanoate"
    assert "magnesium stearate" in v["synonyms"]


def test_pubchem_enrich_cas_extraction():
    """CAS number is correctly extracted from the synonyms list."""
    from app.agents.searchEngine.sources.pubchem import pubchem_enrich

    with patch("httpx.get") as mock_get:
        mock_get.side_effect = [
            _make_response(200, COMPOUND_JSON),
            _make_response(200, SYNONYMS_JSON),
        ]
        results = pubchem_enrich("magnesium stearate", {})

    assert results[0]["value"]["cas_number"] == "557-04-0"


def test_pubchem_enrich_no_cas_in_synonyms():
    """When no CAS-pattern synonym exists cas_number is None."""
    from app.agents.searchEngine.sources.pubchem import pubchem_enrich

    synonyms_no_cas = {
        "InformationList": {
            "Information": [
                {
                    "CID": 11177,
                    "Synonym": ["magnesium stearate", "Magnesium distearate"],
                }
            ]
        }
    }

    with patch("httpx.get") as mock_get:
        mock_get.side_effect = [
            _make_response(200, COMPOUND_JSON),
            _make_response(200, synonyms_no_cas),
        ]
        results = pubchem_enrich("magnesium stearate", {})

    assert results[0]["value"]["cas_number"] is None


def test_pubchem_enrich_not_found_404():
    """404 from compound endpoint returns empty list."""
    from app.agents.searchEngine.sources.pubchem import pubchem_enrich

    with patch("httpx.get") as mock_get:
        mock_get.return_value = _make_response(404)
        results = pubchem_enrich("nonexistent compound xyz", {})

    assert results == []


def test_pubchem_enrich_api_error():
    """Network / unexpected error returns empty list and logs warning."""
    from app.agents.searchEngine.sources.pubchem import pubchem_enrich
    import httpx

    with patch("httpx.get", side_effect=httpx.RequestError("timeout")):
        results = pubchem_enrich("magnesium stearate", {})

    assert results == []


def test_pubchem_enrich_synonyms_404_still_returns_result():
    """If the synonyms endpoint 404s, handler still returns result with no CAS/synonyms."""
    from app.agents.searchEngine.sources.pubchem import pubchem_enrich

    with patch("httpx.get") as mock_get:
        mock_get.side_effect = [
            _make_response(200, COMPOUND_JSON),
            _make_response(404),
        ]
        results = pubchem_enrich("magnesium stearate", {})

    assert len(results) == 1
    v = results[0]["value"]
    assert v["cas_number"] is None
    assert v["synonyms"] == []
    assert v["pubchem_cid"] == 11177


def test_pubchem_enrich_is_registered_in_handlers():
    """The real pubchem_enrich function is wired into SOURCE_HANDLERS."""
    from app.agents.searchEngine.handlers import SOURCE_HANDLERS
    from app.agents.searchEngine.sources.pubchem import pubchem_enrich as real_impl

    assert SOURCE_HANDLERS["pubchem"] is real_impl
