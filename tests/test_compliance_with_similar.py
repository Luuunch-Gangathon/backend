"""Integration test: find_similar_raw_materials → check_compliance.

Proves that the data shape produced by pgvector search is accepted by
check_compliance end-to-end, and that vector_similarity appears in the LLM prompt.
OpenAI is monkey-patched; Postgres is real (pgvector).
"""
from __future__ import annotations

import json
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents import compliance
from app.agents.compliance import _RankingResponse
from app.schemas.compliance import SubstituteProposal
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


async def test_check_compliance_accepts_similar_pairs(seed) -> None:
    await _setup(seed)

    # Real pgvector call — returns SimilarRawMaterial list with similarity_score.
    similar = await find_similar_raw_materials(f"rm_db_{_S}")
    assert len(similar) >= 2, "Expected at least 2 similar materials above 0.75 threshold"

    source_rm = await get_raw_material(_S)
    assert source_rm is not None

    product = await get_product(_FG)
    assert product is not None

    # Stub the OpenAI response.
    stub_response = MagicMock()
    stub_response.choices[0].message.parsed = _RankingResponse(
        substitutes=[SubstituteProposal(id=similar[0].raw_material_id.split("_")[-1], score=88, reasoning="Good match")]
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

    # Verify each substitute in the prompt has the expected fields.
    # Note: vector_similarity was intentionally removed — system prompt now bans LLM from using it.
    user_msg = next(m["content"] for m in captured_messages if m["role"] == "user")
    # Find the candidates JSON block — robust to wording changes in the template
    candidates_start = user_msg.index(":\n", user_msg.index("Substitute candidates")) + 2
    candidates_end = user_msg.index("\n\n", candidates_start)
    payload = json.loads(user_msg[candidates_start:candidates_end])
    assert len(payload) >= 1, "Expected at least one candidate in prompt"
    for entry in payload:
        assert "id" in entry, f"Missing id in {entry}"
        assert "sku" in entry, f"Missing sku in {entry}"
        assert "spec" in entry, f"Missing spec in {entry}"
