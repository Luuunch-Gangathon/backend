"""Source handler functions.

Each handler is a plain function:
    fn(name: str, context: dict) -> list[dict]

Each dict in the returned list must have:
    - property: str (which property this value is for)
    - value: Any (the property value)
    - source_url: str | None (citable URL)
    - raw_excerpt: str | None (text the value was extracted from)

All handlers are stubs returning empty lists. Replace with real
implementations one by one. The engine and config do not change.
"""

from __future__ import annotations

from app.api.search_engine.sources.supplier_website import supplier_website_enrich
from app.api.search_engine.sources.pubchem import pubchem_enrich
from app.api.search_engine.sources.open_food_facts import (
    open_food_facts_enrich as _off_enrich,
)
from app.api.search_engine.sources.openfda import (
    openfda_enrich as _openfda_enrich_real,
)
from app.api.search_engine.sources.chebi import (
    chebi_enrich as _chebi_enrich_real,
)
from app.api.search_engine.sources.nih_dsld import (
    nih_dsld_enrich as _nih_dsld_enrich_real,
)
from app.api.search_engine.sources.llm_knowledge import (
    llm_knowledge_enrich as _llm_knowledge_enrich_real,
)


def _stub(name: str, context: dict) -> list[dict]:
    """Placeholder handler — returns no results."""
    return []


def chebi_enrich(name: str, context: dict) -> list[dict]:
    return _chebi_enrich_real(name, context)


def foodb_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def open_food_facts_enrich(name: str, context: dict) -> list[dict]:
    return _off_enrich(name, context)


def nih_dsld_enrich(name: str, context: dict) -> list[dict]:
    return _nih_dsld_enrich_real(name, context)


def openfda_enrich(name: str, context: dict) -> list[dict]:
    return _openfda_enrich_real(name, context)


def fda_eafus_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def efsa_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def retail_page_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def web_search_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)


def llm_knowledge_enrich(name: str, context: dict) -> list[dict]:
    return _llm_knowledge_enrich_real(name, context)


SOURCE_HANDLERS: dict[str, callable] = {
    "supplier_website": supplier_website_enrich,
    "pubchem": pubchem_enrich,
    "chebi": _chebi_enrich_real,
    "foodb": foodb_enrich,
    "open_food_facts": open_food_facts_enrich,
    "nih_dsld": nih_dsld_enrich,
    "openfda": openfda_enrich,
    "fda_eafus": fda_eafus_enrich,
    "efsa": efsa_enrich,
    "retail_page": retail_page_enrich,
    "web_search": web_search_enrich,
    "llm_knowledge": _llm_knowledge_enrich_real,
}
