"""Pipeline — runs once on startup.

SearchEngine enriches all raw materials and finished products
that don't have specs yet.
All other agents (compliance, proposal, auditor) are on-demand only.
"""

from __future__ import annotations
import logging
from app.agents import search_engine

logger = logging.getLogger(__name__)


async def run() -> None:
    """Run startup pipeline: material enrichment, then product enrichment."""
    logger.info("Pipeline: started")

    try:
        await search_engine.run_all()
    except Exception:
        logger.exception("Pipeline: material enrichment failed — skipping")

    try:
        await search_engine.run_all_products()
    except Exception:
        logger.exception("Pipeline: product enrichment failed — skipping")

    logger.info("Pipeline: done")
