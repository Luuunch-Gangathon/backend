"""Integration tests for find_similar_raw_materials.

These tests require a running Postgres instance (docker-compose `db` service).
The suite skips automatically when Postgres is unavailable.
"""
from __future__ import annotations

import math
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest

from app.data.repo import find_similar_raw_materials
from tests.conftest import emb

# Unique negative-range IDs to avoid colliding with real data even if
# rollback misbehaves.  Company/product IDs share the same namespace.
_CO = 800001
_FG = 800001  # finished-product placeholder
_S = 900001  # raw-material product IDs start here


async def _seed_company_and_fg(seed) -> None:
    await seed.company(_CO)
    await seed.product(_FG, "FG-TEST", _CO)


async def _add_rm(seed, rm_id: int, name: str, embedding: str | None = None) -> None:
    await seed.product(rm_id, name, _CO)
    await seed.raw_material_map(rm_id, name, _CO, _FG)
    if embedding is not None:
        await seed.substitution_group(name, embedding)


# ─── Test 1: Malformed / non-DB ids ──────────────────────────────────────────


async def test_malformed_id_returns_empty(seed):
    for bad_id in ("bogus", "", "rm_1", "rm_db_", "rm_db_abc"):
        result = await find_similar_raw_materials(bad_id)
        assert result == [], f"Expected [] for id={bad_id!r}, got {result}"


# ─── Test 2: Valid DB id but no matching row ──────────────────────────────────


async def test_unknown_db_id_returns_empty(seed):
    result = await find_similar_raw_materials("rm_db_999999")
    assert result == []


# ─── Test 3: Source exists in raw_material_map but not in substitution_groups ─


async def test_source_without_embedding_returns_empty(seed):
    await _seed_company_and_fg(seed)
    # Insert into raw_material_map only — no substitution_groups row, so no embedding.
    await seed.product(_S, "rm-no-emb", _CO)
    await seed.raw_material_map(_S, "rm-no-emb", _CO, _FG)

    result = await find_similar_raw_materials(f"rm_db_{_S}")
    assert result == []


# ─── Test 4: Above/below threshold, correct ordering, source excluded ─────────


async def test_returns_similar_above_threshold_sorted(seed):
    await _seed_company_and_fg(seed)

    source_id = _S
    near_id = _S + 1
    far_id = _S + 2
    mid_id = _S + 3

    near_cos = 0.95  # ≥ 0.75 ✓
    far_cos = 0.5  # < 0.75 ✗
    mid_cos = 0.8  # ≥ 0.75 ✓

    await _add_rm(seed, source_id, "rm-source", emb(1.0, 0.0))
    await _add_rm(seed, near_id, "rm-near", emb(near_cos, math.sqrt(1 - near_cos**2)))
    await _add_rm(seed, far_id, "rm-far", emb(far_cos, math.sqrt(1 - far_cos**2)))
    await _add_rm(seed, mid_id, "rm-mid", emb(mid_cos, math.sqrt(1 - mid_cos**2)))

    results = await find_similar_raw_materials(f"rm_db_{source_id}")

    ids = [r.raw_material_id for r in results]
    assert f"rm_db_{far_id}" not in ids, "Far material (cos=0.5) should be below threshold"
    assert f"rm_db_{source_id}" not in ids, "Source should be excluded from results"
    assert f"rm_db_{near_id}" in ids
    assert f"rm_db_{mid_id}" in ids

    # Must be sorted descending by score
    assert ids.index(f"rm_db_{near_id}") < ids.index(f"rm_db_{mid_id}")

    scores = {r.raw_material_id: r.similarity_score for r in results}
    assert scores[f"rm_db_{near_id}"] == pytest.approx(near_cos, rel=1e-4)
    assert scores[f"rm_db_{mid_id}"] == pytest.approx(mid_cos, rel=1e-4)


# ─── Test 5: Source exclusion by name covers multiple raw_material_map rows ───


async def test_source_excluded_even_if_name_matches_multiple_products(seed):
    await _seed_company_and_fg(seed)

    source_id = _S
    source_dup_id = _S + 4  # second product row sharing the same name
    near_id = _S + 1

    source_emb = emb(1.0, 0.0)
    near_cos = 0.9

    await _add_rm(seed, source_id, "rm-source", source_emb)
    # Second raw_material_map row with the same name but different product id.
    await seed.product(source_dup_id, "rm-source", _CO)
    await seed.raw_material_map(source_dup_id, "rm-source", _CO, _FG)
    # substitution_groups already has "rm-source" from the first call above.

    await _add_rm(seed, near_id, "rm-near", emb(near_cos, math.sqrt(1 - near_cos**2)))

    results = await find_similar_raw_materials(f"rm_db_{source_id}")
    ids = [r.raw_material_id for r in results]

    assert f"rm_db_{source_id}" not in ids
    assert f"rm_db_{source_dup_id}" not in ids
    assert f"rm_db_{near_id}" in ids


# ─── Test 6: Threshold is inclusive (>= 0.75 included) ───────────────────────


async def test_threshold_boundary_inclusive(seed):
    await _seed_company_and_fg(seed)

    boundary_cos = 0.75
    source_id = _S
    boundary_id = _S + 5

    await _add_rm(seed, source_id, "rm-source", emb(1.0, 0.0))
    await _add_rm(
        seed,
        boundary_id,
        "rm-boundary",
        emb(boundary_cos, math.sqrt(1 - boundary_cos**2)),
    )

    results = await find_similar_raw_materials(f"rm_db_{source_id}")
    ids = [r.raw_material_id for r in results]

    assert f"rm_db_{boundary_id}" in ids, "Score exactly at 0.75 should be included (>=)"


# ─── Test 7: DB error swallowed → [] ─────────────────────────────────────────


async def test_db_unavailable_returns_empty():
    @asynccontextmanager
    async def _boom():
        raise RuntimeError("DB is down")
        yield  # make it a generator

    with patch("app.data.db.get_conn", _boom):
        result = await find_similar_raw_materials("rm_db_1")

    assert result == []
