"""Prune DB to benchmark scope: 5 target companies × PureBulk supplier.

Keeps only:
  - 5 target companies (Nature's Nutrition, PRIME HYDRATION+, One A Day,
    New Chapter, Liquid I.V.)
  - Their finished-good products + raw materials used in those BOMs
  - Their BOMs + bom_components (intact so composition is complete)
  - PureBulk supplier — other suppliers removed
  - supplier_products only where supplier = PureBulk AND product is kept

Clears substitution_groups and substitutions so they can be regenerated
fresh against the reduced dataset. Rebuilds raw_material_map.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/filter_for_benchmark.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from app.data import db

TARGET_COMPANIES = [
    "Nature's Nutrition",
    "PRIME HYDRATION+",
    "One A Day",
    "New Chapter",
    "Liquid I.V.",
]
TARGET_SUPPLIER = "PureBulk"


async def _resolve_company_ids(conn) -> list[int]:
    """Resolve target company names to IDs. Falls back to ILIKE match when exact fails."""
    rows = await conn.fetch(
        "SELECT id, name FROM companies WHERE name = ANY($1::text[])",
        TARGET_COMPANIES,
    )
    found = {r["name"]: r["id"] for r in rows}

    for name in TARGET_COMPANIES:
        if name in found:
            continue
        fallback = await conn.fetchrow(
            "SELECT id, name FROM companies WHERE name ILIKE $1 LIMIT 1",
            f"%{name}%",
        )
        if fallback is None:
            raise SystemExit(f"ERROR: company not found: {name!r}")
        print(f"  matched {fallback['name']!r} for target {name!r}")
        found[name] = fallback["id"]

    return list(found.values())


async def _resolve_supplier_id(conn) -> int:
    row = await conn.fetchrow(
        "SELECT id, name FROM suppliers WHERE name ILIKE $1 LIMIT 1",
        f"%{TARGET_SUPPLIER}%",
    )
    if row is None:
        raise SystemExit(f"ERROR: supplier not found: {TARGET_SUPPLIER!r}")
    print(f"  matched supplier {row['name']!r} (id={row['id']})")
    return row["id"]


async def _kept_product_ids(conn, company_ids: list[int]) -> list[int]:
    rows = await conn.fetch(
        """
        WITH fg AS (
            SELECT id FROM products
            WHERE company_id = ANY($1::int[]) AND type = 'finished-good'
        ),
        used_rm AS (
            SELECT DISTINCT bc.consumed_product_id AS id
            FROM boms b
            JOIN bom_components bc ON bc.bom_id = b.id
            WHERE b.produced_product_id IN (SELECT id FROM fg)
        )
        SELECT id FROM fg
        UNION
        SELECT id FROM used_rm
        """,
        company_ids,
    )
    return [r["id"] for r in rows]


async def main() -> None:
    await db.init_pool()
    try:
        async with db.get_conn() as conn:
            async with conn.transaction():
                print("Resolving target companies...")
                company_ids = await _resolve_company_ids(conn)
                print(f"  {len(company_ids)} companies selected")

                print("Resolving target supplier...")
                supplier_id = await _resolve_supplier_id(conn)

                print("Collecting product IDs to keep...")
                kept_ids = await _kept_product_ids(conn, company_ids)
                print(f"  {len(kept_ids)} products to keep (finished-goods + raw materials in their BOMs)")

                print("Clearing derived tables (substitutions, substitution_groups, raw_material_map)...")
                await conn.execute("TRUNCATE substitutions RESTART IDENTITY CASCADE")
                await conn.execute("TRUNCATE substitution_groups RESTART IDENTITY CASCADE")
                await conn.execute("TRUNCATE raw_material_map RESTART IDENTITY CASCADE")

                print("Deleting bom_components outside scope...")
                await conn.execute(
                    """
                    DELETE FROM bom_components
                    WHERE bom_id IN (
                        SELECT id FROM boms WHERE produced_product_id <> ALL($1::int[])
                    )
                       OR consumed_product_id <> ALL($1::int[])
                    """,
                    kept_ids,
                )

                print("Deleting BOMs outside scope...")
                await conn.execute(
                    "DELETE FROM boms WHERE produced_product_id <> ALL($1::int[])",
                    kept_ids,
                )

                print("Deleting supplier_products outside scope...")
                await conn.execute(
                    """
                    DELETE FROM supplier_products
                    WHERE supplier_id <> $1
                       OR product_id <> ALL($2::int[])
                    """,
                    supplier_id,
                    kept_ids,
                )

                print("Deleting products outside scope...")
                await conn.execute(
                    "DELETE FROM products WHERE id <> ALL($1::int[])",
                    kept_ids,
                )

                print("Deleting suppliers other than PureBulk...")
                await conn.execute("DELETE FROM suppliers WHERE id <> $1", supplier_id)

                print("Deleting companies outside target list...")
                await conn.execute(
                    "DELETE FROM companies WHERE id <> ALL($1::int[])",
                    company_ids,
                )

                print("Rebuilding raw_material_map...")
                await conn.execute("SELECT refresh_raw_material_map()")

            c = await conn.fetchval("SELECT COUNT(*) FROM companies")
            s = await conn.fetchval("SELECT COUNT(*) FROM suppliers")
            p_fg = await conn.fetchval("SELECT COUNT(*) FROM products WHERE type='finished-good'")
            p_rm = await conn.fetchval("SELECT COUNT(*) FROM products WHERE type='raw-material'")
            sp = await conn.fetchval("SELECT COUNT(*) FROM supplier_products")
            rmm = await conn.fetchval("SELECT COUNT(*) FROM raw_material_map")
            rmm_purebulk = await conn.fetchval(
                "SELECT COUNT(*) FROM raw_material_map WHERE supplier_id = $1", supplier_id
            )

            print()
            print("Benchmark dataset ready:")
            print(f"  companies:          {c}")
            print(f"  suppliers:          {s}")
            print(f"  finished-goods:     {p_fg}")
            print(f"  raw-materials:      {p_rm}")
            print(f"  supplier_products:  {sp}")
            print(f"  raw_material_map:   {rmm} total rows ({rmm_purebulk} with PureBulk)")
            print()
            print("Note: substitution_groups was cleared. Re-run enrichment to repopulate:")
            print("  - restart backend (seeds name-only embeddings)")
            print("  - POST /raw-materials/{id}/enrich for each material, or wait for scheduler")
    finally:
        await db.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
