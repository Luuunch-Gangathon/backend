# Supplier Website Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `supplier_website_enrich` stub with a real implementation that discovers supplier product pages via DuckDuckGo search, crawls them with crawl4ai, and extracts material properties using LLM-powered structured extraction.

**Architecture:** Three components — `search_utils.py` (DuckDuckGo search wrapper + domain cache), `supplier_website.py` (crawl4ai crawling + LLM extraction + result conversion), and a one-line change in `handlers.py` to swap the stub. The handler resolves supplier domains dynamically, finds product pages via `site:` search, crawls with crawl4ai, and extracts properties into the existing handler result format.

**Tech Stack:** crawl4ai (page crawling + LLM extraction), duckduckgo-search (URL discovery), Anthropic Claude via litellm (extraction LLM), Pydantic (extraction schema), existing SQLite DB (supplier name lookup)

---

## File Structure

```
app/api/search_engine/
├── handlers.py                      # Modify: swap stub → real import
├── sources/
│   ├── __init__.py                  # Create: empty
│   ├── search_utils.py              # Create: search(), get_supplier_domain(), find_product_page()
│   └── supplier_website.py          # Create: MaterialProperties, _crawl_and_extract(), supplier_website_enrich()
tests/search_engine/
├── test_search_utils.py             # Create
├── test_supplier_website.py         # Create
```

---

### Task 1: Add dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add new packages to requirements.txt**

Add these lines to `requirements.txt`:

```
crawl4ai
duckduckgo-search
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: successful install of crawl4ai, duckduckgo-search, and their transitive deps

- [ ] **Step 3: Run crawl4ai setup**

Run: `crawl4ai-setup`
Expected: Playwright browsers downloaded (needed for JS-rendered pages)

- [ ] **Step 4: Create sources package**

Create `app/api/search_engine/sources/__init__.py`:

```python
```

- [ ] **Step 5: Verify existing tests still pass**

Run: `python -m pytest tests/search_engine/ -v`
Expected: 34 passed

- [ ] **Step 6: Commit**

```bash
git add requirements.txt app/api/search_engine/sources/__init__.py
git commit -m "chore: add crawl4ai and duckduckgo-search dependencies"
```

---

### Task 2: Search utilities — search wrapper + domain cache

**Files:**
- Create: `app/api/search_engine/sources/search_utils.py`
- Create: `tests/search_engine/test_search_utils.py`

- [ ] **Step 1: Write failing tests**

Create `tests/search_engine/test_search_utils.py`:

```python
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

    # Clear cache
    search_utils._domain_cache.clear()

    fake_results = [
        {"title": "PureBulk", "url": "https://purebulk.com/about", "snippet": "..."},
    ]

    with patch("app.api.search_engine.sources.search_utils.search", return_value=fake_results):
        domain = get_supplier_domain("PureBulk")

    assert domain == "purebulk.com"

    # Second call should use cache, not search again
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_search_utils.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement search_utils**

Create `app/api/search_engine/sources/search_utils.py`:

```python
"""Search utilities — DuckDuckGo wrapper with domain caching.

Provides three functions:
- search(query) — generic web search returning title/url/snippet
- get_supplier_domain(name) — resolves supplier name to domain, cached
- find_product_page(material, domain) — finds product page via site: search
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

_domain_cache: dict[str, str | None] = {}


def search(query: str, max_results: int = 3) -> list[dict]:
    """Search DuckDuckGo and return results as [{title, url, snippet}]."""
    try:
        with DDGS() as ddgs:
            raw = ddgs.text(query, max_results=max_results)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in raw
        ]
    except Exception:
        logger.warning("Search failed for query: %s", query, exc_info=True)
        return []


def extract_domain(url: str) -> str:
    """Extract the registrable domain from a URL (strips www. prefix)."""
    hostname = urlparse(url).hostname or ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname


def get_supplier_domain(supplier_name: str) -> str | None:
    """Resolve a supplier name to its website domain. Results are cached."""
    if supplier_name in _domain_cache:
        return _domain_cache[supplier_name]

    results = search(f'"{supplier_name}" official website', max_results=3)
    if not results:
        _domain_cache[supplier_name] = None
        return None

    domain = extract_domain(results[0]["url"])
    _domain_cache[supplier_name] = domain or None
    return _domain_cache[supplier_name]


def find_product_page(material_name: str, domain: str) -> str | None:
    """Find a product page for a material on a specific supplier domain."""
    results = search(f'"{material_name}" site:{domain}', max_results=3)
    if not results:
        return None
    return results[0]["url"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_search_utils.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/sources/search_utils.py tests/search_engine/test_search_utils.py
git commit -m "feat: add search utilities — DuckDuckGo wrapper + domain cache"
```

---

### Task 3: Supplier name resolution from DB

**Files:**
- Create: `app/api/search_engine/sources/db_utils.py`
- Create: `tests/search_engine/test_db_utils.py`

The handler receives `supplier_ids` like `["sup_db_12", "sup_db_7"]`. We need the actual names from the Supplier table.

- [ ] **Step 1: Write failing tests**

Create `tests/search_engine/test_db_utils.py`:

```python
"""Tests for DB utility functions."""

from __future__ import annotations

from unittest.mock import patch, MagicMock


def test_parse_supplier_id():
    from app.api.search_engine.sources.db_utils import parse_supplier_id

    assert parse_supplier_id("sup_db_12") == 12
    assert parse_supplier_id("sup_db_7") == 7
    assert parse_supplier_id("sup_db_100") == 100


def test_get_supplier_names():
    from app.api.search_engine.sources.db_utils import get_supplier_names

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = [
        {"Name": "PureBulk"},
        {"Name": "Jost Chemical"},
    ]
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.api.search_engine.sources.db_utils.db.get_conn", return_value=mock_ctx):
        with patch("app.api.search_engine.sources.db_utils.db.is_available", return_value=True):
            names = get_supplier_names(["sup_db_12", "sup_db_7"])

    assert names == ["PureBulk", "Jost Chemical"]


def test_get_supplier_names_db_unavailable():
    from app.api.search_engine.sources.db_utils import get_supplier_names

    with patch("app.api.search_engine.sources.db_utils.db.is_available", return_value=False):
        names = get_supplier_names(["sup_db_12"])

    assert names == []


def test_get_supplier_names_empty_list():
    from app.api.search_engine.sources.db_utils import get_supplier_names

    names = get_supplier_names([])
    assert names == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_db_utils.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement db_utils**

Create `app/api/search_engine/sources/db_utils.py`:

```python
"""DB utilities for the search engine sources."""

from __future__ import annotations

from app.data import db


def parse_supplier_id(supplier_id: str) -> int:
    """Extract the raw DB ID from a prefixed supplier ID like 'sup_db_12'."""
    return int(supplier_id.replace("sup_db_", ""))


def get_supplier_names(supplier_ids: list[str]) -> list[str]:
    """Look up supplier names from the DB given prefixed IDs."""
    if not supplier_ids or not db.is_available():
        return []

    raw_ids = [parse_supplier_id(sid) for sid in supplier_ids]
    placeholders = ",".join("?" for _ in raw_ids)

    with db.get_conn() as conn:
        rows = conn.execute(
            f"SELECT Name FROM Supplier WHERE Id IN ({placeholders})",
            raw_ids,
        ).fetchall()

    return [row["Name"] for row in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_db_utils.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/sources/db_utils.py tests/search_engine/test_db_utils.py
git commit -m "feat: add supplier name resolution from DB"
```

---

### Task 4: MaterialProperties extraction schema

**Files:**
- Create: `app/api/search_engine/sources/supplier_website.py`
- Create: `tests/search_engine/test_supplier_website.py`

Start with just the Pydantic schema and the result conversion function. The crawling comes next.

- [ ] **Step 1: Write failing tests**

Create `tests/search_engine/test_supplier_website.py`:

```python
"""Tests for supplier website handler."""

from __future__ import annotations


def test_material_properties_schema():
    from app.api.search_engine.sources.supplier_website import MaterialProperties

    props = MaterialProperties(
        is_correct_material=True,
        chemical_identity={"cas_number": "557-04-0"},
        functional_role=["lubricant"],
        source_origin="plant",
        dietary_flags={"vegan": True},
        allergens={"contains": [], "free_from": ["soy"]},
        certifications=["Non-GMO"],
        regulatory_status={"gras": True},
        form_grade={"form": "powder"},
        price="$25/kg",
    )
    assert props.is_correct_material is True
    assert props.chemical_identity == {"cas_number": "557-04-0"}


def test_material_properties_all_none():
    from app.api.search_engine.sources.supplier_website import MaterialProperties

    props = MaterialProperties(is_correct_material=False)
    assert props.chemical_identity is None
    assert props.allergens is None


def test_convert_to_handler_results():
    from app.api.search_engine.sources.supplier_website import (
        MaterialProperties,
        convert_to_handler_results,
    )

    props = MaterialProperties(
        is_correct_material=True,
        chemical_identity={"cas_number": "557-04-0"},
        functional_role=["lubricant"],
        source_origin=None,
        dietary_flags=None,
        allergens={"contains": [], "free_from": ["soy"]},
        certifications=None,
        regulatory_status=None,
        form_grade=None,
        price=None,
    )

    results = convert_to_handler_results(props, source_url="https://purebulk.com/products/mag", raw_markdown="page text")

    # Should only include non-None properties
    property_names = [r["property"] for r in results]
    assert "chemical_identity" in property_names
    assert "functional_role" in property_names
    assert "allergens" in property_names
    assert "source_origin" not in property_names
    assert "price" not in property_names

    # Check structure
    chem = next(r for r in results if r["property"] == "chemical_identity")
    assert chem["value"] == {"cas_number": "557-04-0"}
    assert chem["source_url"] == "https://purebulk.com/products/mag"
    assert chem["raw_excerpt"] == "page text"


def test_convert_to_handler_results_wrong_material():
    from app.api.search_engine.sources.supplier_website import (
        MaterialProperties,
        convert_to_handler_results,
    )

    props = MaterialProperties(
        is_correct_material=False,
        chemical_identity={"cas_number": "999-99-9"},
    )

    results = convert_to_handler_results(props, source_url="https://example.com", raw_markdown="wrong page")
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_supplier_website.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement schema and conversion**

Create `app/api/search_engine/sources/supplier_website.py`:

```python
"""Supplier website handler — crawl supplier product pages and extract properties.

Uses crawl4ai for page crawling and LLM-powered structured extraction.
Uses DuckDuckGo for URL discovery.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Extraction schema — maps to our 9 properties
EXTRACTION_INSTRUCTION = """
Extract material properties from this product page for the material "{material_name}".

Rules:
- Set is_correct_material to false if this page is NOT about "{material_name}"
- Only extract what is explicitly stated on the page — do not infer or guess
- Leave fields as null if the information is not present
- For allergens, list what the page explicitly says under "contains" and "free_from"
- For dietary_flags, look for vegan, vegetarian, halal, kosher mentions
- For certifications, look for Non-GMO, Organic, GMP, BSE/TSE Free, etc.
- For price, include the unit (e.g. "$25/kg")
"""


class MaterialProperties(BaseModel):
    """Schema for LLM extraction from supplier product pages."""

    is_correct_material: bool
    chemical_identity: Optional[dict[str, Any]] = None
    functional_role: Optional[list[str]] = None
    source_origin: Optional[str] = None
    dietary_flags: Optional[dict[str, Any]] = None
    allergens: Optional[dict[str, Any]] = None
    certifications: Optional[list[str]] = None
    regulatory_status: Optional[dict[str, Any]] = None
    form_grade: Optional[dict[str, Any]] = None
    price: Optional[str] = None


# Properties that map from MaterialProperties fields to handler result "property" keys
_PROPERTY_FIELDS = [
    "chemical_identity",
    "functional_role",
    "source_origin",
    "dietary_flags",
    "allergens",
    "certifications",
    "regulatory_status",
    "form_grade",
    "price",
]


def convert_to_handler_results(
    props: MaterialProperties,
    source_url: str,
    raw_markdown: str,
) -> list[dict]:
    """Convert MaterialProperties to the handler result format.

    Returns empty list if is_correct_material is False.
    Only includes properties that have non-None values.
    """
    if not props.is_correct_material:
        return []

    results = []
    for field_name in _PROPERTY_FIELDS:
        value = getattr(props, field_name)
        if value is not None:
            results.append(
                {
                    "property": field_name,
                    "value": value,
                    "source_url": source_url,
                    "raw_excerpt": raw_markdown[:500] if raw_markdown else None,
                }
            )
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_supplier_website.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/sources/supplier_website.py tests/search_engine/test_supplier_website.py
git commit -m "feat: add MaterialProperties schema and result conversion"
```

---

### Task 5: Crawl-and-extract function

**Files:**
- Modify: `app/api/search_engine/sources/supplier_website.py`
- Modify: `tests/search_engine/test_supplier_website.py`

Add the async crawl function that uses crawl4ai + LLM extraction.

- [ ] **Step 1: Write failing tests**

Append to `tests/search_engine/test_supplier_website.py`:

```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_crawl_and_extract_success():
    from app.api.search_engine.sources.supplier_website import _crawl_and_extract

    fake_extracted = json.dumps([{
        "is_correct_material": True,
        "chemical_identity": {"cas_number": "557-04-0"},
        "functional_role": ["lubricant"],
        "source_origin": "plant",
        "dietary_flags": None,
        "allergens": None,
        "certifications": ["Non-GMO"],
        "regulatory_status": None,
        "form_grade": None,
        "price": None,
    }])

    mock_result = MagicMock()
    mock_result.extracted_content = fake_extracted
    mock_result.markdown = "# Magnesium Stearate\nCAS: 557-04-0"

    mock_crawler = AsyncMock()
    mock_crawler.arun.return_value = mock_result
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.search_engine.sources.supplier_website.AsyncWebCrawler", return_value=mock_crawler):
        props, markdown = await _crawl_and_extract("https://purebulk.com/products/mag", "magnesium stearate")

    assert props is not None
    assert props.is_correct_material is True
    assert props.chemical_identity == {"cas_number": "557-04-0"}
    assert "Magnesium Stearate" in markdown


@pytest.mark.asyncio
async def test_crawl_and_extract_wrong_material():
    from app.api.search_engine.sources.supplier_website import _crawl_and_extract

    fake_extracted = json.dumps([{
        "is_correct_material": False,
    }])

    mock_result = MagicMock()
    mock_result.extracted_content = fake_extracted
    mock_result.markdown = "# Some Other Product"

    mock_crawler = AsyncMock()
    mock_crawler.arun.return_value = mock_result
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.search_engine.sources.supplier_website.AsyncWebCrawler", return_value=mock_crawler):
        props, markdown = await _crawl_and_extract("https://example.com/wrong", "magnesium stearate")

    assert props is not None
    assert props.is_correct_material is False


@pytest.mark.asyncio
async def test_crawl_and_extract_returns_none_on_error():
    from app.api.search_engine.sources.supplier_website import _crawl_and_extract

    mock_crawler = AsyncMock()
    mock_crawler.arun.side_effect = Exception("connection timeout")
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.search_engine.sources.supplier_website.AsyncWebCrawler", return_value=mock_crawler):
        result = await _crawl_and_extract("https://example.com", "magnesium stearate")

    assert result is None
```

Note: add `import json` at the top of the test file, and add `pytest-asyncio` to requirements.txt.

- [ ] **Step 2: Add pytest-asyncio dependency**

Add to `requirements.txt`:
```
pytest-asyncio
```

Run: `pip install pytest-asyncio`

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_supplier_website.py -v`
Expected: FAIL — `_crawl_and_extract` not defined

- [ ] **Step 4: Implement _crawl_and_extract**

Add to `app/api/search_engine/sources/supplier_website.py` (after the existing code):

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy


async def _crawl_and_extract(
    url: str, material_name: str
) -> tuple[MaterialProperties, str] | None:
    """Crawl a URL and extract material properties using LLM.

    Returns (MaterialProperties, raw_markdown) or None on failure.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping supplier website crawl")
        return None

    strategy = LLMExtractionStrategy(
        provider="anthropic/claude-sonnet-4-20250514",
        api_token=api_key,
        schema=MaterialProperties.model_json_schema(),
        instruction=EXTRACTION_INSTRUCTION.format(material_name=material_name),
    )

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, extraction_strategy=strategy)

        raw_markdown = getattr(result, "markdown", "") or ""
        extracted = json.loads(result.extracted_content)

        # crawl4ai returns a list; take the first item
        if isinstance(extracted, list) and len(extracted) > 0:
            props = MaterialProperties(**extracted[0])
        else:
            props = MaterialProperties(**extracted)

        return props, raw_markdown

    except Exception:
        logger.warning("Crawl failed for %s", url, exc_info=True)
        return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_supplier_website.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add requirements.txt app/api/search_engine/sources/supplier_website.py tests/search_engine/test_supplier_website.py
git commit -m "feat: add crawl-and-extract function using crawl4ai"
```

---

### Task 6: Full supplier_website_enrich handler

**Files:**
- Modify: `app/api/search_engine/sources/supplier_website.py`
- Modify: `tests/search_engine/test_supplier_website.py`

Wire together: get supplier names → resolve domains → find product pages → crawl and extract → convert results.

- [ ] **Step 1: Write failing tests**

Append to `tests/search_engine/test_supplier_website.py`:

```python
def test_supplier_website_enrich_full_flow():
    from app.api.search_engine.sources.supplier_website import supplier_website_enrich

    fake_props = MaterialProperties(
        is_correct_material=True,
        chemical_identity={"cas_number": "557-04-0"},
        allergens={"contains": [], "free_from": ["soy"]},
    )

    with patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_names",
        return_value=["PureBulk"],
    ), patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_domain",
        return_value="purebulk.com",
    ), patch(
        "app.api.search_engine.sources.supplier_website.find_product_page",
        return_value="https://purebulk.com/products/magnesium-stearate",
    ), patch(
        "app.api.search_engine.sources.supplier_website._run_crawl_and_extract",
        return_value=(fake_props, "# Magnesium Stearate page content"),
    ):
        results = supplier_website_enrich("magnesium stearate", {"supplier_ids": ["sup_db_12"]})

    assert len(results) == 2
    props_found = {r["property"] for r in results}
    assert "chemical_identity" in props_found
    assert "allergens" in props_found
    assert results[0]["source_url"] == "https://purebulk.com/products/magnesium-stearate"


def test_supplier_website_enrich_no_suppliers():
    from app.api.search_engine.sources.supplier_website import supplier_website_enrich

    results = supplier_website_enrich("magnesium stearate", {"supplier_ids": []})
    assert results == []


def test_supplier_website_enrich_domain_not_found():
    from app.api.search_engine.sources.supplier_website import supplier_website_enrich

    with patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_names",
        return_value=["UnknownSupplier"],
    ), patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_domain",
        return_value=None,
    ):
        results = supplier_website_enrich("magnesium stearate", {"supplier_ids": ["sup_db_99"]})

    assert results == []


def test_supplier_website_enrich_no_product_page():
    from app.api.search_engine.sources.supplier_website import supplier_website_enrich

    with patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_names",
        return_value=["PureBulk"],
    ), patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_domain",
        return_value="purebulk.com",
    ), patch(
        "app.api.search_engine.sources.supplier_website.find_product_page",
        return_value=None,
    ):
        results = supplier_website_enrich("magnesium stearate", {"supplier_ids": ["sup_db_12"]})

    assert results == []


def test_supplier_website_enrich_stops_at_first_successful_supplier():
    from app.api.search_engine.sources.supplier_website import supplier_website_enrich

    fake_props = MaterialProperties(
        is_correct_material=True,
        certifications=["Non-GMO"],
    )

    find_call_count = 0

    def mock_find(material, domain):
        nonlocal find_call_count
        find_call_count += 1
        if domain == "purebulk.com":
            return "https://purebulk.com/products/mag"
        return "https://jostchemical.com/products/mag"

    with patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_names",
        return_value=["PureBulk", "Jost Chemical"],
    ), patch(
        "app.api.search_engine.sources.supplier_website.get_supplier_domain",
        side_effect=["purebulk.com", "jostchemical.com"],
    ), patch(
        "app.api.search_engine.sources.supplier_website.find_product_page",
        side_effect=mock_find,
    ), patch(
        "app.api.search_engine.sources.supplier_website._run_crawl_and_extract",
        return_value=(fake_props, "page text"),
    ):
        results = supplier_website_enrich("magnesium stearate", {"supplier_ids": ["sup_db_12", "sup_db_7"]})

    assert len(results) == 1
    # Should have only searched for the first supplier's product page
    assert find_call_count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_supplier_website.py::test_supplier_website_enrich_full_flow -v`
Expected: FAIL — `supplier_website_enrich` not importable from sources module (or missing functions)

- [ ] **Step 3: Implement the full handler**

Add to `app/api/search_engine/sources/supplier_website.py` (after the existing code):

```python
from app.api.search_engine.sources.search_utils import (
    get_supplier_domain,
    find_product_page,
)
from app.api.search_engine.sources.db_utils import get_supplier_names


def _run_crawl_and_extract(
    url: str, material_name: str
) -> tuple[MaterialProperties, str] | None:
    """Sync wrapper for _crawl_and_extract."""
    return asyncio.run(_crawl_and_extract(url, material_name))


def supplier_website_enrich(name: str, context: dict) -> list[dict]:
    """Enrich material properties by crawling supplier product pages.

    For each supplier associated with this material:
    1. Resolve the supplier's website domain
    2. Search for the material's product page on that domain
    3. Crawl the page and extract properties with LLM
    4. Return on first successful extraction
    """
    supplier_ids = context.get("supplier_ids", [])
    if not supplier_ids:
        return []

    supplier_names = get_supplier_names(supplier_ids)

    for supplier_name in supplier_names:
        domain = get_supplier_domain(supplier_name)
        if domain is None:
            logger.info("Could not resolve domain for supplier: %s", supplier_name)
            continue

        product_url = find_product_page(name, domain)
        if product_url is None:
            logger.info("No product page found for '%s' on %s", name, domain)
            continue

        result = _run_crawl_and_extract(product_url, name)
        if result is None:
            continue

        props, raw_markdown = result
        handler_results = convert_to_handler_results(props, product_url, raw_markdown)
        if handler_results:
            return handler_results

    return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_supplier_website.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/sources/supplier_website.py tests/search_engine/test_supplier_website.py
git commit -m "feat: implement full supplier_website_enrich handler"
```

---

### Task 7: Wire handler into registry

**Files:**
- Modify: `app/api/search_engine/handlers.py:24-25`

- [ ] **Step 1: Write a test to verify wiring**

Append to `tests/search_engine/test_supplier_website.py`:

```python
def test_handler_is_registered():
    from app.api.search_engine.handlers import SOURCE_HANDLERS
    from app.api.search_engine.sources.supplier_website import (
        supplier_website_enrich as real_impl,
    )

    assert SOURCE_HANDLERS["supplier_website"] is real_impl
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/search_engine/test_supplier_website.py::test_handler_is_registered -v`
Expected: FAIL — the stub is still registered, not the real implementation

- [ ] **Step 3: Update handlers.py**

In `app/api/search_engine/handlers.py`, replace the supplier_website stub:

Replace:
```python
def supplier_website_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)
```

With:
```python
from app.api.search_engine.sources.supplier_website import supplier_website_enrich
```

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/search_engine/ -v`
Expected: All tests pass (34 existing + 13 new = 47 total)

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/handlers.py tests/search_engine/test_supplier_website.py
git commit -m "feat: wire real supplier_website handler into registry"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/search_engine/ -v`
Expected: 47+ tests pass, 0 failed

- [ ] **Step 2: Verify app still loads**

Run: `python -c "from app.main import app; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Verify handler import chain works**

Run: `python -c "from app.api.search_engine.handlers import SOURCE_HANDLERS; print(SOURCE_HANDLERS['supplier_website'])"`
Expected: prints the real function reference, not the stub

- [ ] **Step 4: Commit any remaining changes**

```bash
git status
# If clean, no commit needed
```
