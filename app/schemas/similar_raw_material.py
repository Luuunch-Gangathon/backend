from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class SimilarRawMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_material_id: str
    similarity_score: float
