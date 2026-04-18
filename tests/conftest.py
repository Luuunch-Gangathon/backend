"""Pytest fixtures for integration tests against a real Postgres instance."""
from __future__ import annotations

import math
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from unittest.mock import patch

import asyncpg
import pytest
import requests

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://spherecast:spherecast@localhost:5432/spherecast",
)

BASE_URL = "http://localhost:8000"


def emb(x: float, y: float) -> str:
    """2-D unit vector embedded in R^1536 (padded with zeros).

    cos_sim(emb(a,b), emb(c,d)) == a*c + b*d when both inputs are unit vectors.
    """
    n = math.hypot(x, y) or 1.0
    vec = [x / n, y / n] + [0.0] * 1534
    return "[" + ",".join(repr(v) for v in vec) + "]"


@pytest.fixture
async def seed():
    """Transactional seed fixture.

    Opens a single asyncpg connection, starts a transaction, patches
    app.data.db.get_conn so find_similar_raw_materials uses that same
    connection, yields a Seeder helper, then rolls back.
    """
    try:
        conn: asyncpg.Connection = await asyncpg.connect(DATABASE_URL)
    except Exception as exc:
        pytest.skip(f"Postgres not available: {exc}")

    tr = conn.transaction()
    await tr.start()

    class Seeder:
        async def company(self, id: int, name: str = "Test Co") -> None:
            await conn.execute(
                "INSERT INTO companies (id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                id,
                name,
            )

        async def product(self, id: int, sku: str, company_id: int, type_: str = "raw-material") -> None:
            await conn.execute(
                "INSERT INTO products (id, sku, company_id, type) "
                "VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                id,
                sku,
                company_id,
                type_,
            )

        async def raw_material_map(
            self,
            raw_material_id: int,
            raw_material_name: str,
            company_id: int,
            finished_product_id: int,
        ) -> None:
            await conn.execute(
                """
                INSERT INTO raw_material_map
                  (raw_material_name, company_id, company_name,
                   finished_product_id, finished_product_sku,
                   raw_material_id, raw_material_sku)
                VALUES ($1, $2, 'Test Co', $3, 'FG-TEST', $4, $1)
                """,
                raw_material_name,
                company_id,
                finished_product_id,
                raw_material_id,
            )

        async def bom(self, bom_id: int, produced_product_id: int) -> None:
            await conn.execute(
                "INSERT INTO boms (id, produced_product_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                bom_id,
                produced_product_id,
            )

        async def bom_component(self, bom_id: int, consumed_product_id: int) -> None:
            await conn.execute(
                "INSERT INTO bom_components (bom_id, consumed_product_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                bom_id,
                consumed_product_id,
            )

        async def substitution_group(
            self, raw_material_name: str, embedding: str
        ) -> None:
            await conn.execute(
                """
                INSERT INTO substitution_groups
                  (raw_material_name, group_name, confidence, embedding)
                VALUES ($1, $1, 'high', $2::vector)
                ON CONFLICT (raw_material_name)
                DO UPDATE SET embedding = EXCLUDED.embedding
                """,
                raw_material_name,
                embedding,
            )

    @asynccontextmanager
    async def _patched_get_conn() -> AsyncIterator[asyncpg.Connection]:
        yield conn

    try:
        with patch("app.data.db.get_conn", _patched_get_conn):
            yield Seeder()
    finally:
        try:
            await tr.rollback()
        finally:
            await conn.close()


@pytest.fixture(scope="session")
def api():
    """Plain HTTP session pointing at running server."""
    s = requests.Session()
    s.base_url = BASE_URL
    # Verify server is up
    r = s.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Server not running at {BASE_URL}"
    yield s
    s.close()


def get(api, path):
    return api.get(f"{api.base_url}{path}")
