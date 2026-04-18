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
