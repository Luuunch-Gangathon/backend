# DONT TOUCH
# """Batch enrichment test — 10 materials, all handlers, save results to JSON."""

# import json
# import logging
# import os
# import sys
# import time

# # Ensure project root is on sys.path
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, PROJECT_ROOT)

# # Suppress noisy loggers
# logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
# for name in ["crawl4ai", "httpx", "httpcore", "primp", "playwright"]:
#     logging.getLogger(name).setLevel(logging.WARNING)

# logger = logging.getLogger("batch_test")

# # Reset cost tracker for this run
# from pathlib import Path
# cost_file = Path(__file__).resolve().parents[1] / "llm_costs.json"
# if cost_file.exists():
#     cost_file.unlink()

# from dotenv import load_dotenv
# load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# from app.api.search_engine import config as engine_config

# # Skip slow crawling sources — only APIs + llm_knowledge
# engine_config.SOURCES = [
#     s for s in engine_config.SOURCES
#     if s["name"] not in ("supplier_website", "retail_page", "web_search")
# ]

# # Patch the engine module's reference too
# from app.api.search_engine import engine as engine_module
# engine_module.SOURCES = engine_config.SOURCES

# logger.info("Active sources: %s", [s["name"] for s in engine_config.SOURCES])

# from app.api.search_engine import enrich
# from app.api.search_engine.sources.cost_tracker import get_summary, _load as load_costs

# TEST_MATERIALS = [
#     {"Id": 472, "SKU": "RM-C25-selenium-e14cba90", "CompanyId": 25, "SupplierIds": [19, 27]},
#     {"Id": 421, "SKU": "RM-C19-magnesium-oxide-22a42bff", "CompanyId": 19, "SupplierIds": [19, 27]},
# ]

# results = []
# total_start = time.time()

# for i, material in enumerate(TEST_MATERIALS):
#     sku = material["SKU"]
#     logger.info("=" * 60)
#     logger.info("[%d/%d] Enriching: %s", i + 1, len(TEST_MATERIALS), sku)
#     logger.info("=" * 60)

#     start = time.time()
#     try:
#         result = enrich(material)
#         elapsed = time.time() - start

#         entry = {
#             "material": result.model_dump(),
#             "elapsed_seconds": round(elapsed, 1),
#         }
#         results.append(entry)

#         filled = [p for p, v in result.properties.items() if v.confidence != "unknown"]
#         logger.info(
#             "Done: %s — %d/%d properties filled in %.1fs",
#             result.normalized_name,
#             len(filled),
#             result.total_properties,
#             elapsed,
#         )
#         for p in filled:
#             prop = result.properties[p]
#             logger.info("  %s: %s (from %s)", p, prop.confidence, prop.source_name)

#     except Exception as e:
#         elapsed = time.time() - start
#         logger.error("FAILED: %s — %s (%.1fs)", sku, str(e), elapsed)
#         results.append({
#             "material": {"raw_sku": sku, "error": str(e)},
#             "elapsed_seconds": round(elapsed, 1),
#         })

# total_elapsed = time.time() - total_start

# # Load final costs
# costs = load_costs()

# output = {
#     "test_run": {
#         "materials_tested": len(TEST_MATERIALS),
#         "total_elapsed_seconds": round(total_elapsed, 1),
#         "costs": {
#             "total_usd": round(costs.get("total_cost_usd", 0), 6),
#             "total_calls": costs.get("calls", 0),
#             "total_input_tokens": costs.get("total_input_tokens", 0),
#             "total_output_tokens": costs.get("total_output_tokens", 0),
#             "by_model": costs.get("by_model", {}),
#         },
#     },
#     "results": results,
# }

# output_path = Path(__file__).resolve().parents[1] / "enrichment_test_results.json"
# with open(output_path, "w") as f:
#     json.dump(output, f, indent=2, default=str)

# logger.info("")
# logger.info("=" * 60)
# logger.info("BATCH TEST COMPLETE")
# logger.info("=" * 60)
# logger.info("Results saved to: %s", output_path)
# logger.info("")
# logger.info(get_summary())
# logger.info("Total time: %.1fs", total_elapsed)
