# Enrichment Search Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a config-driven, domain-agnostic enrichment pipeline that normalizes raw material names, queries external sources in trust-tier order, and returns provenance-tagged property values.

**Architecture:** Three decoupled layers — Config (what properties to find, which sources to try), Engine (waterfall loop that fills gaps per-property), and Source Handlers (plain functions returning whatever they can find). External APIs are stubbed initially; real integrations replace stubs one-by-one later.

**Tech Stack:** Python 3.11+, Pydantic 2.x, pytest, FastAPI (existing), SQLite (existing DB at `assets/db.sqlite`)

---

## File Structure

```
app/api/search_engine/
├── __init__.py          # Public exports: enrich()
├── config.py            # PROPERTIES, SOURCES, TRUST_TIERS
├── models.py            # PropertyResult, EnrichmentResult
├── normalizer.py        # SKU -> clean material name
├── storage.py           # Save/load enrichment results (in-memory mock)
├── handlers.py          # Source handler stubs (one function per source)
└── engine.py            # Main enrich() waterfall loop

tests/search_engine/
├── __init__.py
├── test_models.py
├── test_config.py
├── test_normalizer.py
├── test_storage.py
├── test_handlers.py
└── test_engine.py
```

---

### Task 1: Project setup

**Files:**
- Modify: `requirements.txt`
- Create: `app/api/search_engine/__init__.py`
- Create: `tests/search_engine/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Add pytest to requirements**

Add `pytest` to `requirements.txt`:

```
pytest==8.3.5
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: successful install including pytest

- [ ] **Step 3: Create package skeletons**

Create `app/api/search_engine/__init__.py`:
```python
"""Enrichment search engine — config-driven material property enrichment."""
```

Create `tests/__init__.py`:
```python
```

Create `tests/search_engine/__init__.py`:
```python
```

- [ ] **Step 4: Verify pytest runs**

Run: `python -m pytest tests/ -v`
Expected: "no tests ran" (0 collected), exit code 5 (no tests), no import errors

- [ ] **Step 5: Commit**

```bash
git add requirements.txt app/api/search_engine/__init__.py tests/__init__.py tests/search_engine/__init__.py
git commit -m "chore: add pytest, create search_engine package skeleton"
```

---

### Task 2: Models — PropertyResult, EnrichmentResult

**Files:**
- Create: `app/api/search_engine/models.py`
- Create: `tests/search_engine/test_models.py`

- [ ] **Step 1: Write failing tests for PropertyResult**

Create `tests/search_engine/test_models.py`:

```python
"""Tests for enrichment data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_property_result_valid():
    from app.api.search_engine.models import PropertyResult

    pr = PropertyResult(
        value={"cas_number": "557-04-0", "synonyms": ["magnesium octadecanoate"]},
        confidence="verified",
        source_name="pubchem",
        source_url="https://pubchem.ncbi.nlm.nih.gov/compound/11177",
        raw_excerpt="Magnesium stearate, CAS 557-04-0",
    )
    assert pr.confidence == "verified"
    assert pr.source_name == "pubchem"


def test_property_result_unknown():
    from app.api.search_engine.models import PropertyResult

    pr = PropertyResult(
        value=None,
        confidence="unknown",
        source_name=None,
        source_url=None,
        raw_excerpt=None,
    )
    assert pr.confidence == "unknown"
    assert pr.value is None


def test_property_result_invalid_confidence():
    from app.api.search_engine.models import PropertyResult

    with pytest.raises(ValidationError):
        PropertyResult(
            value="something",
            confidence="super_trusted",
            source_name="test",
            source_url=None,
            raw_excerpt=None,
        )


def test_enrichment_result_valid():
    from app.api.search_engine.models import EnrichmentResult, PropertyResult

    pr = PropertyResult(
        value=True,
        confidence="verified",
        source_name="pubchem",
        source_url="https://example.com",
        raw_excerpt="excerpt",
    )
    er = EnrichmentResult(
        material_id="ing_db_42",
        raw_sku="RM-C5-magnesium-stearate-c3a91d20",
        normalized_name="magnesium stearate",
        company_id="co_db_5",
        supplier_ids=["sup_db_12"],
        enriched_at="2026-04-18T02:30:00Z",
        completeness=1,
        total_properties=9,
        properties={"chemical_identity": pr},
    )
    assert er.material_id == "ing_db_42"
    assert er.completeness == 1
    assert "chemical_identity" in er.properties


def test_enrichment_result_empty_properties():
    from app.api.search_engine.models import EnrichmentResult

    er = EnrichmentResult(
        material_id="ing_db_1",
        raw_sku="RM-C1-test-abc12345",
        normalized_name="test",
        company_id="co_db_1",
        supplier_ids=[],
        enriched_at="2026-04-18T00:00:00Z",
        completeness=0,
        total_properties=9,
        properties={},
    )
    assert er.completeness == 0
    assert er.properties == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.api.search_engine.models'`

- [ ] **Step 3: Implement models**

Create `app/api/search_engine/models.py`:

```python
"""Data models for enrichment results."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class PropertyResult(BaseModel):
    """A single enriched property value with provenance."""

    value: Any
    confidence: Literal["verified", "probable", "inferred", "unknown"]
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    raw_excerpt: Optional[str] = None


class EnrichmentResult(BaseModel):
    """Full enrichment output for one material."""

    material_id: str
    raw_sku: str
    normalized_name: str
    company_id: str
    supplier_ids: list[str]
    enriched_at: str
    completeness: int
    total_properties: int
    properties: dict[str, PropertyResult]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_models.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/models.py tests/search_engine/test_models.py
git commit -m "feat: add PropertyResult and EnrichmentResult models"
```

---

### Task 3: Config — PROPERTIES, SOURCES, TRUST_TIERS

**Files:**
- Create: `app/api/search_engine/config.py`
- Create: `tests/search_engine/test_config.py`

- [ ] **Step 1: Write failing tests for config**

Create `tests/search_engine/test_config.py`:

```python
"""Tests for search engine configuration."""

from __future__ import annotations


def test_properties_is_list_of_strings():
    from app.api.search_engine.config import PROPERTIES

    assert isinstance(PROPERTIES, list)
    assert len(PROPERTIES) == 9
    assert all(isinstance(p, str) for p in PROPERTIES)


def test_properties_contains_expected():
    from app.api.search_engine.config import PROPERTIES

    expected = [
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
    assert PROPERTIES == expected


def test_trust_tiers_order():
    from app.api.search_engine.config import TRUST_TIERS

    assert TRUST_TIERS == ["verified", "probable", "inferred"]


def test_sources_have_required_fields():
    from app.api.search_engine.config import SOURCES

    for source in SOURCES:
        assert "name" in source
        assert "trust_tier" in source
        assert "provides" in source
        assert source["trust_tier"] in ("verified", "probable", "inferred")
        assert isinstance(source["provides"], list)


def test_sources_trust_tiers_are_valid():
    from app.api.search_engine.config import SOURCES, TRUST_TIERS

    for source in SOURCES:
        assert source["trust_tier"] in TRUST_TIERS


def test_wildcard_sources_exist():
    from app.api.search_engine.config import SOURCES

    wildcard = [s for s in SOURCES if "*" in s["provides"]]
    assert len(wildcard) >= 1, "At least one source should provide '*'"


def test_every_property_has_at_least_one_source():
    from app.api.search_engine.config import PROPERTIES, SOURCES

    for prop in PROPERTIES:
        providers = [
            s for s in SOURCES if prop in s["provides"] or "*" in s["provides"]
        ]
        assert len(providers) >= 1, f"No source provides '{prop}'"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement config**

Create `app/api/search_engine/config.py`:

```python
"""Search engine configuration — properties, sources, trust tiers.

To adapt to a new domain (e.g. packaging materials), change PROPERTIES
and SOURCES here. The engine and handlers do not need modification.
"""

from __future__ import annotations

PROPERTIES: list[str] = [
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

TRUST_TIERS: list[str] = ["verified", "probable", "inferred"]

SOURCES: list[dict] = [
    {
        "name": "supplier_website",
        "trust_tier": "verified",
        "provides": ["*"],
    },
    {
        "name": "pubchem",
        "trust_tier": "verified",
        "provides": ["chemical_identity"],
    },
    {
        "name": "chebi",
        "trust_tier": "verified",
        "provides": ["functional_role"],
    },
    {
        "name": "foodb",
        "trust_tier": "verified",
        "provides": ["source_origin"],
    },
    {
        "name": "open_food_facts",
        "trust_tier": "verified",
        "provides": ["allergens", "dietary_flags", "certifications"],
    },
    {
        "name": "nih_dsld",
        "trust_tier": "verified",
        "provides": ["dietary_flags", "certifications"],
    },
    {
        "name": "openfda",
        "trust_tier": "verified",
        "provides": ["regulatory_status"],
    },
    {
        "name": "fda_eafus",
        "trust_tier": "verified",
        "provides": ["regulatory_status"],
    },
    {
        "name": "efsa",
        "trust_tier": "verified",
        "provides": ["regulatory_status"],
    },
    {
        "name": "retail_page",
        "trust_tier": "probable",
        "provides": ["*"],
    },
    {
        "name": "web_search",
        "trust_tier": "inferred",
        "provides": ["*"],
    },
    {
        "name": "llm_knowledge",
        "trust_tier": "inferred",
        "provides": ["*"],
    },
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_config.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/config.py tests/search_engine/test_config.py
git commit -m "feat: add search engine config — properties, sources, trust tiers"
```

---

### Task 4: Normalizer — SKU to clean material name

**Files:**
- Create: `app/api/search_engine/normalizer.py`
- Create: `tests/search_engine/test_normalizer.py`

SKU format from the DB: `RM-C{companyNum}-{material-name}-{8char-hex-hash}`
Examples:
- `RM-C52-magnesium-stearate-c3a91d20` → `magnesium stearate`
- `RM-C47-organic-dairy-whey-protein-concentrate-380e0c61` → `organic dairy whey protein concentrate`
- `RM-C40-l-leucine-dc251fa2` → `l-leucine`
- `RM-C5-natural-flavor-177a6a66` → `natural flavor`
- `RM-C62-salt-8c7e3d71` → `salt`

The hash is always 8 hex chars. The company prefix is always `RM-C{digits}-`.

Note: `l-leucine` should keep its internal hyphen (it's part of the name, not a word separator). The approach: strip the known prefix and suffix by structure, then replace remaining hyphens with spaces. But `l-leucine` is tricky — the `l-` is a chemical prefix. For now, a simple approach: strip prefix `RM-C\d+-` and suffix `-[0-9a-f]{8}`, replace remaining hyphens with spaces. The `l-leucine` case will become `l leucine` which is acceptable for search queries. Perfect normalization of chemical names is out of scope — PubChem synonym matching will handle it.

- [ ] **Step 1: Write failing tests**

Create `tests/search_engine/test_normalizer.py`:

```python
"""Tests for material name normalization."""

from __future__ import annotations


def test_basic_normalization():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C52-magnesium-stearate-c3a91d20") == "magnesium stearate"


def test_long_name():
    from app.api.search_engine.normalizer import normalize_sku

    result = normalize_sku(
        "RM-C47-organic-dairy-whey-protein-concentrate-380e0c61"
    )
    assert result == "organic dairy whey protein concentrate"


def test_single_word_name():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C62-salt-8c7e3d71") == "salt"


def test_double_digit_company():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C17-cupric-oxide-95cf9a6a") == "cupric oxide"


def test_name_with_numbers():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C40-l-leucine-dc251fa2") == "l leucine"


def test_normalize_raw_fields():
    from app.api.search_engine.normalizer import normalize

    fields = {
        "SKU": "RM-C5-magnesium-stearate-c3a91d20",
        "CompanyId": 5,
        "Id": 42,
    }
    result = normalize(fields)
    assert result["normalized_name"] == "magnesium stearate"
    assert result["material_id"] == "ing_db_42"
    assert result["company_id"] == "co_db_5"
    assert result["raw_sku"] == "RM-C5-magnesium-stearate-c3a91d20"


def test_normalize_includes_supplier_ids():
    from app.api.search_engine.normalizer import normalize

    fields = {
        "SKU": "RM-C5-magnesium-stearate-c3a91d20",
        "CompanyId": 5,
        "Id": 42,
        "SupplierIds": [12, 7],
    }
    result = normalize(fields)
    assert result["supplier_ids"] == ["sup_db_12", "sup_db_7"]


def test_normalize_no_suppliers():
    from app.api.search_engine.normalizer import normalize

    fields = {"SKU": "RM-C1-test-abcd1234", "CompanyId": 1, "Id": 1}
    result = normalize(fields)
    assert result["supplier_ids"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_normalizer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement normalizer**

Create `app/api/search_engine/normalizer.py`:

```python
"""Material name normalization — extracts clean name from raw DB fields.

SKU format: RM-C{companyNum}-{material-name}-{8char-hex-hash}
"""

from __future__ import annotations

import re


def normalize_sku(sku: str) -> str:
    """Extract clean material name from a raw SKU string."""
    # Strip prefix: RM-C{digits}-
    without_prefix = re.sub(r"^RM-C\d+-", "", sku)
    # Strip suffix: -{8 hex chars} at end
    without_hash = re.sub(r"-[0-9a-f]{8}$", "", without_prefix)
    # Replace hyphens with spaces
    return without_hash.replace("-", " ")


def normalize(raw_fields: dict) -> dict:
    """Normalize raw DB fields into a clean context dict for the engine."""
    supplier_ids_raw = raw_fields.get("SupplierIds", [])
    return {
        "material_id": f"ing_db_{raw_fields['Id']}",
        "raw_sku": raw_fields["SKU"],
        "normalized_name": normalize_sku(raw_fields["SKU"]),
        "company_id": f"co_db_{raw_fields['CompanyId']}",
        "supplier_ids": [f"sup_db_{sid}" for sid in supplier_ids_raw],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_normalizer.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/normalizer.py tests/search_engine/test_normalizer.py
git commit -m "feat: add SKU normalizer for material name extraction"
```

---

### Task 5: Storage — mock save/load

**Files:**
- Create: `app/api/search_engine/storage.py`
- Create: `tests/search_engine/test_storage.py`

Uses an in-memory dict for now. Interface is `save_enrichment()` and `get_enrichment()` — easy to swap to SQLite later.

- [ ] **Step 1: Write failing tests**

Create `tests/search_engine/test_storage.py`:

```python
"""Tests for enrichment storage (in-memory mock)."""

from __future__ import annotations


def _make_result(material_id: str = "ing_db_1") -> dict:
    """Helper to build a minimal EnrichmentResult dict."""
    return {
        "material_id": material_id,
        "raw_sku": "RM-C1-test-abcd1234",
        "normalized_name": "test",
        "company_id": "co_db_1",
        "supplier_ids": [],
        "enriched_at": "2026-04-18T00:00:00Z",
        "completeness": 0,
        "total_properties": 9,
        "properties": {},
    }


def test_save_and_get():
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()
    result = _make_result("ing_db_42")
    store.save(result)
    loaded = store.get("ing_db_42")
    assert loaded is not None
    assert loaded["material_id"] == "ing_db_42"


def test_get_missing_returns_none():
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()
    assert store.get("nonexistent") is None


def test_save_overwrites():
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()
    r1 = _make_result("ing_db_1")
    r1["completeness"] = 0
    store.save(r1)

    r2 = _make_result("ing_db_1")
    r2["completeness"] = 5
    store.save(r2)

    loaded = store.get("ing_db_1")
    assert loaded["completeness"] == 5


def test_list_all():
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()
    store.save(_make_result("ing_db_1"))
    store.save(_make_result("ing_db_2"))
    all_results = store.list_all()
    assert len(all_results) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement storage**

Create `app/api/search_engine/storage.py`:

```python
"""Enrichment result storage.

In-memory mock implementation. Replace internals with SQLite/Postgres
later — the interface (save/get/list_all) stays the same.
"""

from __future__ import annotations


class EnrichmentStore:
    """Simple in-memory store for enrichment results."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def save(self, result: dict) -> None:
        """Save or overwrite an enrichment result by material_id."""
        self._data[result["material_id"]] = result

    def get(self, material_id: str) -> dict | None:
        """Retrieve an enrichment result, or None if not found."""
        return self._data.get(material_id)

    def list_all(self) -> list[dict]:
        """Return all stored enrichment results."""
        return list(self._data.values())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_storage.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/storage.py tests/search_engine/test_storage.py
git commit -m "feat: add in-memory enrichment storage (mock)"
```

---

### Task 6: Source handler stubs

**Files:**
- Create: `app/api/search_engine/handlers.py`
- Create: `tests/search_engine/test_handlers.py`

Every handler is a plain function: `fn(name: str, context: dict) -> list[dict]`.
Each dict in the returned list has keys: `property`, `value`, `source_url`, `raw_excerpt`.
All handlers return empty lists for now (stubs). Real implementations replace them one by one later.

- [ ] **Step 1: Write failing tests**

Create `tests/search_engine/test_handlers.py`:

```python
"""Tests for source handler stubs."""

from __future__ import annotations


def test_handler_registry_has_all_sources():
    from app.api.search_engine.config import SOURCES
    from app.api.search_engine.handlers import SOURCE_HANDLERS

    for source in SOURCES:
        assert source["name"] in SOURCE_HANDLERS, (
            f"Missing handler for source '{source['name']}'"
        )


def test_all_handlers_are_callable():
    from app.api.search_engine.handlers import SOURCE_HANDLERS

    for name, handler in SOURCE_HANDLERS.items():
        assert callable(handler), f"Handler '{name}' is not callable"


def test_stub_handler_returns_list():
    from app.api.search_engine.handlers import SOURCE_HANDLERS

    for name, handler in SOURCE_HANDLERS.items():
        result = handler("magnesium stearate", {})
        assert isinstance(result, list), (
            f"Handler '{name}' should return a list, got {type(result)}"
        )


def test_stub_handler_result_items_have_required_keys():
    from app.api.search_engine.handlers import SOURCE_HANDLERS

    required_keys = {"property", "value", "source_url", "raw_excerpt"}
    for name, handler in SOURCE_HANDLERS.items():
        results = handler("magnesium stearate", {})
        for item in results:
            assert required_keys.issubset(item.keys()), (
                f"Handler '{name}' result missing keys: {required_keys - item.keys()}"
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_handlers.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement handler stubs**

Create `app/api/search_engine/handlers.py`:

```python
"""Source handler functions.

Each handler is a plain function:
    fn(name: str, context: dict) -> list[dict]

Each dict in the returned list must have:
    - property: str (which property this value is for)
    - value: Any (the property value)
    - source_url: str | None (citable URL)
    - raw_excerpt: str | None (text the value was extracted from)

All handlers are stubs returning empty lists. Replace with real
implementations one by one. The engine and config do not change.
"""

from __future__ import annotations


def _stub(name: str, context: dict) -> list[dict]:
    """Placeholder handler — returns no results."""
    return []


def supplier_website_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def pubchem_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def chebi_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def foodb_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def open_food_facts_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def nih_dsld_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def openfda_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def fda_eafus_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def efsa_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def retail_page_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def web_search_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def llm_knowledge_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


SOURCE_HANDLERS: dict[str, callable] = {
    "supplier_website": supplier_website_enrich,
    "pubchem": pubchem_enrich,
    "chebi": chebi_enrich,
    "foodb": foodb_enrich,
    "open_food_facts": open_food_facts_enrich,
    "nih_dsld": nih_dsld_enrich,
    "openfda": openfda_enrich,
    "fda_eafus": fda_eafus_enrich,
    "efsa": efsa_enrich,
    "retail_page": retail_page_enrich,
    "web_search": web_search_enrich,
    "llm_knowledge": llm_knowledge_enrich,
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_handlers.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/handlers.py tests/search_engine/test_handlers.py
git commit -m "feat: add source handler stubs for all 12 sources"
```

---

### Task 7: Engine — the waterfall loop

**Files:**
- Create: `app/api/search_engine/engine.py`
- Create: `tests/search_engine/test_engine.py`

The engine is the core loop: for each unfilled property, find sources that provide it, try them in trust-tier order, take the first value found, tag with provenance.

- [ ] **Step 1: Write failing tests**

Create `tests/search_engine/test_engine.py`:

```python
"""Tests for the enrichment engine waterfall loop."""

from __future__ import annotations

from unittest.mock import patch


def _fake_handler_pubchem(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "chemical_identity",
                "value": {"cas_number": "557-04-0"},
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/11177",
                "raw_excerpt": "CAS 557-04-0",
            }
        ]
    return []


def _fake_handler_chebi(name: str, context: dict) -> list[dict]:
    if name == "magnesium stearate":
        return [
            {
                "property": "functional_role",
                "value": ["lubricant", "flow agent"],
                "source_url": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=9243",
                "raw_excerpt": "Role: lubricant",
            }
        ]
    return []


def _fake_handler_empty(name: str, context: dict) -> list[dict]:
    return []


def test_engine_fills_properties_from_multiple_sources():
    from app.api.search_engine.engine import run_enrichment

    fake_handlers = {
        "supplier_website": _fake_handler_empty,
        "pubchem": _fake_handler_pubchem,
        "chebi": _fake_handler_chebi,
        "foodb": _fake_handler_empty,
        "open_food_facts": _fake_handler_empty,
        "nih_dsld": _fake_handler_empty,
        "openfda": _fake_handler_empty,
        "fda_eafus": _fake_handler_empty,
        "efsa": _fake_handler_empty,
        "retail_page": _fake_handler_empty,
        "web_search": _fake_handler_empty,
        "llm_knowledge": _fake_handler_empty,
    }

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    assert "chemical_identity" in result.properties
    assert result.properties["chemical_identity"].confidence == "verified"
    assert result.properties["chemical_identity"].source_name == "pubchem"

    assert "functional_role" in result.properties
    assert result.properties["functional_role"].source_name == "chebi"

    assert result.completeness == 2


def test_engine_skips_property_already_filled():
    """If a higher-trust source already filled a property, lower sources are not tried."""
    from app.api.search_engine.engine import run_enrichment

    call_log = []

    def _logging_handler(name: str, context: dict) -> list[dict]:
        call_log.append("web_search")
        return [
            {
                "property": "chemical_identity",
                "value": {"cas_number": "000-00-0"},
                "source_url": "https://blog.example.com",
                "raw_excerpt": "some blog",
            }
        ]

    fake_handlers = {
        "supplier_website": _fake_handler_empty,
        "pubchem": _fake_handler_pubchem,
        "chebi": _fake_handler_empty,
        "foodb": _fake_handler_empty,
        "open_food_facts": _fake_handler_empty,
        "nih_dsld": _fake_handler_empty,
        "openfda": _fake_handler_empty,
        "fda_eafus": _fake_handler_empty,
        "efsa": _fake_handler_empty,
        "retail_page": _fake_handler_empty,
        "web_search": _logging_handler,
        "llm_knowledge": _fake_handler_empty,
    }

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    # pubchem (verified) filled chemical_identity, so web_search should not
    # have been called for chemical_identity
    assert result.properties["chemical_identity"].source_name == "pubchem"


def test_engine_unfilled_properties_are_unknown():
    from app.api.search_engine.engine import run_enrichment

    fake_handlers = {s: _fake_handler_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge",
    ]}

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "unknown material",
            {
                "material_id": "ing_db_999",
                "raw_sku": "RM-C1-unknown-material-00000000",
                "company_id": "co_db_1",
                "supplier_ids": [],
            },
        )

    assert result.completeness == 0
    for prop_name in result.properties:
        assert result.properties[prop_name].confidence == "unknown"


def test_engine_respects_trust_tier_order():
    """A 'probable' source should only fill if no 'verified' source did."""
    from app.api.search_engine.engine import run_enrichment

    def _retail_handler(name: str, context: dict) -> list[dict]:
        return [
            {
                "property": "chemical_identity",
                "value": {"cas_number": "999-99-9"},
                "source_url": "https://iherb.com/product",
                "raw_excerpt": "from retail",
            }
        ]

    fake_handlers = {s: _fake_handler_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa",
        "web_search", "llm_knowledge",
    ]}
    fake_handlers["retail_page"] = _retail_handler

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = run_enrichment(
            "magnesium stearate",
            {
                "material_id": "ing_db_42",
                "raw_sku": "RM-C52-magnesium-stearate-c3a91d20",
                "company_id": "co_db_52",
                "supplier_ids": [],
            },
        )

    # retail_page is "probable" — should still fill since no verified source had it
    assert result.properties["chemical_identity"].confidence == "probable"
    assert result.properties["chemical_identity"].source_name == "retail_page"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search_engine/test_engine.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the engine**

Create `app/api/search_engine/engine.py`:

```python
"""Enrichment engine — domain-agnostic waterfall loop.

For each unfilled property, finds sources that declare they provide it,
tries them in trust-tier order, and takes the first value found.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.api.search_engine.config import PROPERTIES, SOURCES, TRUST_TIERS
from app.api.search_engine.handlers import SOURCE_HANDLERS
from app.api.search_engine.models import EnrichmentResult, PropertyResult


def _sources_for_property(prop: str, tier: str) -> list[dict]:
    """Return sources that provide `prop` and belong to `tier`."""
    return [
        s
        for s in SOURCES
        if s["trust_tier"] == tier
        and (prop in s["provides"] or "*" in s["provides"])
    ]


def run_enrichment(name: str, context: dict) -> EnrichmentResult:
    """Run the waterfall enrichment loop for a single material.

    Args:
        name: Normalized material name (e.g. "magnesium stearate").
        context: Dict with material_id, raw_sku, company_id, supplier_ids.

    Returns:
        EnrichmentResult with all properties filled or marked unknown.
    """
    filled: dict[str, PropertyResult] = {}

    for prop in PROPERTIES:
        if prop in filled:
            continue

        found = False
        for tier in TRUST_TIERS:
            if found:
                break
            for source in _sources_for_property(prop, tier):
                handler = SOURCE_HANDLERS.get(source["name"])
                if handler is None:
                    continue
                results = handler(name, context)
                for item in results:
                    if item["property"] == prop:
                        filled[prop] = PropertyResult(
                            value=item["value"],
                            confidence=source["trust_tier"],
                            source_name=source["name"],
                            source_url=item.get("source_url"),
                            raw_excerpt=item.get("raw_excerpt"),
                        )
                        found = True
                        break
                if found:
                    break

        if prop not in filled:
            filled[prop] = PropertyResult(
                value=None,
                confidence="unknown",
                source_name=None,
                source_url=None,
                raw_excerpt=None,
            )

    completeness = sum(
        1 for p in filled.values() if p.confidence != "unknown"
    )

    return EnrichmentResult(
        material_id=context["material_id"],
        raw_sku=context["raw_sku"],
        normalized_name=name,
        company_id=context["company_id"],
        supplier_ids=context.get("supplier_ids", []),
        enriched_at=datetime.now(timezone.utc).isoformat(),
        completeness=completeness,
        total_properties=len(PROPERTIES),
        properties=filled,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search_engine/test_engine.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/engine.py tests/search_engine/test_engine.py
git commit -m "feat: add enrichment engine waterfall loop"
```

---

### Task 8: Public API + integration test

**Files:**
- Modify: `app/api/search_engine/__init__.py`
- Create: `tests/search_engine/test_integration.py`

Wire the normalizer, engine, and storage together into a single `enrich()` entry point.

- [ ] **Step 1: Write failing integration test**

Create `tests/search_engine/test_integration.py`:

```python
"""Integration test — full pipeline from raw DB fields to stored result."""

from __future__ import annotations

from unittest.mock import patch


def _fake_pubchem(name: str, context: dict) -> list[dict]:
    return [
        {
            "property": "chemical_identity",
            "value": {"cas_number": "557-04-0", "synonyms": ["magnesium octadecanoate"]},
            "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/11177",
            "raw_excerpt": "CAS 557-04-0",
        }
    ]


def _fake_empty(name: str, context: dict) -> list[dict]:
    return []


def test_full_pipeline():
    from app.api.search_engine import enrich
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()

    fake_handlers = {s: _fake_empty for s in [
        "supplier_website", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge",
    ]}
    fake_handlers["pubchem"] = _fake_pubchem

    raw_fields = {
        "Id": 42,
        "SKU": "RM-C52-magnesium-stearate-c3a91d20",
        "CompanyId": 52,
        "SupplierIds": [12, 7],
    }

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = enrich(raw_fields, store=store)

    # Check the result
    assert result.material_id == "ing_db_42"
    assert result.normalized_name == "magnesium stearate"
    assert result.company_id == "co_db_52"
    assert result.supplier_ids == ["sup_db_12", "sup_db_7"]
    assert result.completeness == 1
    assert result.properties["chemical_identity"].source_name == "pubchem"
    assert result.properties["chemical_identity"].confidence == "verified"

    # Check it was persisted
    stored = store.get("ing_db_42")
    assert stored is not None
    assert stored["material_id"] == "ing_db_42"


def test_full_pipeline_unknown_material():
    from app.api.search_engine import enrich
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()

    fake_handlers = {s: _fake_empty for s in [
        "supplier_website", "pubchem", "chebi", "foodb", "open_food_facts",
        "nih_dsld", "openfda", "fda_eafus", "efsa", "retail_page",
        "web_search", "llm_knowledge",
    ]}

    raw_fields = {
        "Id": 999,
        "SKU": "RM-C1-mystery-compound-00000000",
        "CompanyId": 1,
    }

    with patch("app.api.search_engine.engine.SOURCE_HANDLERS", fake_handlers):
        result = enrich(raw_fields, store=store)

    assert result.completeness == 0
    assert all(
        p.confidence == "unknown" for p in result.properties.values()
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/search_engine/test_integration.py -v`
Expected: FAIL — `ImportError: cannot import name 'enrich'`

- [ ] **Step 3: Implement the public entry point**

Update `app/api/search_engine/__init__.py`:

```python
"""Enrichment search engine — config-driven material property enrichment.

Usage:
    from app.api.search_engine import enrich
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()
    result = enrich(raw_fields, store=store)
"""

from __future__ import annotations

from app.api.search_engine.engine import run_enrichment
from app.api.search_engine.models import EnrichmentResult
from app.api.search_engine.normalizer import normalize
from app.api.search_engine.storage import EnrichmentStore


def enrich(
    raw_fields: dict,
    store: EnrichmentStore | None = None,
) -> EnrichmentResult:
    """Enrich a raw material from DB fields.

    Args:
        raw_fields: Dict with keys Id, SKU, CompanyId, and optionally SupplierIds.
        store: Optional storage backend. If provided, result is persisted.

    Returns:
        EnrichmentResult with all properties filled or marked unknown.
    """
    context = normalize(raw_fields)
    result = run_enrichment(context["normalized_name"], context)

    if store is not None:
        store.save(result.model_dump())

    return result
```

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/search_engine/ -v`
Expected: All tests pass (2 integration + 4 engine + 4 handlers + 8 normalizer + 4 storage + 7 config + 5 models = 34 tests)

- [ ] **Step 5: Commit**

```bash
git add app/api/search_engine/__init__.py tests/search_engine/test_integration.py
git commit -m "feat: wire up search engine public API with integration tests"
```

---

### Task 9: Run full suite and verify

- [ ] **Step 1: Run all tests from project root**

Run: `python -m pytest tests/ -v`
Expected: 34 passed, 0 failed

- [ ] **Step 2: Verify existing app still works**

Run: `uvicorn app.main:app --reload &` then `curl http://localhost:8000/health`
Expected: `{"status": "ok"}`

Kill the server after verification.

- [ ] **Step 3: Final commit with all files**

Run: `git status` — verify only search engine files are changed.

```bash
git add -A
git commit -m "feat: enrichment search engine — config-driven pipeline with stubs"
```
