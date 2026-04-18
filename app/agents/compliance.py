"""ComplianceAgent

Verifies compliance requirements for each proposal.

Writes to:
  - proposals (compliance_requirements column)
"""

from __future__ import annotations
import logging
from app.data import db

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("ComplianceAgent: started")
    # TODO: implement
    logger.info("ComplianceAgent: done")
