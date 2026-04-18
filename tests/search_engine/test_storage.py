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
    from app.agents.searchEngine.storage import EnrichmentStore

    store = EnrichmentStore()
    result = _make_result("ing_db_42")
    store.save(result)
    loaded = store.get("ing_db_42")
    assert loaded is not None
    assert loaded["material_id"] == "ing_db_42"


def test_get_missing_returns_none():
    from app.agents.searchEngine.storage import EnrichmentStore

    store = EnrichmentStore()
    assert store.get("nonexistent") is None


def test_save_overwrites():
    from app.agents.searchEngine.storage import EnrichmentStore

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
    from app.agents.searchEngine.storage import EnrichmentStore

    store = EnrichmentStore()
    store.save(_make_result("ing_db_1"))
    store.save(_make_result("ing_db_2"))
    all_results = store.list_all()
    assert len(all_results) == 2
