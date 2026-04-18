"""Verify that run_one() resolves supplier names and finds data from supplier website.

Uses the same code path as the production endpoint (search_engine.run_one → _enrich_and_embed).
Picks a PureBulk material and checks that at least one property came from supplier_website.
"""

import asyncio
import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
for name in ["crawl4ai", "httpx", "httpcore", "primp", "playwright"]:
    logging.getLogger(name).setLevel(logging.WARNING)

logger = logging.getLogger("test_supplier_website_fix")

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


async def main():
    from app.data import db
    await db.init_pool()

    try:
        # 1. Pick one PureBulk material
        async with db.get_conn() as conn:
            row = await conn.fetchrow(
                """
                SELECT DISTINCT rm.raw_material_name
                FROM raw_material_map rm
                JOIN suppliers s ON s.id = rm.supplier_id
                WHERE s.name = 'PureBulk'
                ORDER BY rm.raw_material_name
                LIMIT 1
                """,
            )

        if not row:
            logger.error("No PureBulk materials found in DB")
            return

        name = row["raw_material_name"]
        logger.info("Testing with PureBulk material: %s", name)

        # 2. Call run_one — same path as the production endpoint
        from app.agents.search_engine import run_one
        await run_one(name)

        # 3. Read back from DB and check if supplier_website filled any property
        async with db.get_conn() as conn:
            sg = await conn.fetchrow(
                "SELECT spec FROM substitution_groups WHERE raw_material_name = $1",
                name,
            )

        if not sg or not sg["spec"]:
            logger.error("FAIL — no spec found in substitution_groups for '%s'", name)
            return

        import json
        spec = json.loads(sg["spec"]) if isinstance(sg["spec"], str) else sg["spec"]

        supplier_hits = []
        for prop, data in spec.items():
            if isinstance(data, dict) and data.get("source_name") == "supplier_website":
                supplier_hits.append(prop)

        if supplier_hits:
            logger.info("PASS — supplier_website filled %d properties: %s", len(supplier_hits), supplier_hits)
        else:
            sources = {
                prop: data.get("source_name")
                for prop, data in spec.items()
                if isinstance(data, dict)
            }
            logger.error("FAIL — no properties from supplier_website. Sources: %s", sources)

    finally:
        await db.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
