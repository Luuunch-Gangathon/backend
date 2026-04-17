from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

SourceType = Literal["internal_db", "web", "inferred", "scraped"]


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str
    source_url: Optional[str] = None
    source_type: SourceType
    confidence: float
    snippet: Optional[str] = None


class EvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EvidenceItem]
    summary: str
