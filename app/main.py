from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import companies, products, raw_materials, suppliers, proposals, substitutions, agnes
from app.agents import pipeline
from app.agents.compliance import rank_substitutes
from app.data import db, migration
from app.schemas import RawMaterial, Product

logger = logging.getLogger(__name__)


async def _smoke_test_compliance() -> None:
    original = RawMaterial(id=1, sku="RM-001")
    subs = [
        RawMaterial(id=2, sku="RM-002"),
        RawMaterial(id=3, sku="RM-003"),
        RawMaterial(id=4, sku="RM-004"),
    ]
    product = Product(id=10, sku="FG-010", company_id=1)
    results = await rank_substitutes(original, subs, product, top_x=3)
    for r in results:
        logger.info("  [compliance smoke] id=%s score=%d — %s", r.id, r.score, r.reasoning)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    await migration.run_if_empty(db._pool)
    logger.info("Running compliance agent smoke test…")
    # await _smoke_test_compliance()
    await pipeline.run()          # run once immediately on startup
    pipeline.start_scheduler()    # then every hour
    yield
    pipeline.stop_scheduler()
    await db.close_pool()


app = FastAPI(title="Spherecast Supply Chain Co-Pilot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(products.router)
app.include_router(raw_materials.router)
app.include_router(suppliers.router)
app.include_router(proposals.router)
app.include_router(substitutions.router)
app.include_router(agnes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
