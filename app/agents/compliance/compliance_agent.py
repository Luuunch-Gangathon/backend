"""ComplianceAgent — verifies a substitution is compliant for a finished good.

TBD: will check regulatory constraints (REACH, RoHS, food-grade, etc.)
against enriched data from SearchEngine.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ComplianceAgent:
    def check(self, rm_id: str, substitute_id: str, product_id: str) -> bool:
        """Return True if substitute_id is compliant in context of product_id.

        TODO: implement compliance inference against enriched DB data.
        """
        logger.debug(
            "ComplianceAgent.check called: %s → %s in %s (stub, returns True)",
            rm_id, substitute_id, product_id,
        )
        return True
