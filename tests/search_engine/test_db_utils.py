"""Tests for DB utility functions."""

from __future__ import annotations



def test_parse_supplier_id():
    from app.agents.searchEngine.sources.db_utils import parse_supplier_id

    assert parse_supplier_id("sup_db_12") == 12
    assert parse_supplier_id("sup_db_7") == 7
    assert parse_supplier_id("sup_db_100") == 100


def test_parse_supplier_id_edge_cases():
    from app.agents.searchEngine.sources.db_utils import parse_supplier_id

    assert parse_supplier_id("sup_db_1") == 1
    assert parse_supplier_id("sup_db_999") == 999
