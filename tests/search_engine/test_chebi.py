"""Tests for ChEBI source handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# Fake API responses
# ---------------------------------------------------------------------------

# OLS4 search result for "magnesium stearate" — exact match, has roles
SEARCH_EXACT_RESPONSE = {
    "response": {
        "numFound": 1,
        "docs": [
            {
                "id": "http://purl.obolibrary.org/obo/CHEBI_9243",
                "iri": "http://purl.obolibrary.org/obo/CHEBI_9243",
                "short_form": "CHEBI_9243",
                "obo_id": "CHEBI:9243",
                "label": "magnesium stearate",
                "description": ["A magnesium salt of stearic acid."],
                "ontology_name": "chebi",
                "annotation": {
                    "has_role": [
                        "http://purl.obolibrary.org/obo/CHEBI_64909",  # lubricant
                        "http://purl.obolibrary.org/obo/CHEBI_64047",  # food additive
                        "http://purl.obolibrary.org/obo/CHEBI_64050",  # anti-caking agent
                    ]
                },
            }
        ],
    }
}

# Term detail responses for each role IRI
ROLE_LUBRICANT = {
    "_embedded": {
        "terms": [
            {
                "iri": "http://purl.obolibrary.org/obo/CHEBI_64909",
                "label": "lubricant",
            }
        ]
    }
}

ROLE_FOOD_ADDITIVE = {
    "_embedded": {
        "terms": [
            {
                "iri": "http://purl.obolibrary.org/obo/CHEBI_64047",
                "label": "food additive",
            }
        ]
    }
}

ROLE_ANTI_CAKING = {
    "_embedded": {
        "terms": [
            {
                "iri": "http://purl.obolibrary.org/obo/CHEBI_64050",
                "label": "anti-caking agent",
            }
        ]
    }
}

# Fuzzy search fallback response
SEARCH_FUZZY_RESPONSE = {
    "response": {
        "numFound": 1,
        "docs": [
            {
                "id": "http://purl.obolibrary.org/obo/CHEBI_9243",
                "iri": "http://purl.obolibrary.org/obo/CHEBI_9243",
                "short_form": "CHEBI_9243",
                "obo_id": "CHEBI:9243",
                "label": "magnesium stearate",
                "description": ["A magnesium salt of stearic acid."],
                "ontology_name": "chebi",
                "annotation": {
                    "has_role": [
                        "http://purl.obolibrary.org/obo/CHEBI_64909",
                    ]
                },
            }
        ],
    }
}

# Empty search result
SEARCH_EMPTY_RESPONSE = {
    "response": {
        "numFound": 0,
        "docs": [],
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


class TestChebiEnrich:
    """Test the chebi_enrich handler."""

    def _import(self):
        from app.agents.searchEngine.sources.chebi import chebi_enrich
        return chebi_enrich

    # --- successful role extraction ---

    def test_success_returns_functional_role(self):
        """Exact match with role IRIs returns a functional_role result."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_response(200, SEARCH_EXACT_RESPONSE),    # exact search
                _make_response(200, ROLE_LUBRICANT),           # resolve role IRI 1
                _make_response(200, ROLE_FOOD_ADDITIVE),       # resolve role IRI 2
                _make_response(200, ROLE_ANTI_CAKING),         # resolve role IRI 3
            ]
            results = chebi_enrich("magnesium stearate", {})

        assert len(results) == 1
        r = results[0]
        assert r["property"] == "functional_role"
        assert "lubricant" in r["value"]
        assert "food additive" in r["value"]
        assert "anti-caking agent" in r["value"]

    def test_success_source_url_contains_chebi_id(self):
        """source_url points to the ChEBI entry page."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_response(200, SEARCH_EXACT_RESPONSE),
                _make_response(200, ROLE_LUBRICANT),
                _make_response(200, ROLE_FOOD_ADDITIVE),
                _make_response(200, ROLE_ANTI_CAKING),
            ]
            results = chebi_enrich("magnesium stearate", {})

        assert results[0]["source_url"] == (
            "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:9243"
        )

    def test_value_is_a_list(self):
        """value is a list of role strings."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_response(200, SEARCH_EXACT_RESPONSE),
                _make_response(200, ROLE_LUBRICANT),
                _make_response(200, ROLE_FOOD_ADDITIVE),
                _make_response(200, ROLE_ANTI_CAKING),
            ]
            results = chebi_enrich("magnesium stearate", {})

        assert isinstance(results[0]["value"], list)

    # --- no annotation / no roles ---

    def test_doc_without_annotation_returns_empty_list(self):
        """If the matching doc has no has_role annotations, return empty list."""
        chebi_enrich = self._import()

        response_no_roles = {
            "response": {
                "numFound": 1,
                "docs": [
                    {
                        "id": "http://purl.obolibrary.org/obo/CHEBI_9243",
                        "iri": "http://purl.obolibrary.org/obo/CHEBI_9243",
                        "short_form": "CHEBI_9243",
                        "obo_id": "CHEBI:9243",
                        "label": "magnesium stearate",
                        "ontology_name": "chebi",
                        "annotation": {},  # no has_role key
                    }
                ],
            }
        }

        with patch("httpx.get") as mock_get:
            mock_get.return_value = _make_response(200, response_no_roles)
            results = chebi_enrich("magnesium stearate", {})

        assert results == []

    # --- not found ---

    def test_exact_and_fuzzy_both_empty_returns_empty_list(self):
        """When both exact and fuzzy searches return no docs, return []."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.return_value = _make_response(200, SEARCH_EMPTY_RESPONSE)
            results = chebi_enrich("completely unknown compound xyz", {})

        assert results == []

    def test_exact_empty_falls_back_to_fuzzy(self):
        """Exact search returns 0 docs → handler retries with fuzzy search."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_response(200, SEARCH_EMPTY_RESPONSE),  # exact → empty
                _make_response(200, SEARCH_FUZZY_RESPONSE),  # fuzzy → hit
                _make_response(200, ROLE_LUBRICANT),         # resolve role
            ]
            results = chebi_enrich("mag stearate", {})

        assert len(results) == 1
        assert "lubricant" in results[0]["value"]

    # --- API errors ---

    def test_http_status_error_returns_empty_list(self):
        """Non-200 response from search endpoint returns []."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.return_value = _make_response(500)
            results = chebi_enrich("magnesium stearate", {})

        assert results == []

    def test_network_error_returns_empty_list(self):
        """Network-level exception returns []."""
        chebi_enrich = self._import()

        with patch("httpx.get", side_effect=httpx.RequestError("timeout")):
            results = chebi_enrich("magnesium stearate", {})

        assert results == []

    def test_role_iri_resolution_failure_skips_role(self):
        """If a role IRI lookup fails, that role is omitted but others succeed."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_response(200, SEARCH_EXACT_RESPONSE),  # exact search
                _make_response(200, ROLE_LUBRICANT),          # role 1 OK
                _make_response(500),                          # role 2 fails
                _make_response(200, ROLE_ANTI_CAKING),        # role 3 OK
            ]
            results = chebi_enrich("magnesium stearate", {})

        # Should still return a result with the two roles that resolved
        assert len(results) == 1
        roles = results[0]["value"]
        assert "lubricant" in roles
        assert "anti-caking agent" in roles
        assert "food additive" not in roles

    def test_role_iri_all_resolutions_fail_returns_empty(self):
        """If all role IRI lookups fail, return []."""
        chebi_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_response(200, SEARCH_EXACT_RESPONSE),  # exact search
                _make_response(500),  # role 1 fails
                _make_response(500),  # role 2 fails
                _make_response(500),  # role 3 fails
            ]
            results = chebi_enrich("magnesium stearate", {})

        assert results == []

    # --- handler registry ---

    def test_handler_is_registered_in_source_handlers(self):
        """chebi_enrich is wired into SOURCE_HANDLERS and is the real impl."""
        from app.agents.searchEngine.handlers import SOURCE_HANDLERS
        from app.agents.searchEngine.sources.chebi import chebi_enrich as real_impl

        assert SOURCE_HANDLERS["chebi"] is real_impl

    def test_registered_handler_returns_functional_role(self):
        """The handler in SOURCE_HANDLERS returns functional_role results."""
        from app.agents.searchEngine.handlers import SOURCE_HANDLERS

        handler = SOURCE_HANDLERS["chebi"]

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_response(200, SEARCH_EXACT_RESPONSE),
                _make_response(200, ROLE_LUBRICANT),
                _make_response(200, ROLE_FOOD_ADDITIVE),
                _make_response(200, ROLE_ANTI_CAKING),
            ]
            results = handler("magnesium stearate", {})

        assert len(results) == 1
        assert results[0]["property"] == "functional_role"
