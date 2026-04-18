# TBD — schema draft, subject to change as ProposalAgent is implemented.
# No data returned yet (proposals table empty, agent disabled in pipeline).
# Fields may be added/removed once LLM reasoning shape is finalized.

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    claim: str
    source: str
    url: str | None = None
    confidence: Literal['high', 'medium', 'low'] | None = None
    source_type: Literal['internal', 'supplier', 'regulator', 'industry'] | None = None


class ComplianceRequirement(BaseModel):
    label: str
    status: Literal['met', 'gap', 'partial']
    note: str | None = None


class Tradeoffs(BaseModel):
    gained: list[str]
    atRisk: list[str]


class RolloutPlan(BaseModel):
    affected_skus: list[str]
    timeline: str


class Proposal(BaseModel):
    id: int
    kind: Literal['optimization', 'substitution']
    headline: str
    summary: str
    raw_material_id: int
    proposed_action: str
    companies_involved: list[int]
    current_suppliers: list[int]
    proposed_supplier_id: int | None = None
    proposed_substitute_raw_material_id: int | None = None
    fragmentation_score: int
    tradeoffs: Tradeoffs
    conservative: RolloutPlan
    aggressive: RolloutPlan
    evidence: list[EvidenceItem]
    estimated_impact: str
    compliance_requirements: list[ComplianceRequirement]
