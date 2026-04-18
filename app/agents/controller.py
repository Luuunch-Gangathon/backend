"""Controller — startup orchestration only.

Triggers SearchEngine enrichment for all raw materials on app boot.
Request-time logic lives in the routers directly.
"""

from __future__ import annotations

import logging

from app.data import repo
from app.agents.search_engine.search_engine import SearchEngine

logger = logging.getLogger(__name__)

_search_engine = SearchEngine()


async def initialize() -> None:
    raw_materials = await repo.list_raw_materials()
    logger.info("Enriching %d raw materials", len(raw_materials))
    for rm in raw_materials:
        try:
            await _search_engine.enrich(rm)
        except Exception:
            logger.exception("SearchEngine.enrich failed for %s", rm.id)
