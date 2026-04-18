"""Force-run the SQLite → PostgreSQL migration regardless of current DB state.

Normally migration runs automatically on app startup.
Use this script only when you need to hard-reset and repopulate from scratch.

    python scripts/migrate_sqlite.py
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.data.migration import run


async def main() -> None:
    pool = await asyncpg.create_pool(dsn=os.environ["DATABASE_URL"])
    try:
        await run(pool)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
