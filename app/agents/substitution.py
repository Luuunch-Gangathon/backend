"""SubstitutionAgent

Finds functionally equivalent raw materials and writes results to DB.

Writes to:
  - substitution_groups (spec, embedding, group_name, confidence, reasoning)
  - substitutions
"""

from __future__ import annotations

import json
import logging
import os

from openai import AsyncOpenAI

from app.data import db

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
_EMBEDDING_DIMS = 1536
_openai = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])


async def run() -> None:
    logger.info("SubstitutionAgent: started")
    # TODO: read all rows from substitution_groups that have spec but no embedding,
    # call store_embedding() for each, then run vector search to populate group_name.
    logger.info("SubstitutionAgent: done")


async def store_embedding(enriched_result: dict) -> None:
    """Build and persist the embedding for one enriched raw material.

    Called by SearchEngine after it fetches and structures spec data from the web.

    enriched_result shape:
    {
      "normalized_name": str,
      "properties": {
        "chemical_identity": { "value": {...}, ... },
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
    normalized_name = enriched_result.get("normalized_name", "").strip()
    if not normalized_name:
        raise ValueError("enriched_result must contain a non-empty 'normalized_name'")

    embedding_text = _build_embedding_text(enriched_result)
    logger.debug("SubstitutionAgent: embedding text for %r: %s", normalized_name, embedding_text[:120])

    vector = await _embed(embedding_text)
    if len(vector) != _EMBEDDING_DIMS:
        raise ValueError(f"Expected {_EMBEDDING_DIMS}-dim embedding, got {len(vector)}")

    vector_literal = "[" + ",".join(str(x) for x in vector) + "]"

    async with db.get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO substitution_groups (raw_material_name, spec, embedding, updated_at)
            VALUES ($1, $2::jsonb, $3::vector, now())
            ON CONFLICT (raw_material_name) DO UPDATE
                SET spec       = EXCLUDED.spec,
                    embedding  = EXCLUDED.embedding,
                    updated_at = now()
            """,
            normalized_name,
            json.dumps(enriched_result.get("properties", {})),
            vector_literal,
        )

    logger.info("SubstitutionAgent: stored embedding for %r", normalized_name)


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_embedding_text(result: dict) -> str:
    """Flatten spec fields into one string for embedding.

    Includes: name, synonyms, functional role, source origin, dietary flags,
    allergens, certifications, regulatory status, form/grade.
    """
    props = result.get("properties", {})
    name = result.get("normalized_name", "")
    parts: list[str] = [name]

    chem = props.get("chemical_identity", {}).get("value") or {}
    synonyms = chem.get("synonyms") or []
    if synonyms:
        parts.append("also known as: " + ", ".join(synonyms))

    func_roles = props.get("functional_role", {}).get("value") or []
    if func_roles:
        parts.append("function: " + ", ".join(func_roles))

    origin = props.get("source_origin", {}).get("value")
    if origin:
        parts.append(f"source: {origin}")

    dietary = props.get("dietary_flags", {}).get("value") or {}
    active_flags = [k for k, v in dietary.items() if v is True]
    if active_flags:
        parts.append("dietary: " + ", ".join(active_flags))

    allergen_val = props.get("allergens", {}).get("value") or {}
    contains = allergen_val.get("contains") or []
    free_from = allergen_val.get("free_from") or []
    if contains:
        parts.append("allergens: " + ", ".join(contains))
    if free_from:
        parts.append("free from: " + ", ".join(free_from))

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

    form_val = props.get("form_grade", {}).get("value") or {}
    if form_val.get("form"):
        parts.append(f"form: {form_val['form']}")
    if form_val.get("grade"):
        parts.append(f"grade: {form_val['grade']}")

    return ". ".join(parts)


async def _embed(text: str) -> list[float]:
    response = await _openai.embeddings.create(model=_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding
