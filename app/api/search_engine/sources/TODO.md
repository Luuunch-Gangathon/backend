# Search Engine Sources — TODO

## Supplier Website Handler

- [ ] **Improve product page discovery for B2B suppliers** — Ashland/Colorcon return PDFs and generic articles instead of product pages. Explore: trying the supplier's own site search (/search?q=...), looking for product catalog pages, or accepting that B2B suppliers won't have scrapable pages and documenting this as a known limitation.

- [ ] **Add DDG rate-limit retry logic** — DuckDuckGo can rate-limit or throw errors on rapid queries. Add exponential backoff retry (2-3 attempts) in search(), or switch to serper.dev as fallback.

- [ ] **Cache extraction results per material** — Re-running enrichment on the same material currently re-crawls and re-extracts. Cache results (e.g. in SQLite or JSON file keyed by material_name + supplier_domain) so repeat runs skip the LLM call if data already exists.

## Static Dataset Handlers

- [ ] **FDA EAFUS** — Download CSV from https://www.cfsanappsexternal.fda.gov/scripts/fdcc/?set=FoodSubstances, load into local SQLite or in-memory dict at startup. Provides: regulatory_status (GRAS status, regulatory citations). ~10K substances.

- [ ] **EFSA Food Additives DB** — Download CSV from EFSA, load at startup. Provides: regulatory_status (EU-approved, permitted uses, E-numbers). ~350 authorized additives.

## Engine — Handler Result Caching (HIGH PRIORITY)

- [ ] **Cache handler results within a single enrichment run** — Currently `llm_knowledge` (and any wildcard `*` handler) gets called once per unfilled property. For selenium it was called 6 times, each time returning 6-7 properties but the engine only takes the one it needs and discards the rest. Fix: cache each handler's results within `run_enrichment()` so if `llm_knowledge` already ran, reuse its results for subsequent properties. This would cut LLM costs ~6x.

## API Fixes

- [ ] **NIH DSLD endpoint returning empty responses** — Every DSLD call fails with `JSONDecodeError: line 1 column 1`. The API is returning HTML or empty body instead of JSON. The endpoint URL (`api.ods.od.nih.gov/dsld/v9/products`) likely changed. Research current DSLD API docs and update the endpoint.

- [ ] **Open Food Facts 503 errors** — OFF returns `503 Service Temporarily Unavailable` intermittently. Add retry with backoff (1-2 retries), or respect rate limits more carefully (currently no delay between calls).

## Retail Page Handler

- [ ] **retail_page** — Web scraping + LLM extraction from retail/marketplace pages (iHerb, Amazon, etc.). Similar architecture to supplier_website handler. Trust tier: probable. Provides: * (any property).
