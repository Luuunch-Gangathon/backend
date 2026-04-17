"""Load JSON fixtures into Pydantic models once at import time."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import (
    ComplianceResult,
    ConsolidationGroup,
    EvidenceBundle,
    Ingredient,
    Supplier,
)

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def _load(name: str):
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


INGREDIENTS: list[Ingredient] = [
    Ingredient.model_validate(row) for row in _load("ingredients.json")
]

SUPPLIERS_BY_INGREDIENT: dict[str, list[Supplier]] = {
    ingredient_id: [Supplier.model_validate(row) for row in suppliers]
    for ingredient_id, suppliers in _load("suppliers.json").items()
}

CONSOLIDATION_GROUPS: list[ConsolidationGroup] = [
    ConsolidationGroup.model_validate(row) for row in _load("consolidation_groups.json")
]

EVIDENCE_BUNDLE: EvidenceBundle = EvidenceBundle.model_validate(_load("evidence.json"))

COMPLIANCE_RESULT: ComplianceResult = ComplianceResult.model_validate(
    _load("compliance.json")
)
