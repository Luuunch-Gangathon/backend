from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, consolidation, enrichment, ingredients

app = FastAPI(title="Spherecast Supply Chain Co-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingredients.router)
app.include_router(consolidation.router)
app.include_router(chat.router)
app.include_router(enrichment.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
