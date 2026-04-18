"""Data models for enrichment results."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class PropertyResult(BaseModel):
    """A single enriched property value with provenance."""

    value: Any
    confidence: Literal["verified", "probable", "inferred", "unknown"]
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    raw_excerpt: Optional[str] = None


class EnrichmentResult(BaseModel):
    """Full enrichment output for one material."""

    material_id: str
    raw_sku: str
    normalized_name: str
    company_id: str
    supplier_ids: list[str]
    enriched_at: str
    completeness: int
    total_properties: int
    properties: dict[str, PropertyResult]
