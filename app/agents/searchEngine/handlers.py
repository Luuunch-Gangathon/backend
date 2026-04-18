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

from app.agents.searchEngine.sources.supplier_website import supplier_website_enrich
from app.agents.searchEngine.sources.pubchem import pubchem_enrich
from app.agents.searchEngine.sources.open_food_facts import (
    open_food_facts_enrich as _off_enrich,
)
from app.agents.searchEngine.sources.openfda import (
    openfda_enrich as _openfda_enrich_real,
)
from app.agents.searchEngine.sources.chebi import (
    chebi_enrich as _chebi_enrich_real,
)
from app.agents.searchEngine.sources.nih_dsld import (
    nih_dsld_enrich as _nih_dsld_enrich_real,
)
from app.agents.searchEngine.sources.llm_knowledge import (
    llm_knowledge_enrich as _llm_knowledge_enrich_real,
)
from app.agents.searchEngine.sources.llm_general_fallback import (
    llm_general_fallback_enrich as _llm_general_fallback_enrich_real,
)
from app.agents.searchEngine.sources.web_search import (
    web_search_enrich as _web_search_enrich_real,
)


def _stub(name: str, context: dict) -> list[dict]:
    """Placeholder handler — returns no results."""
    return []


SOURCE_HANDLERS: dict[str, callable] = {
    "supplier_website": supplier_website_enrich,
    "pubchem": pubchem_enrich,
    "chebi": _chebi_enrich_real,
    "foodb": _stub,
    "open_food_facts": _off_enrich,
    "nih_dsld": _nih_dsld_enrich_real,
    "openfda": _openfda_enrich_real,
    "fda_eafus": _stub,
    "efsa": _stub,
    "retail_page": _stub,
    "web_search": _web_search_enrich_real,
    "llm_knowledge": _llm_knowledge_enrich_real,
    "llm_general_fallback": _llm_general_fallback_enrich_real,
}
