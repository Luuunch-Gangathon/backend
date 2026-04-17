from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .evidence import EvidenceBundle


class ComplianceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_id: str
    requirements: list[str]


class ComplianceResult(BaseModel):
    # ``pass`` is a Python keyword, so store the attribute as ``passed`` and
    # expose it to JSON under the contract-mandated ``pass`` key via an alias.
    # Callers must serialise with ``by_alias=True`` (the routers do this).
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    passed: bool = Field(..., alias="pass")
    requirements: list[str]
    evidence: EvidenceBundle
