"""Integration test: pgvector → check_compliance → returned proposals.

Proves the end-to-end path:
  seed embeddings → find_similar_raw_materials → check_compliance → list[SubstituteProposal]

OpenAI is monkey-patched; Postgres is real (pgvector).
All tests use the transactional `seed` fixture — auto-rollback, no cleanup.

Note: check_compliance returns proposals but does not persist to substitutions table.
DB persistence is handled by callers (e.g. api/compliance.py endpoint).
"""
from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents import compliance
from app.agents.compliance import _RankingResponse
from app.schemas.compliance import SubstituteProposal
from app.data import repo
from tests.conftest import emb

_CO   = 820001
_FG   = 820001
_BOM  = 820001
_S    = 920001   # source raw material
_N1   = 920002   # near substitute 1
_N2   = 920003   # near substitute 2


async def _setup(seed) -> None:
    await seed.company(_CO)
    await seed.product(_FG, "FG-PIPE-TEST", _CO, type_="finished-good")
    await seed.bom(_BOM, _FG)

    await seed.product(_S,  "rm-pipe-source", _CO)
    await seed.bom_component(_BOM, _S)
    await seed.raw_material_map(_S, "rm-pipe-source", _CO, _FG)
    await seed.substitution_group("rm-pipe-source", emb(1.0, 0.0))

    cos1 = 0.92
    await seed.product(_N1, "rm-pipe-near1", _CO)
    await seed.raw_material_map(_N1, "rm-pipe-near1", _CO, _FG)
    await seed.substitution_group("rm-pipe-near1", emb(cos1, math.sqrt(1 - cos1**2)))

    cos2 = 0.80
    await seed.product(_N2, "rm-pipe-near2", _CO)
    await seed.raw_material_map(_N2, "rm-pipe-near2", _CO, _FG)
    await seed.substitution_group("rm-pipe-near2", emb(cos2, math.sqrt(1 - cos2**2)))


def _make_stub_client(sub_ids: list[int]) -> MagicMock:
    stub_response = MagicMock()
    stub_response.choices[0].message.parsed = _RankingResponse(
        substitutes=[
            SubstituteProposal(id=sid, score=90, reasoning="Good match")
            for sid in sub_ids
        ]
    )
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse = AsyncMock(return_value=stub_response)
    return mock_client


async def test_check_compliance_returns_proposals(seed) -> None:
    await _setup(seed)

    mock_client = _make_stub_client([_N1, _N2])

    with patch.object(compliance, "_client", mock_client):
        results = await compliance.check_compliance(_FG, _S)

    assert len(results) == 2
    for r in results:
        assert r.score == 90
        assert r.reasoning == "Good match"
        assert r.id in (_N1, _N2)


async def test_rm_without_similar_is_noop(seed) -> None:
    """Source rm with no pgvector neighbours above threshold → no LLM call, empty result."""
    await seed.company(_CO)
    await seed.product(_FG, "FG-PIPE-TEST", _CO, type_="finished-good")
    await seed.bom(_BOM, _FG)
    await seed.product(_S,  "rm-pipe-source", _CO)
    await seed.bom_component(_BOM, _S)
    await seed.raw_material_map(_S, "rm-pipe-source", _CO, _FG)
    # No substitution_group → no embedding → find_similar returns []

    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse = AsyncMock(side_effect=AssertionError("LLM called unexpectedly"))

    with patch.object(compliance, "_client", mock_client):
        result = await compliance.check_compliance(_FG, _S)

    mock_client.beta.chat.completions.parse.assert_not_called()
    assert result == []
