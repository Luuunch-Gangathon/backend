"""PubChem source handler — fetch chemical identity data via PUG REST API.

API docs: https://pubchemdocs.ncbi.nlm.nih.gov/pug-rest
Rate limit: 5 requests/second (no auth required).
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
_CAS_RE = re.compile(r"^\d+-\d+-\d+$")


def _get_json(url: str) -> dict | None:
    """GET a URL and return parsed JSON, or None on 404/error."""
    try:
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("PubChem HTTP error for %s: %s", url, exc)
        return None
    except httpx.RequestError as exc:
        logger.warning("PubChem request error for %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.warning("PubChem unexpected error for %s: %s", url, exc)
        return None


def _extract_compound_fields(
    compound: dict,
) -> tuple[int | None, str | None, float | None, str | None]:
    """Return (cid, formula, molecular_weight, iupac_name) from a PUG compound record."""
    cid: int | None = None
    formula: str | None = None
    mw: float | None = None
    iupac: str | None = None

    try:
        cid = compound["id"]["id"]["cid"]
    except (KeyError, TypeError):
        pass

    for prop in compound.get("props", []):
        label = prop.get("urn", {}).get("label", "")
        name = prop.get("urn", {}).get("name", "")
        val = prop.get("value", {})

        if label == "Molecular Formula":
            formula = val.get("sval")
        elif label == "Molecular Weight":
            mw = val.get("fval") or val.get("sval")
            if mw is not None:
                try:
                    mw = float(mw)
                except (TypeError, ValueError):
                    mw = None
        elif label == "IUPAC Name" and name == "Preferred":
            iupac = val.get("sval")

    return cid, formula, mw, iupac


def pubchem_enrich(name: str, context: dict) -> list[dict]:
    """Query PubChem PUG REST for chemical identity data.

    Returns a list with a single 'chemical_identity' result dict, or [] on
    failure / not-found.
    """
    encoded = quote(name)

    # 1. Compound record
    compound_url = f"{_BASE}/{encoded}/JSON"
    compound_data = _get_json(compound_url)
    if compound_data is None:
        return []

    compounds = compound_data.get("PC_Compounds", [])
    if not compounds:
        logger.warning("PubChem: no compounds in response for '%s'", name)
        return []

    compound = compounds[0]
    cid, formula, mw, iupac_name = _extract_compound_fields(compound)

    # 2. Synonyms (optional — don't abort if this fails)
    cas_number: str | None = None
    synonyms: list[str] = []

    synonyms_url = f"{_BASE}/{encoded}/synonyms/JSON"
    synonyms_data = _get_json(synonyms_url)
    if synonyms_data is not None:
        info_list = (
            synonyms_data.get("InformationList", {}).get("Information", [])
        )
        if info_list:
            raw_synonyms: list[str] = info_list[0].get("Synonym", [])
            synonyms = raw_synonyms
            for s in raw_synonyms:
                if _CAS_RE.match(s):
                    cas_number = s
                    break

    value: dict[str, Any] = {
        "cas_number": cas_number,
        "formula": formula,
        "molecular_weight": mw,
        "iupac_name": iupac_name,
        "synonyms": synonyms,
        "pubchem_cid": cid,
    }

    source_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else None
    return [
        {
            "property": "chemical_identity",
            "value": value,
            "source_url": source_url,
        }
    ]
