from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.api import ingredients
from app.data import db, migration


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    await migration.run_if_empty(db._pool)
    yield
    await db.close_pool()


app = FastAPI(title="Spherecast Supply Chain Co-Pilot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingredients.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
