"""openFDA source handler — queries FDA food endpoints for regulatory status.

Queries two endpoints:
  - food/enforcement.json  (recalls)
  - food/event.json        (adverse events)

No API key required (240 req/min unauthenticated).
Returns [] on API errors; 404 is treated as "no results" (normal).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_ENFORCEMENT_URL = "https://api.fda.gov/food/enforcement.json"
_EVENT_URL = "https://api.fda.gov/food/event.json"


def _format_date(raw: str | None) -> str | None:
    """Convert YYYYMMDD → YYYY-MM-DD. Returns None if absent or malformed."""
    if not raw or len(raw) != 8:
        return None
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def _fetch_enforcement(name: str) -> list[dict] | None:
    """Fetch recall records for *name*.

    Returns list of raw result dicts, empty list on 404, None on error.
    """
    try:
        resp = httpx.get(
            _ENFORCEMENT_URL,
            params={"search": f'"{name}"', "limit": 5},
            timeout=10,
        )
        if resp.status_code == 404:
            return []
        if resp.status_code != 200:
            logger.warning(
                "openFDA enforcement endpoint returned %s for %r",
                resp.status_code,
                name,
            )
            return None
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logger.warning("openFDA enforcement request failed for %r — %s", name, e)
        return None


def _fetch_events(name: str) -> int | None:
    """Fetch adverse event count for *name*.

    Returns count (may be 0 on 404), or None on error.
    """
    try:
        resp = httpx.get(
            _EVENT_URL,
            params={"search": f'"{name}"', "limit": 5},
            timeout=10,
        )
        if resp.status_code == 404:
            return 0
        if resp.status_code != 200:
            logger.warning(
                "openFDA event endpoint returned %s for %r",
                resp.status_code,
                name,
            )
            return None
        data = resp.json()
        return len(data.get("results", []))
    except Exception as e:
        logger.warning("openFDA event request failed for %r — %s", name, e)
        return None


def _parse_recall(raw: dict) -> dict:
    return {
        "reason": raw.get("reason_for_recall"),
        "classification": raw.get("classification"),
        "date": _format_date(raw.get("recall_initiation_date")),
    }


def openfda_enrich(name: str, context: dict) -> list[dict]:
    """Enrich a material with FDA regulatory status (recalls + adverse events).

    Returns a single-element list with property='regulatory_status', or [] on
    complete failure (both endpoints errored).
    """
    raw_recalls = _fetch_enforcement(name)   # list | None
    event_count = _fetch_events(name)        # int | None

    # If BOTH endpoints failed entirely, surface nothing rather than noise.
    if raw_recalls is None and event_count is None:
        return []

    recalls = [_parse_recall(r) for r in (raw_recalls or [])]
    adverse_count = event_count if event_count is not None else 0

    has_recalls = len(recalls) > 0
    has_adverse = adverse_count > 0

    if not has_recalls and not has_adverse:
        raw_excerpt = "No recalls or adverse events found"
    else:
        parts: list[str] = []
        if has_recalls:
            parts.append(f"{len(recalls)} recall{'s' if len(recalls) != 1 else ''}")
        if has_adverse:
            parts.append(
                f"{adverse_count} adverse event{'s' if adverse_count != 1 else ''}"
            )
        raw_excerpt = f"Found {' and '.join(parts)} for {name!r}"

    value: dict[str, Any] = {
        "recalls": recalls,
        "adverse_events_count": adverse_count,
        "has_recalls": has_recalls,
        "has_adverse_events": has_adverse,
    }

    return [
        {
            "property": "regulatory_status",
            "value": value,
            "source_url": _ENFORCEMENT_URL,
            "raw_excerpt": raw_excerpt,
        }
    ]
