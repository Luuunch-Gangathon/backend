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
