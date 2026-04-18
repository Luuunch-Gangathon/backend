from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Supplier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str    # sup_db_{Supplier.Id}
    name: str


class SupplierDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    raw_material_ids: list[str]   # ing_db_{Product.Id} of what this supplier can provide
