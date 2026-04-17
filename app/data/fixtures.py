"""Load JSON fixtures into Pydantic models once at import time."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import Ingredient

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def _load(name: str):
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


INGREDIENTS: list[Ingredient] = [
    Ingredient.model_validate(row) for row in _load("ingredients.json")
]
