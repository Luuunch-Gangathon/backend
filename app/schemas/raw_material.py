from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class RawMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str                         # ing_db_{Product.id}
    sku: str
    name: str                       # human-readable, derived from SKU
    canonical_name: str             # normalized, e.g. "whey-protein-isolate"
    company_id: str
    supplier_ids: list[str]         # sup_db_{Supplier.id}


class RawMaterialDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    sku: str
    name: str
    canonical_name: str
    company_id: str
    supplier_ids: list[str]
    used_in_product_ids: list[str]   # finished-good IDs that include this in BOM
    substitute_ids: list[str]        # functionally equivalent raw-material IDs
    enriched: Optional[dict] = None  # SearchEngine output: specs, price, certs
