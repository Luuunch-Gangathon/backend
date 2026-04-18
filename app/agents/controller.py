"""Controller — facade over all agents.

Routers import only this module. No router touches agents or repo directly.

Startup:
  initialize() runs once on app boot — triggers SearchEngine enrichment
  for every raw material. Fire-and-forget per item.

Request path:
  get_raw_material() reads enriched data from DB, then asks SubstitutionAgent
  for candidates before returning.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.data import repo
from app.schemas import (
    Company,
    CompanyDetail,
    FinishedGood,
    FinishedGoodDetail,
    RawMaterial,
    RawMaterialDetail,
    Supplier,
    SupplierDetail,
)
from app.agents.search_engine.search_engine import SearchEngine
from app.agents.substitution.substitution_agent import SubstitutionAgent
from app.agents.compliance.compliance_agent import ComplianceAgent

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self) -> None:
        self.search_engine = SearchEngine()
        self.substitution_agent = SubstitutionAgent()
        self.compliance_agent = ComplianceAgent()

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        raw_materials = await repo.list_raw_materials()
        logger.info("Controller.initialize: enriching %d raw materials", len(raw_materials))
        for rm in raw_materials:
            try:
                await self.search_engine.enrich(rm)
            except Exception:
                logger.exception("SearchEngine.enrich failed for %s", rm.id)

    # ------------------------------------------------------------------
    # Companies
    # ------------------------------------------------------------------

    async def list_companies(self) -> list[Company]:
        return await repo.list_companies()

    async def get_company(self, company_id: str) -> Optional[CompanyDetail]:
        return await repo.get_company(company_id)

    async def list_products_by_company(self, company_id: str) -> list[FinishedGood]:
        return await repo.list_products_by_company(company_id)

    # ------------------------------------------------------------------
    # Products (finished goods)
    # ------------------------------------------------------------------

    async def get_product(self, product_id: str) -> Optional[FinishedGoodDetail]:
        return await repo.get_product(product_id)

    # ------------------------------------------------------------------
    # Raw materials
    # ------------------------------------------------------------------

    async def list_raw_materials(
        self,
        name: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> list[RawMaterial]:
        return await repo.list_raw_materials(name=name, company_id=company_id)

    async def get_raw_material(self, rm_id: str) -> Optional[RawMaterialDetail]:
        detail = await repo.get_raw_material(rm_id)
        if detail is None:
            return None
        detail.substitute_ids = await self.substitution_agent.get_substitutes(
            rm_id=rm_id,
            canonical_name=detail.canonical_name,
        )
        return detail

    # ------------------------------------------------------------------
    # Suppliers
    # ------------------------------------------------------------------

    async def list_suppliers(self) -> list[Supplier]:
        return await repo.list_suppliers()

    async def get_supplier(self, supplier_id: str) -> Optional[SupplierDetail]:
        return await repo.get_supplier(supplier_id)


# Singleton — import this everywhere
controller = Controller()
