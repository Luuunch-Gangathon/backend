"""Pipeline — runs once on startup.

SearchEngine enriches all raw materials that don't have embeddings yet.
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
    """Run startup pipeline. Currently: SearchEngine only."""
    if os.environ.get("SKIP_SEARCH_ENGINE", "").lower() in ("1", "true", "yes"):
        logger.info("Pipeline: SKIP_SEARCH_ENGINE set — skipping SearchEngine")
        return

    logger.info("Pipeline: started")
    try:
        await search_engine.run_all()
    except Exception:
        logger.exception("Pipeline: SearchEngine failed — skipping")
    logger.info("Pipeline: done")
