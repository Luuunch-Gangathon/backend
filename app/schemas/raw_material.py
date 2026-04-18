from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class RawMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str                         # ing_db_{Product.Id}
    sku: str
    name: str                       # human-readable, derived from SKU
    canonical_name: str             # normalized ingredient name, e.g. "whey-protein-isolate"
    company_id: str
    supplier_ids: list[str]         # sup_db_{Supplier.Id}


class RawMaterialDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    sku: str
    name: str
    canonical_name: str
    company_id: str
    supplier_ids: list[str]
    used_in_product_ids: list[str]          # finished-good IDs that include this in BOM
    substitute_ids: list[str]               # other raw-material IDs that are functionally equivalent
    enriched: Optional[dict] = None         # placeholder for SearchEngine output (specs, price, certs)
