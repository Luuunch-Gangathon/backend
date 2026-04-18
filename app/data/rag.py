"""RAG — embedding storage for raw material specs.

Single place for all embedding logic. Any agent that needs to store or
query embeddings imports from here.

Public API:
  store_embedding(enriched_result)       — upsert spec + embedding for one material
  store_name_only_embedding(name)        — fallback when web enrichment unavailable
  get_unembedded_names()                 — names in raw_material_map with no embedding yet

Expected input shape for store_embedding:
{
  "material": {
    "normalized_name": str,
    "properties": {
      "functional_role":   { "value": [str, ...], "confidence": str, ... },
      "source_origin":     { "value": str,         "confidence": str, ... },
      "dietary_flags":     { "value": { "vegan": bool|null, "vegetarian": bool|null,
                                        "halal": bool|null, "kosher": bool|null }, ... },
      "allergens":         { "value": { "contains": [str], "free_from": [str]|null }, ... },
      "certifications":    { "value": [str]|null, ... },
      "regulatory_status": { "value": { "has_recalls": bool, "has_adverse_events": bool,
                                        "adverse_events_count": int,
                                        "recalls": [{"reason": str, "classification": str,
                                                     "date": str}] }, ... },
      "form_grade":        { "value": { "form": str|null, "grade": str|null }|null, ... },
      "price":             { "value": null, ... }   -- always null, ignored
    }
  },
  "elapsed_seconds": float
}
"""

from __future__ import annotations

import json
import logging
import os

from openai import AsyncOpenAI

from app.data import db

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
_openai: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _openai


async def store_embedding(enriched_result: dict) -> None:
    """Upsert spec + embedding for one enriched raw material.

    On conflict (same raw_material_name) always overwrites spec and embedding
    so re-running enrichment automatically refreshes stale vectors.
    """
    material = enriched_result.get("material", enriched_result)
    name = (material.get("normalized_name") or "").strip()
    if not name:
        raise ValueError("enriched_result must contain a non-empty 'normalized_name'")

    props = material.get("properties", {})
    text = _build_embedding_text(name, props)
    logger.debug("rag: embedding text for %r: %.120s", name, text)

    vector = await _embed(text)

    async with db.get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO substitution_groups (raw_material_name, spec, embedding, updated_at)
            VALUES ($1, $2, $3, now())
            ON CONFLICT (raw_material_name) DO UPDATE
                SET spec       = EXCLUDED.spec,
                    embedding  = EXCLUDED.embedding,
                    updated_at = now()
            """,
            name,
            json.dumps(props),
            vector,
        )

    logger.info("rag: stored embedding for %r", name)


async def store_name_only_embedding(name: str) -> None:
    """Fallback: embed just the raw material name when web enrichment is unavailable.

    Only inserts — never overwrites an existing embedding so a richer spec-based
    vector is never replaced by this weaker fallback.
    """
    name = name.strip()
    if not name:
        raise ValueError("name must be non-empty")

    vector = await _embed(name)

    async with db.get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO substitution_groups (raw_material_name, embedding, updated_at)
            VALUES ($1, $2, now())
            ON CONFLICT (raw_material_name) DO NOTHING
            """,
            name,
            vector,
        )

    logger.info("rag: stored name-only embedding for %r", name)


_EMBED_BATCH_SIZE = 256  # OpenAI limit is 2048 inputs; 256 is safe for long texts


async def seed_name_only_embeddings() -> int:
    """Embed any raw material names that have no embedding yet.

    Called once on startup so vector search works immediately, before the
    search engine has enriched anything. Uses ON CONFLICT DO NOTHING so richer
    spec-based vectors written later by store_embedding are never overwritten.

    Batches all names into as few OpenAI calls as possible (max 256 per call).
    Returns the number of names that were newly embedded.
    """
    names = await get_unembedded_names()
    if not names:
        logger.info("rag: all materials already have embeddings, nothing to seed")
        return 0

    logger.info("rag: seeding name-only embeddings for %d materials (batched)", len(names))

    for batch_start in range(0, len(names), _EMBED_BATCH_SIZE):
        batch = names[batch_start: batch_start + _EMBED_BATCH_SIZE]
        try:
            response = await _get_openai().embeddings.create(model=_EMBEDDING_MODEL, input=batch)
            vectors = [item.embedding for item in response.data]
        except Exception:
            logger.exception("rag: embedding batch %d failed, skipping", batch_start)
            continue

        async with db.get_conn() as conn:
            await conn.executemany(
                """
                INSERT INTO substitution_groups (raw_material_name, embedding, updated_at)
                VALUES ($1, $2, now())
                ON CONFLICT (raw_material_name) DO NOTHING
                """,
                list(zip(batch, vectors)),
            )

    logger.info("rag: seeding complete")
    return len(names)


async def get_unembedded_names() -> list[str]:
    """Return distinct raw_material_names that exist in raw_material_map
    but have no embedding in substitution_groups yet.

    SearchEngine calls this to know what still needs enrichment.
    Also catches any new materials added after the last pipeline run.
    """
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT rmm.raw_material_name
            FROM raw_material_map rmm
            LEFT JOIN substitution_groups sg
                   ON sg.raw_material_name = rmm.raw_material_name
            WHERE sg.embedding IS NULL
            ORDER BY rmm.raw_material_name
            """
        )
    return [r["raw_material_name"] for r in rows]


async def search(query: str, top_k: int = 5) -> list[dict]:
    """Semantic search over embedded raw materials.

    Embeds query, finds most similar materials in substitution_groups via
    pgvector cosine distance. Returns top_k results with name, spec, similarity.
    Returns empty list if no embeddings exist yet.
    """
    vector = await _embed(query)
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT raw_material_name,
                   spec,
                   group_name,
                   confidence,
                   reasoning,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM substitution_groups
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
            """,
            vector,
            top_k,
        )
    results = [dict(r) for r in rows]
    logger.info("rag: search %r → %d results", query[:60], len(results))
    return results


# ── private helpers ───────────────────────────────────────────────────────────

def _build_embedding_text(name: str, props: dict) -> str:
    """Flatten spec properties into one string for embedding.

    Fields used (in order): name, functional role, source origin,
    dietary flags, allergens, certifications, regulatory status, form/grade.

    Fields intentionally excluded:
      - chemical_identity: not present in enrichment output
      - price: always null
    """
    parts: list[str] = [name]

    func_roles = props.get("functional_role", {}).get("value") or []
    if func_roles:
        parts.append("function: " + ", ".join(func_roles))

    origin = props.get("source_origin", {}).get("value")
    if origin:
        parts.append(f"source: {origin}")

    dietary = props.get("dietary_flags", {}).get("value") or {}
    active = [k for k, v in dietary.items() if v is True]
    if active:
        parts.append("dietary: " + ", ".join(active))

    allergens = props.get("allergens", {}).get("value") or {}
    if allergens.get("contains"):
        parts.append("allergens: " + ", ".join(allergens["contains"]))
    if allergens.get("free_from"):
        parts.append("free from: " + ", ".join(allergens["free_from"]))

    certs = props.get("certifications", {}).get("value") or []
    if certs:
        parts.append("certifications: " + ", ".join(certs))

    reg = props.get("regulatory_status", {}).get("value") or {}
    reg_notes = []
    if reg.get("gras") is True:
        reg_notes.append("GRAS")
    elif reg.get("gras") is False:
        reg_notes.append("not GRAS")
    if reg.get("has_recalls"):
        recalls = reg.get("recalls") or []
        classes = {r["classification"] for r in recalls if r.get("classification")}
        severity = ", ".join(sorted(classes)) if classes else "unknown class"
        reg_notes.append(f"has FDA recalls ({severity})")
    if reg.get("has_adverse_events"):
        count = reg.get("adverse_events_count")
        reg_notes.append(f"has adverse events ({count} reported)" if count else "has adverse events")
    if reg_notes:
        parts.append("; ".join(reg_notes))

    form = props.get("form_grade", {}).get("value") or {}
    if form.get("form"):
        parts.append(f"form: {form['form']}")
    if form.get("grade"):
        parts.append(f"grade: {form['grade']}")

    return ". ".join(parts)


async def _embed(text: str) -> list[float]:
    response = await _get_openai().embeddings.create(model=_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding
