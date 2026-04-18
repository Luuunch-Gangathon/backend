from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class SearchHit(BaseModel):
    raw_material_name: str
    raw_material_id: int | None = None
    similarity: float
    spec: dict | None = None
    companies: list[str] = []
    suppliers: list[str] = []


class ComplianceMatch(BaseModel):
    raw_material_id: int | None = None
    raw_material_name: str
    score: int          # 0–100
    reasoning: str
    similarity: float   # cosine similarity vs original
    companies_affected: list[str] = []
    suppliers: list[str] = []


class EnrichedMaterial(BaseModel):
    """Shape expected by rag.store_embedding — also used for Pydantic validation
    of web_search results before persisting."""
    normalized_name: str
    properties: dict = {}


class ToolCall(BaseModel):
    name: Literal["search", "similarity_compliance_check", "web_search_enrich"]
    arguments: dict
    result: list[SearchHit] | list[ComplianceMatch] | list[str]
