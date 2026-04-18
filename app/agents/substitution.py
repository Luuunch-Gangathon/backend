"""SubstitutionAgent

Finds functionally equivalent raw materials and writes results to DB.

Writes to:
  - substitution_groups
  - substitutions
"""

from __future__ import annotations
import logging
from app.data import db

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("SubstitutionAgent: started")
    # TODO: implement
    logger.info("SubstitutionAgent: done")
