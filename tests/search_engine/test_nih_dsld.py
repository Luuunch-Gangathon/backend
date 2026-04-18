"""Tests for the NIH DSLD source handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(body: dict, status_code: int = 200) -> MagicMock:
    """Return a mock httpx.Response for a given JSON body."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _make_error_response(status_code: int = 500) -> MagicMock:
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_resp
    )
    return mock_resp


def _dsld_products_response(products: list[dict]) -> dict:
    """Simulate a DSLD API response with a list of products."""
    return {"hits": products, "total": len(products)}


def _dsld_product(label_claims: list[str], product_id: str = "prod_1") -> dict:
    """Minimal DSLD product dict."""
    return {
        "id": product_id,
        "productName": f"Product {product_id}",
        "labelClaims": label_claims,
    }


# ---------------------------------------------------------------------------
# _extract_flags — internal helper
# ---------------------------------------------------------------------------

class TestExtractFlags:
    def _import(self):
        from app.api.search_engine.sources.nih_dsld import _extract_flags
        return _extract_flags

    def test_detects_vegan_claim(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["This product is Vegan certified", "GMP facility"])
        assert dietary.get("vegan") is True

    def test_detects_vegetarian_claim(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["Suitable for Vegetarians"])
        assert dietary.get("vegetarian") is True

    def test_detects_gmp_cert(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["Manufactured in a GMP certified facility"])
        assert "GMP" in certs

    def test_detects_non_gmo_cert(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["Non-GMO verified"])
        assert "Non-GMO" in certs

    def test_detects_organic_cert(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["USDA Organic certified"])
        assert "Organic" in certs

    def test_detects_nsf_cert(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["NSF Certified for Sport"])
        assert "NSF Certified" in certs

    def test_empty_claims_returns_empty(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags([])
        assert dietary == {}
        assert certs == []

    def test_no_matching_claims_returns_empty(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["Contains 500mg of Vitamin C", "Take one daily"])
        assert dietary == {}
        assert certs == []

    def test_case_insensitive_matching(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["VEGAN FORMULA", "non-gmo project verified"])
        assert dietary.get("vegan") is True
        assert "Non-GMO" in certs

    def test_deduplicates_certs(self):
        _extract_flags = self._import()
        dietary, certs = _extract_flags(["GMP facility", "cGMP certified", "GMP standards"])
        assert certs.count("GMP") == 1


# ---------------------------------------------------------------------------
# _aggregate_products — internal helper
# ---------------------------------------------------------------------------

class TestAggregateProducts:
    def _import(self):
        from app.api.search_engine.sources.nih_dsld import _aggregate_products
        return _aggregate_products

    def test_aggregates_dietary_from_multiple_products(self):
        _aggregate_products = self._import()
        products = [
            _dsld_product(["Vegan certified"], "p1"),
            _dsld_product(["Vegetarian friendly"], "p2"),
        ]
        dietary, certs = _aggregate_products(products)
        assert dietary.get("vegan") is True
        assert dietary.get("vegetarian") is True

    def test_aggregates_certs_from_multiple_products(self):
        _aggregate_products = self._import()
        products = [
            _dsld_product(["GMP certified"], "p1"),
            _dsld_product(["Non-GMO verified"], "p2"),
        ]
        dietary, certs = _aggregate_products(products)
        assert "GMP" in certs
        assert "Non-GMO" in certs

    def test_empty_products_returns_empty(self):
        _aggregate_products = self._import()
        dietary, certs = _aggregate_products([])
        assert dietary == {}
        assert certs == []

    def test_skips_products_with_no_label_claims(self):
        _aggregate_products = self._import()
        products = [{"id": "p1", "productName": "No claims", "labelClaims": []}]
        dietary, certs = _aggregate_products(products)
        assert dietary == {}
        assert certs == []


# ---------------------------------------------------------------------------
# nih_dsld_enrich — success cases
# ---------------------------------------------------------------------------

class TestNihDsldEnrichSuccess:
    def _import(self):
        from app.api.search_engine.sources.nih_dsld import nih_dsld_enrich
        return nih_dsld_enrich

    def test_returns_dietary_flags_and_certifications(self):
        nih_dsld_enrich = self._import()
        products = [
            _dsld_product(["Vegan formula", "GMP certified"], "p1"),
            _dsld_product(["Non-GMO verified"], "p2"),
        ]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("vitamin c", {})

        property_names = [r["property"] for r in results]
        assert "dietary_flags" in property_names
        assert "certifications" in property_names

    def test_dietary_flags_structure(self):
        nih_dsld_enrich = self._import()
        products = [_dsld_product(["This supplement is Vegan"])]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("vitamin c", {})

        df = next(r for r in results if r["property"] == "dietary_flags")
        assert df["value"].get("vegan") is True
        assert df["source_url"] is not None
        assert "dsld" in df["source_url"].lower()

    def test_certifications_structure(self):
        nih_dsld_enrich = self._import()
        products = [_dsld_product(["GMP certified facility", "NSF Certified for Sport"])]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("zinc", {})

        cert = next(r for r in results if r["property"] == "certifications")
        assert "GMP" in cert["value"]
        assert "NSF Certified" in cert["value"]
        assert cert["source_url"] is not None

    def test_raw_excerpt_present(self):
        nih_dsld_enrich = self._import()
        products = [_dsld_product(["Vegan", "GMP"])]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("magnesium", {})

        for r in results:
            assert r["raw_excerpt"] is not None
            assert len(r["raw_excerpt"]) > 0

    def test_aggregates_across_products(self):
        """Vegan on product 1, GMP on product 2 — both appear in output."""
        nih_dsld_enrich = self._import()
        products = [
            _dsld_product(["Vegan formula"], "p1"),
            _dsld_product(["Certified GMP"], "p2"),
        ]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("omega-3", {})

        df = next(r for r in results if r["property"] == "dietary_flags")
        cert = next(r for r in results if r["property"] == "certifications")
        assert df["value"].get("vegan") is True
        assert "GMP" in cert["value"]


# ---------------------------------------------------------------------------
# nih_dsld_enrich — no results
# ---------------------------------------------------------------------------

class TestNihDsldEnrichNoResults:
    def _import(self):
        from app.api.search_engine.sources.nih_dsld import nih_dsld_enrich
        return nih_dsld_enrich

    def test_no_products_returns_empty(self):
        nih_dsld_enrich = self._import()
        mock_resp = _make_response(_dsld_products_response([]))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("xanthan gum", {})

        assert results == []

    def test_products_with_no_relevant_claims_returns_empty(self):
        nih_dsld_enrich = self._import()
        products = [
            _dsld_product(["Take 1 capsule daily", "500mg per serving"], "p1"),
        ]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("riboflavin", {})

        assert results == []

    def test_only_dietary_returns_one_entry(self):
        nih_dsld_enrich = self._import()
        products = [_dsld_product(["Suitable for Vegetarians"])]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("b12", {})

        property_names = [r["property"] for r in results]
        assert "dietary_flags" in property_names
        assert "certifications" not in property_names

    def test_only_certifications_returns_one_entry(self):
        nih_dsld_enrich = self._import()
        products = [_dsld_product(["NSF Certified for Sport"])]
        mock_resp = _make_response(_dsld_products_response(products))

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("creatine", {})

        property_names = [r["property"] for r in results]
        assert "certifications" in property_names
        assert "dietary_flags" not in property_names


# ---------------------------------------------------------------------------
# nih_dsld_enrich — API errors
# ---------------------------------------------------------------------------

class TestNihDsldEnrichErrors:
    def _import(self):
        from app.api.search_engine.sources.nih_dsld import nih_dsld_enrich
        return nih_dsld_enrich

    def test_network_error_returns_empty(self):
        nih_dsld_enrich = self._import()

        with patch("httpx.get", side_effect=httpx.RequestError("Connection refused", request=MagicMock())):
            results = nih_dsld_enrich("guar gum", {})

        assert results == []

    def test_http_500_returns_empty(self):
        nih_dsld_enrich = self._import()
        mock_resp = _make_error_response(500)

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("lecithin", {})

        assert results == []

    def test_unexpected_json_structure_returns_empty(self):
        nih_dsld_enrich = self._import()
        # API returns something unexpected
        mock_resp = _make_response({"unexpected_key": "unexpected_value"})

        with patch("httpx.get", return_value=mock_resp):
            results = nih_dsld_enrich("turmeric", {})

        assert results == []


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def test_handler_is_registered():
    from app.api.search_engine.handlers import SOURCE_HANDLERS

    assert "nih_dsld" in SOURCE_HANDLERS
    handler = SOURCE_HANDLERS["nih_dsld"]
    assert callable(handler)


def test_handler_delegates_to_real_impl():
    """The registered handler should delegate to the real implementation, not the stub."""
    from app.api.search_engine.handlers import SOURCE_HANDLERS

    handler = SOURCE_HANDLERS["nih_dsld"]
    products = [
        _dsld_product(["Vegan certified", "GMP facility"], "p1"),
    ]
    mock_resp = _make_response(_dsld_products_response(products))

    with patch("httpx.get", return_value=mock_resp):
        results = handler("vitamin c", {})

    # Real impl returns results; stub would return [].
    assert len(results) >= 1
    property_names = [r["property"] for r in results]
    assert "dietary_flags" in property_names
