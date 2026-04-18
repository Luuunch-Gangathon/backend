from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import companies, products, raw_materials, suppliers
from app.agents.controller import controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    await controller.initialize()
    yield


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
