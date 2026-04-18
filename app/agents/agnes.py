"""AgnesAgent — live LLM agent.

Called from POST /agnes/ask. Not part of background pipeline.
Reads proposal context from DB, calls Claude API, returns answer.

TBD: wire Claude API, add streaming, tool calls, evidence items.
"""

from __future__ import annotations
import logging
from app.data import db, repo
from app.schemas import AgnesMessage, AgnesAskResponse

logger = logging.getLogger(__name__)


async def ask(
    proposal_id: int,
    message: str,
    history: list[AgnesMessage],
) -> AgnesAskResponse:
    logger.info("AgnesAgent: started — proposal_id=%d", proposal_id)

    # TODO: implement — load proposal context, call Claude API, return answer
    proposal = await repo.get_proposal(proposal_id)
    if proposal is None:
        return AgnesAskResponse(
            reply=AgnesMessage(role="assistant", content=f"Proposal {proposal_id} not found.")
        )

    logger.info("AgnesAgent: done")
    return AgnesAskResponse(
        reply=AgnesMessage(
            role="assistant",
            content="[AgnesAgent stub] Wire Claude API in app/agents/agnes.py.",
        )
    )
