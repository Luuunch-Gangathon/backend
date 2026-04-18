"""Tests for search utilities — DuckDuckGo wrapper + domain cache."""

from __future__ import annotations

from unittest.mock import patch, MagicMock


def test_search_returns_list_of_results():
    from app.api.search_engine.sources.search_utils import search

    mock_ddg = MagicMock()
    mock_ddg.return_value = [
        {"title": "PureBulk", "href": "https://purebulk.com", "body": "Supplements"},
        {"title": "PureBulk About", "href": "https://purebulk.com/about", "body": "About us"},
    ]

    with patch("app.api.search_engine.sources.search_utils.DDGS") as MockDDGS:
        MockDDGS.return_value.__enter__ = MagicMock(return_value=MagicMock(text=mock_ddg))
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)
        results = search("PureBulk official website", max_results=3)

    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["url"] == "https://purebulk.com"
    assert results[0]["title"] == "PureBulk"
    assert results[0]["snippet"] == "Supplements"


def test_search_returns_empty_on_exception():
    from app.api.search_engine.sources.search_utils import search

    with patch("app.api.search_engine.sources.search_utils.DDGS") as MockDDGS:
        MockDDGS.return_value.__enter__ = MagicMock(
            return_value=MagicMock(text=MagicMock(side_effect=Exception("rate limited")))
        )
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)
        results = search("anything")

    assert results == []


def test_extract_domain():
    from app.api.search_engine.sources.search_utils import extract_domain

    assert extract_domain("https://www.purebulk.com/products/magnesium") == "purebulk.com"
    assert extract_domain("https://prinovaglobal.com/ingredients") == "prinovaglobal.com"
    assert extract_domain("https://sub.domain.example.co.uk/page") == "domain.example.co.uk"


def test_get_supplier_domain_searches_and_caches():
    from app.api.search_engine.sources import search_utils
    from app.api.search_engine.sources.search_utils import get_supplier_domain

    search_utils._domain_cache.clear()

    fake_results = [
        {"title": "PureBulk", "url": "https://purebulk.com/about", "snippet": "..."},
    ]

    with patch("app.api.search_engine.sources.search_utils.search", return_value=fake_results):
        domain = get_supplier_domain("PureBulk")

    assert domain == "purebulk.com"

    with patch("app.api.search_engine.sources.search_utils.search", side_effect=Exception("should not be called")):
        domain2 = get_supplier_domain("PureBulk")

    assert domain2 == "purebulk.com"


def test_get_supplier_domain_returns_none_on_no_results():
    from app.api.search_engine.sources import search_utils
    from app.api.search_engine.sources.search_utils import get_supplier_domain

    search_utils._domain_cache.clear()

    with patch("app.api.search_engine.sources.search_utils.search", return_value=[]):
        domain = get_supplier_domain("NonexistentSupplier")

    assert domain is None


def test_find_product_page():
    from app.api.search_engine.sources.search_utils import find_product_page

    fake_results = [
        {"title": "Magnesium Stearate - PureBulk", "url": "https://purebulk.com/products/magnesium-stearate", "snippet": "..."},
    ]

    with patch("app.api.search_engine.sources.search_utils.search", return_value=fake_results):
        url = find_product_page("magnesium stearate", "purebulk.com")

    assert url == "https://purebulk.com/products/magnesium-stearate"


def test_find_product_page_returns_none_on_no_results():
    from app.api.search_engine.sources.search_utils import find_product_page

    with patch("app.api.search_engine.sources.search_utils.search", return_value=[]):
        url = find_product_page("unknown material", "purebulk.com")

    assert url is None
