"""Pipeline — runs once on startup.

SearchEngine enriches all raw materials that don't have embeddings yet.
All other agents (compliance, proposal, auditor) are on-demand only.
"""

from __future__ import annotations
import logging
from app.agents import search_engine

logger = logging.getLogger(__name__)


async def run() -> None:
    """Run startup pipeline. Currently: SearchEngine only."""
    logger.info("Pipeline: started")

    try:
        await search_engine.run_all()
    except Exception:
        logger.exception("Pipeline: SearchEngine failed — skipping")

    logger.info("Pipeline: done")
