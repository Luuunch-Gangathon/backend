"""AuditorAgent

Reviews proposals and flags hallucinated claims or unsupported evidence.

Writes to:
  - proposals (confidence/flags columns — TBD)
"""

from __future__ import annotations
import logging
from app.data import db

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("AuditorAgent: started")
    # TODO: implement
    logger.info("AuditorAgent: done")
