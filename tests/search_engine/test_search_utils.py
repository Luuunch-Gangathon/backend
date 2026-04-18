"""Tests for search utilities — DuckDuckGo wrapper + LLM-verified domain discovery."""

from __future__ import annotations

from unittest.mock import patch, MagicMock


def test_search_returns_list_of_results():
    from app.agents.searchEngine.sources.search_utils import search

    mock_ddg = MagicMock()
    mock_ddg.return_value = [
        {"title": "PureBulk", "href": "https://purebulk.com", "body": "Supplements"},
        {"title": "PureBulk About", "href": "https://purebulk.com/about", "body": "About us"},
    ]

    with patch("app.agents.searchEngine.sources.search_utils.DDGS") as MockDDGS:
        MockDDGS.return_value.__enter__ = MagicMock(return_value=MagicMock(text=mock_ddg))
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)
        results = search("PureBulk official website", max_results=3)

    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["url"] == "https://purebulk.com"


def test_search_returns_empty_on_exception():
    from app.agents.searchEngine.sources.search_utils import search

    with patch("app.agents.searchEngine.sources.search_utils.DDGS") as MockDDGS:
        MockDDGS.return_value.__enter__ = MagicMock(
            return_value=MagicMock(text=MagicMock(side_effect=Exception("rate limited")))
        )
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)
        results = search("anything")

    assert results == []


def test_extract_domain():
    from app.agents.searchEngine.sources.search_utils import extract_domain

    assert extract_domain("https://www.purebulk.com/products/magnesium") == "purebulk.com"
    assert extract_domain("https://prinovaglobal.com/ingredients") == "prinovaglobal.com"
    assert extract_domain("https://ashland.com") == "ashland.com"


def test_name_to_slug():
    from app.agents.searchEngine.sources.search_utils import _name_to_slug

    assert _name_to_slug("PureBulk") == "purebulk"
    assert _name_to_slug("Jost Chemical") == "jostchemical"
    assert _name_to_slug("Prinova USA") == "prinova"
    assert _name_to_slug("Gold Coast Ingredients") == "goldcoastingredients"
    assert _name_to_slug("Darling Ingredients / Rousselot") == "darlingingredients"
    assert _name_to_slug("Magtein / ThreoTech LLC") == "magtein"


def test_generate_candidate_domains():
    from app.agents.searchEngine.sources.search_utils import _generate_candidate_domains

    candidates = _generate_candidate_domains("PureBulk")
    assert "purebulk.com" in candidates
    assert "purebulk.net" in candidates
    assert "purebulk.org" in candidates
    assert "purebulkglobal.com" in candidates

    candidates = _generate_candidate_domains("Prinova USA")
    assert "prinova.com" in candidates
    assert "prinovaglobal.com" in candidates


def test_get_supplier_domain_direct_hit():
    """Direct URL construction succeeds — no search needed."""
    from app.agents.searchEngine.sources import search_utils
    from app.agents.searchEngine.sources.search_utils import get_supplier_domain

    search_utils._domain_cache.clear()

    with patch(
        "app.agents.searchEngine.sources.search_utils._try_direct_domains",
        return_value="purebulk.com",
    ):
        domain = get_supplier_domain("PureBulk")

    assert domain == "purebulk.com"

    # Second call uses cache
    with patch(
        "app.agents.searchEngine.sources.search_utils._try_direct_domains",
        side_effect=Exception("should not be called"),
    ):
        domain2 = get_supplier_domain("PureBulk")

    assert domain2 == "purebulk.com"


def test_get_supplier_domain_falls_back_to_search():
    """Direct fails, search succeeds."""
    from app.agents.searchEngine.sources import search_utils
    from app.agents.searchEngine.sources.search_utils import get_supplier_domain

    search_utils._domain_cache.clear()

    with patch(
        "app.agents.searchEngine.sources.search_utils._try_direct_domains",
        return_value=None,
    ), patch(
        "app.agents.searchEngine.sources.search_utils._try_search_domain",
        return_value="ashland.com",
    ):
        domain = get_supplier_domain("Ashland")

    assert domain == "ashland.com"


def test_get_supplier_domain_returns_none_when_both_fail():
    """Both direct and search fail."""
    from app.agents.searchEngine.sources import search_utils
    from app.agents.searchEngine.sources.search_utils import get_supplier_domain

    search_utils._domain_cache.clear()

    with patch(
        "app.agents.searchEngine.sources.search_utils._try_direct_domains",
        return_value=None,
    ), patch(
        "app.agents.searchEngine.sources.search_utils._try_search_domain",
        return_value=None,
    ):
        domain = get_supplier_domain("TotallyFakeSupplier")

    assert domain is None


def test_try_search_domain_skips_blocklisted():
    """Search results from wikipedia/linkedin are skipped."""
    from app.agents.searchEngine.sources.search_utils import _try_search_domain

    fake_results = [
        {"title": "Ashland - Wikipedia", "url": "https://en.wikipedia.org/wiki/Ashland", "snippet": "..."},
        {"title": "Ashland | LinkedIn", "url": "https://www.linkedin.com/company/ashland", "snippet": "..."},
        {"title": "Ashland Global", "url": "https://www.ashland.com", "snippet": "Specialty chemicals"},
    ]

    with patch(
        "app.agents.searchEngine.sources.search_utils.search",
        return_value=fake_results,
    ), patch(
        "app.agents.searchEngine.sources.search_utils._check_domain_exists",
    ) as mock_check, patch(
        "app.agents.searchEngine.sources.search_utils._verify_domain_with_llm",
        return_value=True,
    ), patch(
        "app.agents.searchEngine.sources.search_utils.asyncio",
    ) as mock_asyncio:
        mock_asyncio.run.return_value = "# Ashland homepage"
        domain = _try_search_domain("Ashland")

    assert domain == "ashland.com"


def test_find_product_page_tries_specific_first():
    from app.agents.searchEngine.sources.search_utils import find_product_page

    call_count = 0

    def mock_search(query, max_results=5):
        nonlocal call_count
        call_count += 1
        if "product specifications" in query:
            return []  # specific query finds nothing
        return [
            {"title": "Mag Stearate", "url": "https://purebulk.com/products/magnesium-stearate", "snippet": "..."},
        ]

    with patch("app.agents.searchEngine.sources.search_utils.search", side_effect=mock_search):
        url = find_product_page("magnesium stearate", "purebulk.com")

    assert url == "https://purebulk.com/products/magnesium-stearate"
    assert call_count == 2  # tried specific first, then broader


def test_find_product_page_returns_none_on_no_results():
    from app.agents.searchEngine.sources.search_utils import find_product_page

    with patch("app.agents.searchEngine.sources.search_utils.search", return_value=[]):
        url = find_product_page("unknown material", "purebulk.com")

    assert url is None
