"""SearchEngine — enriches raw materials with external data.

Teammate implements the actual search logic here.
Contract: receive a RawMaterial, write enriched fields back to DB.
"""

from __future__ import annotations

import logging

from app.schemas import RawMaterial

logger = logging.getLogger(__name__)


class SearchEngine:
    async def enrich(self, raw_material: RawMaterial) -> None:
        """Fetch external data for a raw material and persist to DB.

        TODO (teammate): implement web scraping, PDF parsing, regulatory DB
        lookups here. Write results into enriched columns in DB.

        Args:
            raw_material: the ingredient to enrich.
        """
        logger.debug("SearchEngine.enrich called for %s (stub)", raw_material.id)
