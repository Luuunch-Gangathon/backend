"""SearchEngine

Enriches raw materials with external data (web search), generates embeddings,
and finds similar materials via pgvector.

Two entry points:
  run_all()          — startup: process all unenriched materials
  run_one(rm_name)   — on-demand: process single material (from chat or frontend)

Flow per material (from activity diagram):
  Raw Material → Web Search → New Information → Updated Raw Material
  → Generate Embedding → Store in substitution_groups → Similarities Search

Writes to:
  - substitution_groups (spec + embedding columns via rag.store_embedding)
"""

from __future__ import annotations
import logging
from app.data import rag

logger = logging.getLogger(__name__)


async def run_all() -> None:
    """Process all raw materials that don't have embeddings yet.

    Called by pipeline on startup. Skips materials already embedded.
    """
    names = await rag.get_unembedded_names()
    logger.info("SearchEngine: %d materials to process", len(names))

    ok, fail = 0, 0
    for name in names:
        try:
            await _enrich_and_embed(name)
            ok += 1
        except Exception:
            fail += 1
            logger.exception("SearchEngine: failed for %r — skipping", name)

    logger.info("SearchEngine: done — %d ok, %d failed", ok, fail)


async def run_one(raw_material_name: str) -> None:
    """Enrich and embed a single raw material. Called on-demand from chat or frontend."""
    logger.info("SearchEngine: on-demand enrich for %r", raw_material_name)
    await _enrich_and_embed(raw_material_name)
    logger.info("SearchEngine: done for %r", raw_material_name)


async def _enrich_and_embed(name: str) -> None:
    """Core enrichment flow for one raw material.

    Steps:
    1. Web search — fetch specs, certs, allergens from external sources
    2. Build enriched result dict
    3. Store embedding via rag.store_embedding()

    TODO: teammate implements actual web search logic.
    Currently: falls back to name-only embedding.
    """
    # TODO: implement web search + enrichment
    # enriched_result = await _web_search(name)
    # await rag.store_embedding(enriched_result)

    # Fallback: embed just the name until web search is implemented
    await rag.store_name_only_embedding(name)
