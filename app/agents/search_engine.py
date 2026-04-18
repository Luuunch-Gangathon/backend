"""SearchEngine

Scrapes external sources and enriches raw material data.

Writes to:
  - TBD (enrichment schema not yet decided)
"""

from __future__ import annotations
import logging
from app.data import db

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("SearchEngine: started")
    # TODO: implement
    logger.info("SearchEngine: done")
