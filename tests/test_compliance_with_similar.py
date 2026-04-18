"""Integration test: compare seeder → find_similar_raw_materials → compliance.run.

Proves that the data shape produced by the compare pipeline is accepted by
compliance end-to-end, and that vector_similarity appears in the LLM prompt.
OpenAI is monkey-patched; Postgres is real (pgvector).
"""
from __future__ import annotations

import json
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents import compliance
from app.agents.compliance import _RankingResponse
from app.schemas.compliance import SubstituteProposal as SubstituteScore
from app.data.repo import find_similar_raw_materials, get_product, get_raw_material
from tests.conftest import emb

_CO = 810001
_FG = 810001   # finished-good product
_S  = 910001   # source raw-material
_N1 = 910002   # near substitute 1
_N2 = 910003   # near substitute 2


async def _setup(seed) -> None:
    await seed.company(_CO)
    await seed.product(_FG, "FG-COMP-TEST", _CO, type_="finished-good")

    await seed.product(_S,  "rm-comp-source", _CO)
    await seed.raw_material_map(_S, "rm-comp-source", _CO, _FG)
    await seed.substitution_group("rm-comp-source", emb(1.0, 0.0))

    cos1 = 0.92
    await seed.product(_N1, "rm-comp-near1", _CO)
    await seed.raw_material_map(_N1, "rm-comp-near1", _CO, _FG)
    await seed.substitution_group("rm-comp-near1", emb(cos1, math.sqrt(1 - cos1**2)))

    cos2 = 0.80
    await seed.product(_N2, "rm-comp-near2", _CO)
    await seed.raw_material_map(_N2, "rm-comp-near2", _CO, _FG)
    await seed.substitution_group("rm-comp-near2", emb(cos2, math.sqrt(1 - cos2**2)))


async def test_compliance_run_accepts_similar_pairs(seed) -> None:
    await _setup(seed)

    # Real pgvector call — returns SimilarRawMaterial list with similarity_score.
    similar = await find_similar_raw_materials(f"rm_db_{_S}")
    assert len(similar) >= 2, "Expected at least 2 similar materials above 0.75 threshold"

    # Resolve to (RawMaterial, float) pairs — same as pipeline._run_compliance.
    import re
    _re = re.compile(r"rm_db_(\d+)$")
    sub_pairs = []
    for s in similar:
        m = _re.match(s.raw_material_id)
        if m:
            rm = await get_raw_material(int(m.group(1)))
            if rm:
                sub_pairs.append((rm, s.similarity_score))

    assert len(sub_pairs) >= 2

    source_rm = await get_raw_material(_S)
    assert source_rm is not None

    product = await get_product(_FG)
    assert product is not None

    # Stub the OpenAI response.
    stub_response = MagicMock()
    stub_response.choices[0].message.parsed = _RankingResponse(
        substitutes=[SubstituteScore(id=sub_pairs[0][0].id, score=88, reasoning="Good match")]
    )

    captured_messages: list = []

    async def _fake_parse(**kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return stub_response

    mock_parse = AsyncMock(side_effect=_fake_parse)
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse = mock_parse

    with patch.object(compliance, "_client", mock_client):
        await compliance.check_compliance(product.id, source_rm.id)

    mock_parse.assert_called_once()

    # Verify vector_similarity appears in the user prompt for every substitute.
    user_msg = next(m["content"] for m in captured_messages if m["role"] == "user")
    payload = json.loads(user_msg.split("Substitute candidates:\n")[1].split("\n\nReturn")[0])
    for entry in payload:
        assert "vector_similarity" in entry, f"Missing vector_similarity in {entry}"
        score = entry["vector_similarity"]
        assert 0.0 <= score <= 1.0, f"vector_similarity out of range: {score}"
