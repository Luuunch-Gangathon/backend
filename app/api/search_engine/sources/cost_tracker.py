"""Persistent LLM cost tracker.

Tracks token usage and estimated costs across all sessions.
Stores data in a JSON file at the project root.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

COST_FILE = Path(__file__).resolve().parents[4] / "llm_costs.json"

# Pricing per million tokens (as of 2025)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
}


def _load() -> dict:
    if COST_FILE.exists():
        with open(COST_FILE) as f:
            return json.load(f)
    return {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost_usd": 0.0,
        "calls": 0,
        "by_model": {},
        "history": [],
    }


def _save(data: dict) -> None:
    with open(COST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def track_usage(response, model: str, purpose: str) -> None:
    """Track an Anthropic API response's token usage and cost.

    Args:
        response: The anthropic.messages.create() response object.
        model: Model ID used (e.g. "claude-haiku-4-5-20251001").
        purpose: What the call was for (e.g. "domain_verification", "property_extraction").
    """
    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens

    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    cost = (input_tokens / 1_000_000) * pricing["input"] + \
           (output_tokens / 1_000_000) * pricing["output"]

    data = _load()
    data["total_input_tokens"] += input_tokens
    data["total_output_tokens"] += output_tokens
    data["total_cost_usd"] += cost
    data["calls"] += 1

    if model not in data["by_model"]:
        data["by_model"][model] = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "calls": 0}
    data["by_model"][model]["input_tokens"] += input_tokens
    data["by_model"][model]["output_tokens"] += output_tokens
    data["by_model"][model]["cost_usd"] += cost
    data["by_model"][model]["calls"] += 1

    data["history"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "purpose": purpose,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
    })

    _save(data)
    logger.info("LLM cost: $%.5f (%d in / %d out) — total: $%.4f (%d calls)",
                cost, input_tokens, output_tokens, data["total_cost_usd"], data["calls"])


def get_summary() -> str:
    """Return a human-readable cost summary."""
    data = _load()
    lines = [
        f"Total LLM calls: {data['calls']}",
        f"Total tokens: {data['total_input_tokens']:,} in / {data['total_output_tokens']:,} out",
        f"Total cost: ${data['total_cost_usd']:.4f}",
    ]
    for model, stats in data.get("by_model", {}).items():
        lines.append(f"  {model}: {stats['calls']} calls, ${stats['cost_usd']:.4f}")
    return "\n".join(lines)
