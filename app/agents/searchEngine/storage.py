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
