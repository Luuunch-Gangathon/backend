"""Compliance scoring schemas.

SubstituteProposal is the core output of the compliance agent.
ScoreBreakdown provides a quantifiable, auditable 5-dimension scoring rubric
so every score can be justified (why 75, not 80?).

Dimensions (each 0–20, total 0–100):
  functional_equivalence — same functional role in the formulation
  spec_compatibility     — physical/chemical overlap (form, grade, origin)
  regulatory_fit         — GRAS, recalls, regulatory pathway alignment
  dietary_compliance     — preserves dietary claims (vegan, halal, allergens)
  certification_match    — retains required certifications (organic, non-GMO)
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    """Per-dimension compliance scores (0–20 each, sum = total score)."""
    functional_equivalence: int
    spec_compatibility: int
    regulatory_fit: int
    dietary_compliance: int
    certification_match: int


class SubstituteProposal(BaseModel):
    """A scored substitute candidate returned by the compliance agent.

    Attributes:
        id: Raw material DB id of the proposed substitute.
        sku: SKU string for display/linking.
        score: Total compliance score 0–100 (sum of breakdown dimensions).
        score_breakdown: Per-dimension scores. Populated by GPT-4o structured output.
        reasoning: LLM-generated explanation citing each dimension score and evidence.
    """
    id: int
    sku: str = ""
    score: int
    score_breakdown: ScoreBreakdown | None = None
    reasoning: str


class ComplianceResult(BaseModel):
    raw_material_id: int
    proposal: Optional[SubstituteProposal] = None


class SubstituteScoreRequest(BaseModel):
    candidate_ids: list[int]
