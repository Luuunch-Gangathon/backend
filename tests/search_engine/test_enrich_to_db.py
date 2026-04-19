# DONT TOUCH
# """Quick test: enrich 1-2 materials and verify they land in the DB."""

# import asyncio
# import json
# import logging
# import os
# import sys
# import time
# from pathlib import Path

# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.insert(0, PROJECT_ROOT)

# logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
# for name in ["crawl4ai", "httpx", "httpcore", "primp", "playwright"]:
#     logging.getLogger(name).setLevel(logging.WARNING)

# logger = logging.getLogger("test_enrich_to_db")

# # Reset cost tracker for this run
# cost_file = Path(PROJECT_ROOT) / "llm_costs.json"
# if cost_file.exists():
#     cost_file.unlink()

# from dotenv import load_dotenv
# load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# async def main():
#     from app.data import db
#     await db.init_pool()

#     try:
#         # 1. Pick materials supplied by PureBulk
#         async with db.get_conn() as conn:
#             rows = await conn.fetch(
#                 """
#                 SELECT DISTINCT rm.raw_material_name
#                 FROM raw_material_map rm
#                 JOIN suppliers s ON s.id = rm.supplier_id
#                 WHERE s.name = 'PureBulk'
#                 ORDER BY rm.raw_material_name
#                 LIMIT 10
#                 """,
#             )

#         if not rows:
#             logger.info("No PureBulk materials found.")
#             return

#         test_names = [r["raw_material_name"] for r in rows]
#         logger.info("Testing with %d PureBulk material(s): %s", len(test_names), test_names)

#         # 2. For each name, fetch raw_fields from raw_material_map and enrich+store
#         from app.agents.searchEngine import enrich_and_store, save_results_json

#         all_results = []
#         total_start = time.time()

#         for name in test_names:
#             async with db.get_conn() as conn:
#                 row = await conn.fetchrow(
#                     """
#                     SELECT raw_material_id, raw_material_sku, company_id
#                     FROM raw_material_map
#                     WHERE raw_material_name = $1
#                     LIMIT 1
#                     """,
#                     name,
#                 )
#                 supplier_rows = await conn.fetch(
#                     """
#                     SELECT DISTINCT supplier_id
#                     FROM raw_material_map
#                     WHERE raw_material_name = $1 AND supplier_id IS NOT NULL
#                     """,
#                     name,
#                 )

#             raw_fields = {
#                 "Id": row["raw_material_id"],
#                 "SKU": row["raw_material_sku"],
#                 "CompanyId": row["company_id"],
#                 "SupplierIds": [r["supplier_id"] for r in supplier_rows],
#             }

#             logger.info("=" * 60)
#             logger.info("Enriching: %s (SKU: %s)", name, raw_fields["SKU"])
#             logger.info("=" * 60)

#             start = time.time()
#             result = await enrich_and_store(raw_fields, raw_material_name=name)
#             elapsed = time.time() - start

#             filled = [p for p, v in result.properties.items() if v.confidence != "unknown"]
#             logger.info("Done in %.1fs — %d/%d properties filled", elapsed, len(filled), result.total_properties)

#             all_results.append({
#                 "raw_material_name": name,
#                 "material": result.model_dump(),
#                 "elapsed_seconds": round(elapsed, 1),
#             })

#         # 3. Save JSON for review
#         path = save_results_json(all_results)
#         logger.info("Results saved to: %s", path)

#         from app.api.search_engine.sources.cost_tracker import get_summary, _load as load_costs

#         total_elapsed = time.time() - total_start
#         costs = load_costs()

#         output = {
#             "test_run": {
#                 "materials_tested": len(test_names),
#                 "total_elapsed_seconds": round(total_elapsed, 1),
#                 "costs": {
#                     "total_usd": round(costs.get("total_cost_usd", 0), 6),
#                     "total_calls": costs.get("calls", 0),
#                     "total_input_tokens": costs.get("total_input_tokens", 0),
#                     "total_output_tokens": costs.get("total_output_tokens", 0),
#                     "by_model": costs.get("by_model", {}),
#                 },
#             },
#             "results": all_results,
#         }

#         output_path = Path(PROJECT_ROOT) / "enrichment_test_results.json"
#         with open(output_path, "w") as f:
#             json.dump(output, f, indent=2, default=str)
#         logger.info("Results saved to: %s", output_path)
#         logger.info(get_summary())

#         # 4. Verify DB writes
#         logger.info("")
#         logger.info("=" * 60)
#         logger.info("DB VERIFICATION")
#         logger.info("=" * 60)

#         async with db.get_conn() as conn:
#             for name in test_names:
#                 row = await conn.fetchrow(
#                     """
#                     SELECT raw_material_name,
#                            spec IS NOT NULL       AS has_spec,
#                            embedding IS NOT NULL   AS has_embedding,
#                            updated_at
#                     FROM substitution_groups
#                     WHERE raw_material_name = $1
#                     """,
#                     name,
#                 )
#                 if row:
#                     logger.info(
#                         "  ✓ %s — spec=%s, embedding=%s, updated_at=%s",
#                         row["raw_material_name"],
#                         row["has_spec"],
#                         row["has_embedding"],
#                         row["updated_at"],
#                     )
#                 else:
#                     logger.error("  ✗ %s — NOT FOUND in substitution_groups!", name)

#     finally:
#         await db.close_pool()


# if __name__ == "__main__":
#     asyncio.run(main())
