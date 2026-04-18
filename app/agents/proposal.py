"""ProposalAgent

Generates consolidation proposals from raw_material_map + substitution_groups.

Writes to:
  - proposals
  - agnes_suggestions
"""

from __future__ import annotations
import logging
from app.data import db

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("ProposalAgent: started")
    # TODO: implement
    logger.info("ProposalAgent: done")
