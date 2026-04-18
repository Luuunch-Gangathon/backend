"""NIH DSLD (Dietary Supplement Label Database) source handler.

Queries the NIH DSLD API to retrieve dietary supplement label data, extracting
dietary flags (vegan, vegetarian) and certifications (GMP, Non-GMO, Organic,
NSF Certified) from real product labels.

API endpoint: https://api.ods.od.nih.gov/dsld/v9/products?ingredient={name}&limit=10
No authentication required.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DSLD_PRODUCTS_URL = "https://api.ods.od.nih.gov/dsld/v9/products"
_DSLD_BROWSE_URL = "https://dsld.od.nih.gov/api/ingredient"
_SOURCE_BASE = "https://dsld.od.nih.gov"

# Keywords triggering dietary flag extraction (matched case-insensitively)
_DIETARY_PATTERNS: dict[str, list[str]] = {
    "vegan": ["vegan"],
    "vegetarian": ["vegetarian"],
}

# Canonical certification labels and their trigger substrings
_CERT_PATTERNS: list[tuple[str, list[str]]] = [
    ("GMP", ["gmp", "cgmp"]),
    ("Non-GMO", ["non-gmo", "non gmo"]),
    ("Organic", ["organic"]),
    ("NSF Certified", ["nsf certified", "nsf cert"]),
]


def _extract_flags(label_claims: list[str]) -> tuple[dict[str, bool], list[str]]:
    """Parse label claim strings, returning (dietary_flags, certifications).

    Args:
        label_claims: List of free-text claim strings from a single product label.

    Returns:
        Tuple of:
            dietary_flags – dict[str, bool] for dietary keywords found.
            certifications – deduplicated list of canonical cert labels.
    """
    dietary: dict[str, bool] = {}
    cert_set: set[str] = set()

    combined = " ".join(label_claims).lower()

    for flag, patterns in _DIETARY_PATTERNS.items():
        if any(p in combined for p in patterns):
            dietary[flag] = True

    for canonical, patterns in _CERT_PATTERNS:
        if any(p in combined for p in patterns):
            cert_set.add(canonical)

    return dietary, sorted(cert_set)


def _aggregate_products(products: list[dict]) -> tuple[dict[str, bool], list[str]]:
    """Aggregate dietary flags and certifications across multiple product dicts.

    Args:
        products: List of DSLD product dicts, each expected to have a
            'labelClaims' key with a list of strings.

    Returns:
        Tuple of (dietary_flags, certifications) merged across all products.
    """
    merged_dietary: dict[str, bool] = {}
    merged_certs: set[str] = set()

    for product in products:
        claims = product.get("labelClaims", [])
        if not claims:
            continue
        dietary, certs = _extract_flags(claims)
        merged_dietary.update(dietary)
        merged_certs.update(certs)

    return merged_dietary, sorted(merged_certs)


def _fetch_products(name: str) -> list[dict] | None:
    """Query DSLD API for products containing the named ingredient.

    Tries the primary endpoint; falls back to a secondary browse endpoint if
    the primary returns no results or a non-success status.

    Returns:
        List of product dicts, empty list on 404 / no results, None on error.
    """
    # Primary endpoint
    try:
        resp = httpx.get(
            _DSLD_PRODUCTS_URL,
            params={"ingredient": name, "limit": 10},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        products: list[dict] = data.get("hits", data.get("results", []))
        if products:
            return products
    except httpx.HTTPStatusError:
        logger.warning("DSLD primary endpoint returned non-2xx for %r", name)
    except Exception:
        logger.warning("DSLD primary endpoint request failed for %r", name, exc_info=True)
        return None

    # Fallback endpoint
    try:
        resp = httpx.get(
            _DSLD_BROWSE_URL,
            params={"name": name},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("hits", data.get("results", []))
    except Exception:
        logger.warning("DSLD fallback endpoint failed for %r", name, exc_info=True)
        return None


def nih_dsld_enrich(name: str, context: dict) -> list[dict]:
    """Enrich an ingredient with dietary flags and certifications from NIH DSLD.

    Args:
        name: Ingredient / supplement name to search for.
        context: Unused by this handler (kept for interface consistency).

    Returns:
        List of up to 2 property dicts (dietary_flags, certifications).
        Returns an empty list when no products are found or on API error.
    """
    raw_products = _fetch_products(name)

    if raw_products is None:
        return []

    if not raw_products:
        logger.info("DSLD: no products found for %r", name)
        return []

    dietary_flags, certifications = _aggregate_products(raw_products)

    if not dietary_flags and not certifications:
        logger.info("DSLD: no dietary flags or certifications found for %r", name)
        return []

    source_url = f"{_SOURCE_BASE}/ingredient/{name}"
    results: list[dict] = []

    if dietary_flags:
        results.append(
            {
                "property": "dietary_flags",
                "value": dietary_flags,
                "source_url": source_url,
                "raw_excerpt": (
                    f"Dietary flags from DSLD label claims: {', '.join(dietary_flags.keys())}"
                ),
            }
        )

    if certifications:
        results.append(
            {
                "property": "certifications",
                "value": certifications,
                "source_url": source_url,
                "raw_excerpt": (
                    f"Certifications from DSLD label claims: {', '.join(certifications)}"
                ),
            }
        )

    return results
