"""RAG — embedding storage for raw material specs.

Single place for all embedding logic. Any agent that needs to store or
query embeddings imports from here.

Public API:
  store_embedding(enriched_result)  — upsert spec + embedding for one material
  get_unembedded_names()            — names in raw_material_map with no embedding yet
"""

from __future__ import annotations

import json
import logging
import os

from openai import AsyncOpenAI

from app.data import db

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
_openai = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def store_embedding(enriched_result: dict) -> None:
    """Upsert spec + embedding for one enriched raw material.

    On conflict (same raw_material_name) always overwrites spec and embedding
    so re-running enrichment automatically refreshes stale vectors.

    enriched_result shape:
    {
      "normalized_name": str,
      "properties": {
        "chemical_identity": { "value": {...}, "confidence": str, ... },
        "functional_role":   { "value": [...], ... },
        "source_origin":     { "value": str,   ... },
        "dietary_flags":     { "value": {...}, ... },
        "allergens":         { "value": {...}, ... },
        "certifications":    { "value": [...], ... },
        "regulatory_status": { "value": {...}, ... },
        "form_grade":        { "value": {...}, ... },
      }
    }
    """
    name = enriched_result.get("normalized_name", "").strip()
    if not name:
        raise ValueError("enriched_result must contain a non-empty 'normalized_name'")

    text = _build_embedding_text(enriched_result)
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
            json.dumps(enriched_result.get("properties", {})),
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

def _build_embedding_text(result: dict) -> str:
    """Flatten spec properties into one string for embedding.

    Only uses fields relevant to functional similarity: name, synonyms,
    functional role, source origin, dietary flags, allergens, certifications,
    regulatory status, form and grade.
    """
    props = result.get("properties", {})
    parts: list[str] = [result.get("normalized_name", "")]

    chem = props.get("chemical_identity", {}).get("value") or {}
    if chem.get("synonyms"):
        parts.append("also known as: " + ", ".join(chem["synonyms"]))

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
    if reg.get("gras"):
        reg_notes.append("GRAS approved")
    if reg.get("eu_approved"):
        reg_notes.append("EU approved")
    if reg_notes:
        parts.append(", ".join(reg_notes))

    form = props.get("form_grade", {}).get("value") or {}
    if form.get("form"):
        parts.append(f"form: {form['form']}")
    if form.get("grade"):
        parts.append(f"grade: {form['grade']}")

    return ". ".join(parts)


async def _embed(text: str) -> list[float]:
    response = await _openai.embeddings.create(model=_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding
