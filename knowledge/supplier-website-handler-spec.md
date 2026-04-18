# Supplier Website Handler — Design Spec

## Overview

Replace the `supplier_website_enrich` stub with a real implementation that discovers supplier product pages via search, crawls them with crawl4ai, and extracts material properties using LLM-powered structured extraction.

## Flow

```
supplier_website_enrich(name, context)
│
├─ 1. Get supplier names from context.supplier_ids → DB lookup
│
├─ 2. For each supplier:
│     ├─ Resolve supplier domain (cached after first lookup)
│     │   └─ DuckDuckGo: "{supplier_name} official website"
│     ├─ Find product page
│     │   └─ DuckDuckGo: "{material_name} site:{domain}"
│     ├─ Crawl product page with crawl4ai → markdown
│     ├─ LLM extraction with Pydantic schema
│     │   └─ Includes verification: "is this page about {material_name}?"
│     └─ If valid → convert to handler result format, return
│
└─ 3. Return properties found (or empty list if nothing found)
```

## Components

### search_utils.py — Search + domain cache

**`search(query, max_results=3) -> list[dict]`**
- Wraps `duckduckgo-search` behind a clean interface
- Returns list of `{"title": str, "url": str, "snippet": str}`
- Swappable to serper.dev or Google if DDG gets rate-limited

**`get_supplier_domain(supplier_name) -> str | None`**
- Searches `"{supplier_name}" official website`
- Extracts domain from top result URL
- Caches result in module-level dict (domain discovery happens at most 40 times)
- Returns None if supplier can't be found

**`find_product_page(material_name, domain) -> str | None`**
- Searches `"{material_name}" site:{domain}`
- Returns top result URL, or None if no results

### supplier_website.py — Handler implementation

**`MaterialProperties` Pydantic model** (extraction schema):
```python
class MaterialProperties(BaseModel):
    is_correct_material: bool
    chemical_identity: dict | None = None
    functional_role: list[str] | None = None
    source_origin: str | None = None
    dietary_flags: dict | None = None
    allergens: dict | None = None
    certifications: list[str] | None = None
    regulatory_status: dict | None = None
    form_grade: dict | None = None
    price: str | None = None
```

**`_crawl_and_extract(url, material_name) -> MaterialProperties | None`**
- Async function using crawl4ai AsyncWebCrawler
- Uses LLMExtractionStrategy with:
  - Provider: `anthropic/claude-sonnet-4-20250514` (via litellm)
  - Schema: MaterialProperties.model_json_schema()
  - Instruction: extract properties for the specified material, return null if wrong page
- Returns None if extraction fails or `is_correct_material` is false

**`supplier_website_enrich(name, context) -> list[dict]`**
- Sync wrapper (uses asyncio.run internally)
- Gets supplier IDs from context, resolves names from DB
- For each supplier: resolve domain → find product page → crawl and extract
- Converts MaterialProperties fields to handler result format:
  ```python
  [
      {"property": "chemical_identity", "value": {...}, "source_url": "https://...", "raw_excerpt": "..."},
      {"property": "allergens", "value": {...}, "source_url": "https://...", "raw_excerpt": "..."},
      ...
  ]
  ```
- Stops at first supplier that returns results (don't query all suppliers)

### Supplier name resolution

The context has `supplier_ids` like `["sup_db_12", "sup_db_7"]`. We need the actual supplier names from the DB. Add a utility function:

**`get_supplier_names(supplier_ids) -> list[str]`**
- Queries `SELECT Name FROM Supplier WHERE Id IN (...)` from the SQLite DB
- Strips the `sup_db_` prefix to get the raw DB ID

### handlers.py changes

Replace the stub:
```python
# Before
def supplier_website_enrich(name: str, context: dict) -> list[dict]:
    return _stub(name, context)

# After
from app.api.search_engine.sources.supplier_website import supplier_website_enrich
```

## Error handling

| Scenario | Behavior |
|---|---|
| Supplier not in search results | Skip supplier, try next |
| Product page not found | Skip supplier, try next |
| Gated/login page | LLM sees no product data → nulls → skip |
| Wrong material on page | `is_correct_material: false` → skip |
| crawl4ai/LLM timeout or error | Catch exception, log, return empty list |
| DuckDuckGo rate-limited | Catch exception, return empty list |

## Async handling

crawl4ai is async-only. The handler interface is sync. Use `asyncio.run()` inside `supplier_website_enrich()`. This is fine — the engine calls handlers sequentially.

## Dependencies (new)

```
crawl4ai
duckduckgo-search
```

The Anthropic API key must be set as `ANTHROPIC_API_KEY` env var (crawl4ai reads it via litellm).

## File structure

```
app/api/search_engine/
├── handlers.py                  # registry — import real impl, remove stub
├── sources/
│   ├── __init__.py
│   ├── supplier_website.py      # handler + MaterialProperties + crawl logic
│   └── search_utils.py          # search(), get_supplier_domain(), find_product_page()
```

## Testing approach

- Mock DuckDuckGo search results and crawl4ai responses
- Test domain caching (second call should not search again)
- Test verification gate (is_correct_material=false → empty result)
- Test conversion from MaterialProperties to handler result format
- Integration test with a real PureBulk page (optional, manual)
