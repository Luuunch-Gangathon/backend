"""Pipeline — embedding backfill on startup.

Ensures every raw material in raw_material_map has a name-only embedding
in substitution_groups so the search tool works out of the box.

Gated by SKIP_EMBED_BACKFILL=1 for fast local dev.
"""

from __future__ import annotations
import logging
import os

from app.data import rag

logger = logging.getLogger(__name__)


async def run_embedding_backfill() -> None:
    """Embed all raw material names that are missing embeddings.

    Off by default — set RUN_EMBED_BACKFILL=1 to enable.
    """
    if os.environ.get("RUN_EMBED_BACKFILL") != "1":
        logger.info("Pipeline: embedding backfill skipped (set RUN_EMBED_BACKFILL=1 to enable)")
        return

    names = await rag.get_unembedded_names()
    if not names:
        logger.info("Pipeline: no unembedded names — backfill not needed")
        return

    logger.info("Pipeline: backfilling %d name-only embeddings", len(names))
    ok = 0
    for name in names:
        try:
            await rag.store_name_only_embedding(name)
            ok += 1
        except Exception:
            logger.exception("Pipeline: failed to embed %r — skipping", name)

    logger.info("Pipeline: backfill done — %d/%d embedded", ok, len(names))
