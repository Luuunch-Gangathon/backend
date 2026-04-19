"""Generate compliance_cases.json from an independent Claude oracle.

Scope: every (finished-product × raw-material) pair where the product belongs
to one of 5 target companies and the raw material is currently supplied by
PureBulk.

For each pair the script:
  1. Assembles a candidate pool (same-name matches + pgvector neighbours).
  2. Fetches enriched specs from substitution_groups.
  3. Asks Claude Haiku to rank the pool with the same 5-dimension rubric the
     evaluated engine uses (app/prompts/system/compliance.j2). Because the
     oracle is Claude and the benchmarked engine is GPT-4o, the resulting
     dataset is independent enough to produce meaningful precision/recall
     numbers when scripts/benchmark.py runs.
  4. Records the top-5 ranked IDs as expected_ids / ideal_ranking.

expected_ids is guaranteed non-empty. If the oracle returns nothing we fall
back to the raw candidate pool ordered by pgvector similarity so every case
still has ground truth to score against.

Output: knowledge/benchmark/compliance_cases.json

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/build_benchmark_dataset.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

import anthropic

from app.data import db
from app.data import repo
from app.prompts.loader import render

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

TARGET_COMPANIES = [
    "Nature's Nutrition",
    "PRIME HYDRATION+",
    "One A Day",
    "New Chapter",
    "Liquid I.V.",
]
TARGET_SUPPLIER = "PureBulk"

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "benchmark" / "compliance_cases.json"

ORACLE_MODEL = "claude-opus-4-7"
TOP_X = 5
CANDIDATE_POOL_CAP = 15
ORACLE_MAX_TOKENS = 8000


_JSON_FORMAT_HINT = (
    "\n\nReturn ONLY a JSON object with this exact shape (no markdown fences, "
    "no commentary):\n"
    '{"substitutes": [{"id": <int>, "sku": <str>, "score": <int>, '
    '"reasoning": <str>}]}\n'
    f"Include up to {TOP_X} items ordered best-first. Scores must be distinct "
    "integers in [0, 100]. Only use ids from the candidate list above."
)


def _classify_difficulty(scores: list[int], n_candidates: int, fallback_used: bool) -> str:
    if fallback_used or n_candidates < 2 or not scores:
        return "hard"
    top = scores[0]
    spread = top - scores[-1] if len(scores) > 1 else 0
    if top >= 75 and spread < 10:
        return "easy"
    if top < 60:
        return "hard"
    return "medium"


async def _candidate_pool(conn, rm_id: int, rm_name: str) -> list[dict]:
    """Return deduped candidate list with {id, sku, similarity} ordered best-first.

    Union of same-name matches (similarity=1.0 virtual) and pgvector neighbours.
    Excludes the original id. Capped at CANDIDATE_POOL_CAP.
    """
    same_name_rows = await conn.fetch(
        """
        SELECT DISTINCT p.id, p.sku
        FROM   products p
        JOIN   raw_material_map rmm ON rmm.raw_material_id = p.id
        WHERE  p.type = 'raw-material'
          AND  rmm.raw_material_name = $1
          AND  p.id <> $2
        LIMIT  $3
        """,
        rm_name,
        rm_id,
        CANDIDATE_POOL_CAP,
    )

    vector_rows = await conn.fetch(
        """
        WITH source AS (
            SELECT sg.raw_material_name, sg.embedding
            FROM   raw_material_map rmm
            JOIN   substitution_groups sg
                   ON sg.raw_material_name = rmm.raw_material_name
            WHERE  rmm.raw_material_id = $1
              AND  sg.embedding IS NOT NULL
            LIMIT  1
        )
        SELECT DISTINCT ON (rmm.raw_material_id)
               rmm.raw_material_id AS id,
               p.sku                AS sku,
               1 - (sg.embedding <=> (SELECT embedding FROM source)) AS similarity
        FROM   substitution_groups sg
        JOIN   raw_material_map    rmm ON rmm.raw_material_name = sg.raw_material_name
        JOIN   products            p   ON p.id = rmm.raw_material_id
        WHERE  sg.embedding IS NOT NULL
          AND  (SELECT embedding FROM source) IS NOT NULL
          AND  sg.raw_material_name <> (SELECT raw_material_name FROM source)
          AND  rmm.raw_material_id <> $1
        ORDER  BY rmm.raw_material_id, similarity DESC
        """,
        rm_id,
    )

    pool: dict[int, dict] = {}
    for r in same_name_rows:
        pool[r["id"]] = {"id": r["id"], "sku": r["sku"], "similarity": 1.0}

    for r in vector_rows:
        if r["id"] in pool:
            continue
        pool[r["id"]] = {"id": r["id"], "sku": r["sku"], "similarity": float(r["similarity"])}

    ranked = sorted(pool.values(), key=lambda c: c["similarity"], reverse=True)
    return ranked[:CANDIDATE_POOL_CAP]


async def _call_oracle(
    client: anthropic.AsyncAnthropic,
    original: dict,
    product: dict,
    substitutes: list[dict],
) -> list[dict]:
    """Ask Claude to rank substitutes. Returns list of {id, sku, score, reasoning}.

    Returns [] on any error or parse failure — caller handles fallback.
    """
    system_prompt = render("system/compliance")
    user_prompt = render(
        "user/compliance_rank",
        original=original,
        product=product,
        substitutes=substitutes,
        top_x=TOP_X,
    ) + _JSON_FORMAT_HINT

    try:
        response = await client.messages.create(
            model=ORACLE_MODEL,
            max_tokens=ORACLE_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        logger.warning("oracle call failed: %s", exc)
        return []

    raw_text = response.content[0].text.strip()
    if "```json" in raw_text:
        raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in raw_text:
        raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.warning("oracle JSON parse failed: %s — raw: %.200s", exc, raw_text)
        return []

    items = parsed.get("substitutes", [])
    valid_ids = {s["id"] for s in substitutes}
    ranked: list[dict] = []
    for item in items:
        rid = item.get("id")
        score = item.get("score")
        if not isinstance(rid, int) or not isinstance(score, int):
            continue
        if rid not in valid_ids:
            logger.warning("oracle hallucinated id=%s — dropping", rid)
            continue
        ranked.append(
            {
                "id": rid,
                "sku": item.get("sku", ""),
                "score": score,
                "reasoning": item.get("reasoning", ""),
            }
        )

    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:TOP_X]


async def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set — oracle requires Claude access.")
        sys.exit(1)

    await db.init_pool()
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    try:
        async with db.get_conn() as conn:
            print("Querying benchmark scope...")
            scope_rows = await conn.fetch(
                """
                SELECT DISTINCT
                    rmm.finished_product_id  AS product_id,
                    rmm.finished_product_sku AS product_sku,
                    rmm.raw_material_id      AS rm_id,
                    rmm.raw_material_sku     AS rm_sku,
                    rmm.raw_material_name    AS rm_name,
                    rmm.company_name         AS company
                FROM raw_material_map rmm
                WHERE rmm.company_name = ANY($1::text[])
                  AND rmm.supplier_name ILIKE $2
                ORDER BY rmm.company_name, rmm.raw_material_name, rmm.finished_product_sku
                """,
                TARGET_COMPANIES,
                f"%{TARGET_SUPPLIER}%",
            )
            print(f"  {len(scope_rows)} (product, raw_material) pairs in scope")

            if not scope_rows:
                print("ERROR: no data in scope — check company names and supplier presence")
                return

            cases: list[dict] = []
            seq_by_name: dict[str, int] = {}
            product_spec_cache: dict[int, dict] = {}
            fallback_count = 0

            output = {
                "version": "1.0",
                "description": (
                    "Ground-truth cases for compliance benchmark. Each case defines one "
                    "substitution scenario: which product, which raw material to replace, "
                    "and what results we expect the compliance engine to return. "
                    f"Rankings produced by an independent oracle ({ORACLE_MODEL}) applying "
                    "the 5-dimension compliance rubric over enriched product and raw-material "
                    "specs — scoped to 5 target companies (Nature's Nutrition, PRIME HYDRATION+, "
                    "One A Day, New Chapter, Liquid I.V.) where the current supplier is PureBulk."
                ),
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "oracle": {
                        "provider": "anthropic",
                        "model": ORACLE_MODEL,
                        "max_tokens": ORACLE_MAX_TOKENS,
                        "temperature": None,
                        "temperature_note": "Omitted — deprecated for claude-opus-4-7 (model is deterministic by default).",
                        "reasoning_effort": None,
                    },
                    "prompts": {
                        "system": "app/prompts/system/compliance.j2",
                        "user": "app/prompts/user/compliance_rank.j2",
                        "json_format_hint_inline": True,
                    },
                    "scope": {
                        "target_companies": TARGET_COMPANIES,
                        "target_supplier": TARGET_SUPPLIER,
                    },
                    "ranking_config": {
                        "top_x": TOP_X,
                        "candidate_pool_cap": CANDIDATE_POOL_CAP,
                    },
                },
                "cases": cases,
                "_field_reference": {
                    "case_id": "Unique string identifier. Format: '<material>-<NNN>'.",
                    "description": "Human-readable explanation of the substitution scenario.",
                    "product_id": "Integer DB id of the finished-good product.",
                    "raw_material_id": "Integer DB id of the raw material being replaced.",
                    "expected_ids": "Raw-material IDs that SHOULD appear in the top-K results. Precision/Recall/F1 computed against this set.",
                    "ideal_ranking": "expected_ids ordered best-to-worst. Used for NDCG and MRR.",
                    "difficulty": "'easy' (top≥75, spread<10), 'medium' (moderate), 'hard' (top<60, few candidates, or oracle fallback).",
                    "oracle_scores": "Per-position scores (0–100) returned by the oracle. Debug trace only — not used by the benchmark.",
                    "note": "Present only when oracle fallback was used (expected_ids seeded from raw candidates).",
                },
            }

            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

            def _flush() -> None:
                with open(OUTPUT_PATH, "w") as f:
                    json.dump(output, f, indent=2)

            _flush()  # overwrite any previous run with a fresh, empty dataset

            for i, row in enumerate(scope_rows, 1):
                rm_id = row["rm_id"]
                rm_name = row["rm_name"]
                product_id = row["product_id"]
                print(f"  [{i}/{len(scope_rows)}] {rm_name} in {row['product_sku']} ...", end=" ", flush=True)

                pool = await _candidate_pool(conn, rm_id, rm_name)
                if not pool:
                    print("no candidates — skipping")
                    continue

                all_ids = [rm_id] + [c["id"] for c in pool]
                specs = await repo.get_specs_for_raw_materials(all_ids)

                if product_id not in product_spec_cache:
                    product_spec_cache[product_id] = await repo.get_product_spec(product_id)
                product_spec = product_spec_cache[product_id]

                original = {
                    "id": rm_id,
                    "sku": row["rm_sku"],
                    "spec": specs.get(rm_id, {}),
                }
                product = {
                    "id": product_id,
                    "sku": row["product_sku"],
                    "spec": product_spec,
                }
                substitutes_payload = [
                    {"id": c["id"], "sku": c["sku"], "spec": specs.get(c["id"], {})}
                    for c in pool
                ]

                ranked = await _call_oracle(client, original, product, substitutes_payload)
                fallback_used = not ranked

                if fallback_used:
                    fallback_count += 1
                    ranked = [
                        {"id": c["id"], "sku": c["sku"], "score": 0, "reasoning": ""}
                        for c in pool[:TOP_X]
                    ]

                expected_ids = [r["id"] for r in ranked]
                oracle_scores = [r["score"] for r in ranked]

                seq_by_name[rm_name] = seq_by_name.get(rm_name, 0) + 1
                seq = seq_by_name[rm_name]

                case: dict = {
                    "case_id": f"{rm_name}-{seq:03d}",
                    "description": (
                        f"Replace {rm_name} in {row['product_sku']} "
                        f"(company: {row['company']}, current supplier: PureBulk)."
                    ),
                    "product_id": product_id,
                    "raw_material_id": rm_id,
                    "expected_ids": expected_ids,
                    "ideal_ranking": expected_ids,
                    "difficulty": _classify_difficulty(oracle_scores, len(pool), fallback_used),
                    "oracle_scores": oracle_scores,
                }
                if fallback_used:
                    case["note"] = "oracle empty — seeded from pgvector candidates"

                cases.append(case)
                _flush()

                top_score = oracle_scores[0] if oracle_scores else 0
                print(f"→ {len(expected_ids)} results, top={top_score}{' (fallback)' if fallback_used else ''}")

            easy = sum(1 for c in cases if c["difficulty"] == "easy")
            medium = sum(1 for c in cases if c["difficulty"] == "medium")
            hard = sum(1 for c in cases if c["difficulty"] == "hard")

            print()
            print(f"Wrote {len(cases)} cases to {OUTPUT_PATH}")
            print(f"  easy:     {easy}")
            print(f"  medium:   {medium}")
            print(f"  hard:     {hard}")
            print(f"  fallback: {fallback_count}  (oracle returned nothing — review manually)")
    finally:
        await db.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
