"""SearchEngine

Enriches raw materials with specs, then upgrades their embeddings.

Two entry points:
  run_all()          — scheduled: enrich all materials that still have no spec
  run_one(rm_name)   — on-demand: enrich a single material (from chat or frontend)

Flow per material:
  Raw Material Name → searchEngine waterfall (web sources → LLM knowledge fallback)
  → rag.store_embedding()  (upserts spec + rich vector, overwrites name-only baseline)

Name-only baseline embeddings are seeded on startup by rag.seed_name_only_embeddings()
before this engine runs. store_embedding() overwrites them with richer vectors once
enrichment results are available.

The underlying searchEngine tries sources in trust-tier order:
  verified (supplier websites, ChEBI, FooDB, NIH, FDA, EFSA)
  → probable (retail pages)
  → inferred (LLM knowledge, web search)
  → speculative (LLM general fallback)

Without web access, LLM knowledge (Claude Haiku) fires automatically as the inferred
tier, giving usable spec data for embedding quality testing.

Writes to:
  - substitution_groups (spec + embedding columns via rag.store_embedding)
"""

from __future__ import annotations

import asyncio
import logging
import time
from functools import partial

from app.agents.searchEngine.engine import run_enrichment
from app.agents.searchEngine.models import EnrichmentResult
from app.data import rag

logger = logging.getLogger(__name__)


async def run_all() -> None:
    """Enrich all raw materials that have a name-only embedding but no spec yet.

    Called by the hourly pipeline scheduler. Materials added after the last run
    are caught automatically since seed_name_only_embeddings() runs on startup.
    """
    names = await rag.get_unenriched_names()
    logger.info("SearchEngine: enriching %d materials (capped at 10 for testing)", len(names))
    if not names:
        return

    ok, fail = 0, 0
    for name in names:
        try:
            await _enrich_and_embed(name)
            ok += 1
        except Exception:
            fail += 1
            logger.exception("SearchEngine: failed for %r — skipping", name)

    logger.info("SearchEngine: done — %d ok, %d failed", ok, fail)


async def run_one(raw_material_name: str) -> None:
    """Enrich and embed a single raw material. Called on-demand from chat or frontend."""
    logger.info("SearchEngine: on-demand enrich for %r", raw_material_name)
    await _enrich_and_embed(raw_material_name)
    logger.info("SearchEngine: done for %r", raw_material_name)


async def _enrich_and_embed(name: str) -> None:
    """Run the enrichment waterfall for one material, then store a rich embedding.

    run_enrichment is synchronous (blocking HTTP + LLM calls), so it runs in a
    thread executor to avoid blocking the async event loop.
    """
    t0 = time.monotonic()
    context = {
        "material_id": name,
        "raw_sku": name,
        "company_id": "unknown",
        "supplier_ids": [],
    }

    loop = asyncio.get_event_loop()
    result: EnrichmentResult = await loop.run_in_executor(
        None, partial(run_enrichment, name, context)
    )
    elapsed = time.monotonic() - t0

    enriched_result = _to_store_format(result, elapsed)
    await rag.store_embedding(enriched_result)
    logger.info(
        "SearchEngine: stored embedding for %r (completeness %d/%d, %.1fs)",
        name, result.completeness, result.total_properties, elapsed,
    )


def _to_store_format(result: EnrichmentResult, elapsed: float) -> dict:
    """Convert EnrichmentResult to the shape rag.store_embedding() expects."""
    return {
        "material": {
            "normalized_name": result.normalized_name,
            "properties": {
                prop: {
                    "value": pr.value,
                    "confidence": pr.confidence,
                    "source_name": pr.source_name,
                    "source_url": pr.source_url
                }
                for prop, pr in result.properties.items()
            },
        },
        "elapsed_seconds": elapsed,
    }
