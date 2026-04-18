# Enrichment Search Engine — Design Spec

## Overview

A domain-agnostic, config-driven enrichment pipeline. Given raw material fields from the DB, it normalizes the name, queries external sources based on which properties still need filling, and writes enriched results back to the DB. Every value carries its provenance (source, URL, confidence level).

## Architecture (3 layers, fully decoupled)

```
CONFIG               ENGINE                    SOURCE HANDLERS
(what + where)  -->  (domain-agnostic loop) --> (plain functions)
```

- **Config** — sources (name, trust tier, provides[]), properties schema (flat list), confidence levels, handler mapping. Swap config to change domain.
- **Engine** — normalizes name, iterates unfilled properties, queries matching sources in trust-tier order, tags values with provenance, writes to DB. Never changes per domain.
- **Source handlers** — plain functions implementing `enrich(name, context) -> list[PropertyResult]`. Each returns whatever properties it can find.

## Config

### Properties (flat list, no priorities)

```python
PROPERTIES = [
    "chemical_identity",   # CAS number, synonyms, formula
    "functional_role",     # binder, filler, active, coating, preservative
    "source_origin",       # plant, animal, synthetic, mineral
    "dietary_flags",       # vegan, vegetarian, halal, kosher
    "allergens",           # soy, gluten, dairy, nuts, shellfish, etc.
    "certifications",      # Non-GMO, Organic, GMP, BSE/TSE Free
    "regulatory_status",   # GRAS, EU-approved, recalls
    "form_grade",          # powder, granular, liquid, capsule-grade
    "price",               # per kg/lb
]
```

### Sources (with declared capabilities)

| Source | Trust tier | Provides |
|---|---|---|
| `supplier_website` | verified | `*` |
| `pubchem` | verified | chemical_identity |
| `chebi` | verified | functional_role |
| `foodb` | verified | source_origin |
| `open_food_facts` | verified | allergens, dietary_flags, certifications |
| `nih_dsld` | verified | dietary_flags, certifications |
| `openfda` | verified | regulatory_status |
| `fda_eafus` | verified | regulatory_status |
| `efsa` | verified | regulatory_status |
| `retail_page` | probable | `*` |
| `web_search` | inferred | `*` |
| `llm_knowledge` | inferred | `*` |

### Trust tiers

```python
TRUST_TIERS = ["verified", "probable", "inferred"]
```

## Confidence model

| Level | Meaning | Assigned when |
|---|---|---|
| `verified` | Authoritative, citable | Structured APIs, supplier product page |
| `probable` | Credible, citable, not authoritative | Retail page, manufacturer TDS |
| `inferred` | Weak source or LLM-derived | Blog, forum, web search, LLM knowledge |
| `unknown` | No data found | All sources exhausted |

## Engine logic

```
def enrich(raw_material_fields: dict) -> EnrichmentResult:
    name = normalize(raw_material_fields)
    result = {}

    for property in PROPERTIES:
        if property in result:
            continue
        sources = find_sources(property, trust_order=TRUST_TIERS)
        for source in sources:
            values = SOURCE_HANDLERS[source["name"]](name, context)
            if property found in values:
                result[property] = {
                    "value": ...,
                    "confidence": source["trust_tier"],
                    "source_name": source["name"],
                    "source_url": ...,
                    "raw_excerpt": ...
                }
                break

    save_to_db(material_id, result)
    return result
```

## Result structure (per material)

```json
{
  "material_id": "ing_db_42",
  "raw_sku": "RM-C5-magnesium-stearate-a1b2c3",
  "normalized_name": "magnesium stearate",
  "company_id": "co_db_5",
  "supplier_ids": ["sup_db_12", "sup_db_7"],
  "enriched_at": "2026-04-18T02:30:00Z",
  "completeness": 8,
  "total_properties": 9,
  "properties": {
    "<property_name>": {
      "value": "...",
      "confidence": "verified|probable|inferred|unknown",
      "source_name": "pubchem",
      "source_url": "https://...",
      "raw_excerpt": "actual text the value was extracted from"
    }
  }
}
```

## Input / Output

- **In:** Raw DB fields for a material (SKU, CompanyId, SupplierId — as-is)
- **Out:** Enriched properties written to DB, each tagged with provenance

## Scalability

- New domain (packaging, labels) -> new config. Engine untouched.
- New API discovered -> write handler function, add to SOURCES config.
- Change trust order -> edit trust_tier in config.
- Cross-source validation -> future: run all tiers, flag conflicts. No architectural change.

## Implementation notes

- External API calls use stubs/mocks initially. Real integrations added incrementally.
- Name normalization is a separate module (not inlined in the engine).
- DB write layer uses a simple interface (mockable for testing).
- File location: `app/api/search_engine/search_engine.py`
