# TBD — schema draft, subject to change as SubstitutionAgent is implemented.
# No data returned yet (substitutions table empty, agent disabled in pipeline).
# reason field may expand to include confidence score, evidence sources, etc.

from __future__ import annotations
from pydantic import BaseModel


class Substitution(BaseModel):
    id: int
    from_raw_material_id: int
    to_raw_material_id: int
    reason: str
