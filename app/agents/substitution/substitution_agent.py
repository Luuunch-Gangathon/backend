"""SubstitutionAgent — finds functionally equivalent raw materials.

Current implementation: DB-only heuristic via raw_material_map.
  Same canonical ingredient name → substitution candidate.

Future: LLM reasoning over enriched specs + compliance data,
        pgvector semantic similarity search.
"""

from __future__ import annotations

import logging

from app.data import repo

logger = logging.getLogger(__name__)


class SubstitutionAgent:
    async def get_substitutes(self, rm_id: str, canonical_name: str) -> list[str]:
        """Return IDs of raw materials that are substitution candidates.

        Args:
            rm_id: the raw material to find substitutes for.
            canonical_name: e.g. 'whey-protein-isolate'.

        Returns:
            List of raw material IDs from other companies with the same ingredient.
        """
        candidates = await repo.get_same_canonical(canonical_name, exclude_id=rm_id)
        logger.debug(
            "SubstitutionAgent: %d candidates for %s (%s)",
            len(candidates), rm_id, canonical_name,
        )
        return candidates
