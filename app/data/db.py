"""Read-only SQLite connection helper."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "db.sqlite"


def is_available() -> bool:
    return DB_PATH.exists()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
