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
from app.data import db, migration


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    await migration.run_if_empty(db._pool)
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
