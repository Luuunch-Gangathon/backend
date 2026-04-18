"""Automatic SQLite → PostgreSQL migration.

Runs transparently on app startup (via lifespan in main.py).
Skipped when the database already contains data.
Can be force-run manually via `python scripts/migrate_sqlite.py`.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import asyncpg

SQLITE_PATH = Path(__file__).resolve().parents[2] / "data" / "db.sqlite"


async def run_if_empty(pool: asyncpg.Pool) -> None:
    """Migrate from SQLite if PostgreSQL has no data yet. No-op otherwise."""
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM companies")
        if count > 0:
            print("Database already populated — skipping migration.")
            return

    if not SQLITE_PATH.exists():
        print(f"No SQLite file at {SQLITE_PATH} — skipping migration.")
        return

    print("Empty database detected — running migration from SQLite...")
    await run(pool)
    print("Migration complete.")


async def run(pool: asyncpg.Pool) -> None:
    """Truncate all raw tables and repopulate from SQLite. Rebuilds raw_material_map."""
    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    TRUNCATE
                        raw_material_map,
                        supplier_products,
                        bom_components,
                        boms,
                        products,
                        companies,
                        suppliers
                    RESTART IDENTITY CASCADE
                """)

                await _copy(sqlite, conn,
                            sqlite_table="Company",
                            pg_table="companies",
                            columns=[("Id", "id"), ("Name", "name")])

                await _copy(sqlite, conn,
                            sqlite_table="Supplier",
                            pg_table="suppliers",
                            columns=[("Id", "id"), ("Name", "name")])

                await _copy(sqlite, conn,
                            sqlite_table="Product",
                            pg_table="products",
                            columns=[("Id", "id"), ("SKU", "sku"),
                                     ("CompanyId", "company_id"), ("Type", "type")])

                await _copy(sqlite, conn,
                            sqlite_table="BOM",
                            pg_table="boms",
                            columns=[("Id", "id"),
                                     ("ProducedProductId", "produced_product_id")])

                await _copy(sqlite, conn,
                            sqlite_table="BOM_Component",
                            pg_table="bom_components",
                            columns=[("BOMId", "bom_id"),
                                     ("ConsumedProductId", "consumed_product_id")])

                await _copy(sqlite, conn,
                            sqlite_table="Supplier_Product",
                            pg_table="supplier_products",
                            columns=[("SupplierId", "supplier_id"),
                                     ("ProductId", "product_id")])

                await conn.execute("SELECT refresh_raw_material_map()")
                count = await conn.fetchval("SELECT COUNT(*) FROM raw_material_map")
                print(f"  raw_material_map built — {count} rows")
    finally:
        sqlite.close()


async def _copy(
    sqlite: sqlite3.Connection,
    conn: asyncpg.Connection,
    sqlite_table: str,
    pg_table: str,
    columns: list[tuple[str, str]],
) -> None:
    sqlite_cols = [c[0] for c in columns]
    pg_cols     = [c[1] for c in columns]

    rows = sqlite.execute(
        f"SELECT {', '.join(sqlite_cols)} FROM {sqlite_table}"
    ).fetchall()

    if rows:
        placeholders = ", ".join(f"${i + 1}" for i in range(len(pg_cols)))
        query = f"INSERT INTO {pg_table} ({', '.join(pg_cols)}) VALUES ({placeholders})"
        await conn.executemany(query, [tuple(row) for row in rows])

    print(f"  {pg_table:<22} {len(rows):>6} rows")
