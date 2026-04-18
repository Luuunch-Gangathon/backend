"""Pipeline — runs on startup and every hour.

Orchestrates all background agents in sequence.
Uncomment each agent line when it is ready to run.
"""

from __future__ import annotations
import logging
import re

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.agents import substitution, proposal, compliance, search_engine, auditor
from app.data import repo
from app.schemas import RawMaterial

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


async def run() -> None:
    """Run full agent pipeline once."""
    logger.info("Pipeline: started")

    await _step("SubstitutionAgent", substitution.run)
    await _step("SearchEngine",      search_engine.run)
    await _step("ProposalAgent",     proposal.run)

    await _run_compliance()

    await _step("AuditorAgent",      auditor.run)

    logger.info("Pipeline: done")


def start_scheduler() -> None:
    """Start hourly scheduler. Called once on app startup."""
    _scheduler.add_job(run, "interval", hours=1, id="pipeline")
    _scheduler.start()
    logger.info("Pipeline: scheduler started — runs every hour")


def stop_scheduler() -> None:
    """Stop scheduler. Called on app shutdown."""
    _scheduler.shutdown()
    logger.info("Pipeline: scheduler stopped")


async def _run_compliance() -> None:
    products = await repo.list_products()
    for product in products:
        bom = await repo.get_bom(product.id)
        if not bom:
            continue
        for rm_id in bom.consumed_raw_material_ids:
            rm = await repo.get_raw_material(rm_id)
            if not rm:
                continue
            if await repo.has_substitutions(rm.id):
                continue
            similar = await repo.find_similar_raw_materials(f"rm_db_{rm.id}")
            if not similar:
                continue
            sub_pairs: list[tuple[RawMaterial, float]] = []
            for s in similar:
                m = re.match(r"rm_db_(\d+)$", s.raw_material_id)
                if not m:
                    continue
                sub_rm = await repo.get_raw_material(int(m.group(1)))
                if sub_rm:
                    sub_pairs.append((sub_rm, s.similarity_score))
            if sub_pairs:
                await _step("ComplianceAgent", lambda p=product, r=rm, s=sub_pairs: compliance.run(p, r, s))


async def _step(name: str, fn) -> None:
    try:
        await fn()
    except Exception:
        logger.exception("Pipeline: %s failed — skipping", name)
