"""SearchEngine

Scrapes external sources and enriches raw material spec data.
After enriching each material, hands the result to SubstitutionAgent
which builds and stores the embedding.

Writes to:
  - substitution_groups (via substitution.store_embedding)
"""

from __future__ import annotations

import logging

from app.agents import substitution

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("SearchEngine: started")
    # TODO: fetch all raw_material_names from raw_material_map,
    # run web enrichment for each, call enrich_and_store() per name.
    logger.info("SearchEngine: done")


async def enrich_and_store(enriched_result: dict) -> None:
    """Hand off a completed enrichment result to SubstitutionAgent for embedding storage."""
    await substitution.store_embedding(enriched_result)
