"""Tests for openFDA source handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_enforcement_response(recalls: list[dict]) -> MagicMock:
    """Build a mock httpx.Response for the enforcement endpoint."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "results": recalls,
        "meta": {"results": {"total": len(recalls)}},
    }
    return resp


def _make_event_response(event_count: int) -> MagicMock:
    """Build a mock httpx.Response for the adverse events endpoint."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "results": [{}] * event_count,
        "meta": {"results": {"total": event_count}},
    }
    return resp


def _make_404_response() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 404
    resp.json.return_value = {"error": {"code": "NOT_FOUND"}}
    return resp


def _make_error_response(status_code: int = 500) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"error": {"message": "Internal server error"}}
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOpenfdaEnrich:
    """Test the openfda_enrich handler."""

    def _import(self):
        from app.api.search_engine.sources.openfda import openfda_enrich
        return openfda_enrich

    # --- recalls found ---

    def test_recalls_found_returns_regulatory_status(self):
        openfda_enrich = self._import()

        recall_data = [
            {
                "reason_for_recall": "Undeclared peanuts",
                "classification": "Class II",
                "recall_initiation_date": "20230115",
            },
            {
                "reason_for_recall": "Potential contamination",
                "classification": "Class I",
                "recall_initiation_date": "20221001",
            },
        ]

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_enforcement_response(recall_data),
                _make_404_response(),  # no adverse events
            ]
            results = openfda_enrich("peanuts", {})

        assert len(results) == 1
        item = results[0]
        assert item["property"] == "regulatory_status"
        assert item["source_url"] == "https://api.fda.gov/food/enforcement.json"
        assert item["raw_excerpt"] is not None

        value = item["value"]
        assert value["has_recalls"] is True
        assert value["has_adverse_events"] is False
        assert value["adverse_events_count"] == 0
        assert len(value["recalls"]) == 2

        first_recall = value["recalls"][0]
        assert first_recall["reason"] == "Undeclared peanuts"
        assert first_recall["classification"] == "Class II"
        assert first_recall["date"] == "2023-01-15"

    # --- adverse events found ---

    def test_adverse_events_found(self):
        openfda_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_404_response(),        # no recalls
                _make_event_response(3),     # 3 adverse events
            ]
            results = openfda_enrich("soy lecithin", {})

        assert len(results) == 1
        value = results[0]["value"]
        assert value["has_recalls"] is False
        assert value["has_adverse_events"] is True
        assert value["adverse_events_count"] == 3
        assert value["recalls"] == []

    # --- both recalls and adverse events ---

    def test_recalls_and_adverse_events(self):
        openfda_enrich = self._import()

        recall_data = [
            {
                "reason_for_recall": "Mislabeling",
                "classification": "Class III",
                "recall_initiation_date": "20240301",
            }
        ]

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_enforcement_response(recall_data),
                _make_event_response(5),
            ]
            results = openfda_enrich("sunflower oil", {})

        assert len(results) == 1
        value = results[0]["value"]
        assert value["has_recalls"] is True
        assert value["has_adverse_events"] is True
        assert value["adverse_events_count"] == 5
        assert len(value["recalls"]) == 1

        raw = results[0]["raw_excerpt"]
        assert "1" in raw   # "1 recall"
        assert "5" in raw   # "5 adverse event"

    # --- clean record (both 404) ---

    def test_clean_record_both_404(self):
        openfda_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_404_response(),
                _make_404_response(),
            ]
            results = openfda_enrich("water", {})

        assert len(results) == 1
        item = results[0]
        assert item["property"] == "regulatory_status"
        value = item["value"]
        assert value["recalls"] == []
        assert value["adverse_events_count"] == 0
        assert value["has_recalls"] is False
        assert value["has_adverse_events"] is False
        assert item["raw_excerpt"] == "No recalls or adverse events found"

    # --- API errors ---

    def test_enforcement_api_error_returns_empty(self):
        openfda_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            results = openfda_enrich("salt", {})

        assert results == []

    def test_one_endpoint_error_other_succeeds(self):
        """If enforcement fails but events succeed, we still get a result."""
        openfda_enrich = self._import()

        def side_effect(url, **kwargs):
            if "enforcement" in url:
                raise Exception("Timeout")
            return _make_event_response(2)

        with patch("httpx.get", side_effect=side_effect):
            results = openfda_enrich("citric acid", {})

        assert len(results) == 1
        value = results[0]["value"]
        assert value["adverse_events_count"] == 2
        assert value["has_adverse_events"] is True
        # recalls part should be empty (endpoint failed)
        assert value["recalls"] == []
        assert value["has_recalls"] is False

    def test_enforcement_500_returns_partial(self):
        """Non-404 error response from enforcement — treat as failed, still return result."""
        openfda_enrich = self._import()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_error_response(500),
                _make_event_response(1),
            ]
            results = openfda_enrich("maltodextrin", {})

        # Should still return a result based on the event data
        assert len(results) == 1
        value = results[0]["value"]
        assert value["has_adverse_events"] is True
        assert value["recalls"] == []

    # --- date formatting ---

    def test_date_formatted_as_iso(self):
        """recall_initiation_date YYYYMMDD → YYYY-MM-DD."""
        openfda_enrich = self._import()

        recall_data = [
            {
                "reason_for_recall": "Test",
                "classification": "Class II",
                "recall_initiation_date": "20191231",
            }
        ]

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_enforcement_response(recall_data),
                _make_404_response(),
            ]
            results = openfda_enrich("test ingredient", {})

        recall = results[0]["value"]["recalls"][0]
        assert recall["date"] == "2019-12-31"

    def test_missing_date_handled_gracefully(self):
        """recall_initiation_date absent — date should be None."""
        openfda_enrich = self._import()

        recall_data = [{"reason_for_recall": "No date", "classification": "Class I"}]

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_enforcement_response(recall_data),
                _make_404_response(),
            ]
            results = openfda_enrich("test ingredient", {})

        recall = results[0]["value"]["recalls"][0]
        assert recall["date"] is None

    # --- handler is reachable from handlers registry ---

    def test_handler_is_registered(self):
        from app.api.search_engine.handlers import SOURCE_HANDLERS

        assert "openfda" in SOURCE_HANDLERS
        handler = SOURCE_HANDLERS["openfda"]
        assert callable(handler)

        # Verify it delegates to the real implementation (not a stub returning []).
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [
                _make_404_response(),
                _make_404_response(),
            ]
            results = handler("water", {})

        # Real impl returns a clean-record result; stub would return [].
        assert len(results) == 1
        assert results[0]["property"] == "regulatory_status"
