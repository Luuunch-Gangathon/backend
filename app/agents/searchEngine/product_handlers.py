"""Product source handler registry.

Maps source names from product_config.PRODUCT_SOURCES to handler functions.
Same pattern as handlers.py but for finished product enrichment.
"""

from __future__ import annotations

from app.agents.searchEngine.sources.open_food_facts_product import (
    open_food_facts_product_enrich,
)
from app.agents.searchEngine.sources.openfda import (
    openfda_enrich as _openfda_enrich,
)
from app.agents.searchEngine.sources.llm_knowledge_product import (
    llm_knowledge_product_enrich,
)
from app.agents.searchEngine.sources.llm_general_fallback_product import (
    llm_general_fallback_product_enrich,
)

PRODUCT_SOURCE_HANDLERS: dict[str, callable] = {
    "open_food_facts_product": open_food_facts_product_enrich,
    "openfda_product": _openfda_enrich,
    "llm_knowledge_product": llm_knowledge_product_enrich,
    "llm_general_fallback_product": llm_general_fallback_product_enrich,
}
