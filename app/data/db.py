"""Async PostgreSQL connection pool (asyncpg)."""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from pgvector.asyncpg import register_vector

_pool: asyncpg.Pool | None = None

_RETRY_ATTEMPTS = 10
_RETRY_DELAY = 2  # seconds


async def _init_conn(conn: asyncpg.Connection) -> None:
    await register_vector(conn)


async def init_pool() -> None:
    global _pool
    dsn = os.environ["DATABASE_URL"]
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10, init=_init_conn)
            return
        except Exception as exc:
            if attempt == _RETRY_ATTEMPTS:
                raise
            print(f"DB not ready (attempt {attempt}/{_RETRY_ATTEMPTS}): {exc} — retrying in {_RETRY_DELAY}s")
            await asyncio.sleep(_RETRY_DELAY)


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_conn() -> AsyncIterator[asyncpg.Connection]:
    if _pool is None:
        raise RuntimeError("Database pool not initialised — call init_pool() first.")
    async with _pool.acquire() as conn:
        yield conn
