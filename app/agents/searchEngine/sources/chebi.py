"""ChEBI source handler — fetch functional role classifications via OLS4.

API: https://www.ebi.ac.uk/ols4/api/
No authentication required.

Strategy:
1. Search OLS4 for the ingredient name (exact match first, fuzzy fallback).
2. From the best match extract the list of has_role IRI values in `annotation`.
3. Resolve each role IRI to a human-readable label via the OLS4 terms endpoint.
4. Return a single `functional_role` result whose value is the list of labels.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_OLS_SEARCH = "https://www.ebi.ac.uk/ols4/api/search"
_OLS_TERMS = "https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms"
_CHEBI_PAGE = "https://www.ebi.ac.uk/chebi/searchId.do?chebiId={chebi_id}"


def _get_json(url: str, params: dict | None = None) -> dict | None:
    """GET *url* with optional query *params*, return parsed JSON or None on error."""
    try:
        resp = httpx.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning("ChEBI/OLS4 returned HTTP %s for %s", resp.status_code, url)
            return None
        return resp.json()
    except httpx.RequestError as exc:
        logger.warning("ChEBI/OLS4 request error for %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.warning("ChEBI/OLS4 unexpected error for %s: %s", url, exc)
        return None


def _search(name: str, exact: bool) -> dict | None:
    """Query the OLS4 search endpoint.

    Returns the raw search response dict, or None on error.
    """
    params: dict = {
        "q": name,
        "ontology": "chebi",
        "rows": 1 if exact else 5,
    }
    if exact:
        params["exact"] = "true"
    return _get_json(_OLS_SEARCH, params=params)


def _resolve_role_label(iri: str) -> str | None:
    """Look up a ChEBI role IRI and return its label, or None on failure."""
    # OLS4 terms endpoint uses URL-encoded IRI as query param
    params = {"iri": iri}
    data = _get_json(_OLS_TERMS, params=params)
    if data is None:
        return None
    try:
        terms = data["_embedded"]["terms"]
        if terms:
            return terms[0].get("label")
    except (KeyError, TypeError, IndexError):
        pass
    return None


def _extract_first_doc(search_response: dict) -> dict | None:
    """Return the first doc from an OLS4 search response, or None."""
    try:
        docs = search_response["response"]["docs"]
        if docs:
            return docs[0]
    except (KeyError, TypeError):
        pass
    return None


def chebi_enrich(name: str, context: dict) -> list[dict]:
    """Query ChEBI via OLS4 for functional role classifications.

    Returns a single-element list with property='functional_role', or []
    when not found / all role lookups fail / API errors.
    """
    # 1. Try exact match first; fall back to fuzzy.
    doc: dict | None = None

    exact_resp = _search(name, exact=True)
    if exact_resp is not None:
        doc = _extract_first_doc(exact_resp)

    if doc is None:
        fuzzy_resp = _search(name, exact=False)
        if fuzzy_resp is not None:
            doc = _extract_first_doc(fuzzy_resp)

    if doc is None:
        return []

    # 2. Pull role IRIs from annotation.has_role.
    annotation = doc.get("annotation", {})
    role_iris: list[str] = annotation.get("has_role", [])
    if not role_iris:
        return []

    # 3. Resolve each IRI to a human-readable label.
    roles: list[str] = []
    for iri in role_iris:
        label = _resolve_role_label(iri)
        if label:
            roles.append(label)

    if not roles:
        return []

    # 4. Build result.
    chebi_id: str = doc.get("obo_id", "")        # e.g. "CHEBI:9243"
    label: str = doc.get("label", name)

    source_url = _CHEBI_PAGE.format(chebi_id=chebi_id) if chebi_id else None
    raw_excerpt = f"ChEBI: {label} — roles: {', '.join(roles)}"

    return [
        {
            "property": "functional_role",
            "value": roles,
            "source_url": source_url,
            "raw_excerpt": raw_excerpt,
        }
    ]
