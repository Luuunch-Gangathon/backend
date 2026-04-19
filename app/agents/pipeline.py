"""Pipeline — runs once on startup.

SearchEngine enriches all raw materials and finished products
that don't have specs yet.
All other agents (compliance, proposal, auditor) are on-demand only.

Set SKIP_SEARCH_ENGINE=true in .env to skip enrichment on startup (useful
for local development when you don't want to wait for LLM calls).
"""

from __future__ import annotations
import logging
import os
from app.agents import search_engine

logger = logging.getLogger(__name__)


async def run() -> None:
    """Run startup pipeline: material enrichment, then product enrichment."""
    if os.environ.get("SKIP_SEARCH_ENGINE", "").lower() in ("1", "true", "yes"):
        logger.info("Pipeline: SKIP_SEARCH_ENGINE set — skipping SearchEngine")
        return

    logger.info("Pipeline: started")

    try:
        await search_engine.run_all_products()
    except Exception:
        logger.exception("Pipeline: product enrichment failed — skipping")

    try:
        await search_engine.run_all()
    except Exception:
        logger.exception("Pipeline: material enrichment failed — skipping")

    logger.info("Pipeline: done")
