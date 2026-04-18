"""Controller — facade over all agents.

Routers import only this module. No router touches agents or repo directly.

Responsibilities:
  - initialize(): runs at startup, triggers SearchEngine enrichment for all raw materials
  - get_company / get_product / get_raw_material / get_supplier: serve UI requests
    by reading from DB and delegating to agents as needed
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
        """Called once on app startup.

        Fetches all raw materials and triggers SearchEngine enrichment for each.
        Fire-and-forget per item — enrichment writes directly to DB.
        """
        raw_materials = repo.list_raw_materials()
        logger.info("Controller.initialize: enriching %d raw materials", len(raw_materials))
        for rm in raw_materials:
            try:
                await self.search_engine.enrich(rm)
            except Exception:
                logger.exception("SearchEngine.enrich failed for %s", rm.id)

    # ------------------------------------------------------------------
    # Companies
    # ------------------------------------------------------------------

    def list_companies(self) -> list[Company]:
        return repo.list_companies()

    def get_company(self, company_id: str) -> Optional[CompanyDetail]:
        return repo.get_company(company_id)

    def list_products_by_company(self, company_id: str) -> list[FinishedGood]:
        return repo.list_products_by_company(company_id)

    # ------------------------------------------------------------------
    # Products (finished goods)
    # ------------------------------------------------------------------

    def get_product(self, product_id: str) -> Optional[FinishedGoodDetail]:
        return repo.get_product(product_id)

    # ------------------------------------------------------------------
    # Raw materials
    # ------------------------------------------------------------------

    def list_raw_materials(
        self,
        name: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> list[RawMaterial]:
        return repo.list_raw_materials(name=name, company_id=company_id)

    def get_raw_material(self, rm_id: str) -> Optional[RawMaterialDetail]:
        detail = repo.get_raw_material(rm_id)
        if detail is None:
            return None

        # Augment with substitution candidates from SubstitutionAgent
        substitute_ids = self.substitution_agent.get_substitutes(
            rm_id=rm_id,
            canonical_name=detail.canonical_name,
        )
        detail.substitute_ids = substitute_ids
        return detail

    # ------------------------------------------------------------------
    # Suppliers
    # ------------------------------------------------------------------

    def list_suppliers(self) -> list[Supplier]:
        return repo.list_suppliers()

    def get_supplier(self, supplier_id: str) -> Optional[SupplierDetail]:
        return repo.get_supplier(supplier_id)


# Singleton — import this everywhere
controller = Controller()
