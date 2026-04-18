"""Pipeline — runs on startup and every hour.

Orchestrates all background agents in sequence.
Uncomment each agent line when it is ready to run.
"""

from __future__ import annotations
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.agents import substitution, proposal, compliance, search_engine, auditor

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


async def run() -> None:
    """Run full agent pipeline once."""
    logger.info("Pipeline: started")

    await _step("SubstitutionAgent", substitution.run)
    await _step("SearchEngine",      search_engine.run)
    await _step("ProposalAgent",     proposal.run)
    await _step("ComplianceAgent",   compliance.run)
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


async def _step(name: str, fn) -> None:
    try:
        await fn()
    except Exception:
        logger.exception("Pipeline: %s failed — skipping", name)
