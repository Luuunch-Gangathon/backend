# Search Engine Sources — TODO

## Supplier Website Handler

- [ ] **Improve product page discovery for B2B suppliers** — Ashland/Colorcon return PDFs and generic articles instead of product pages. Explore: trying the supplier's own site search (/search?q=...), looking for product catalog pages, or accepting that B2B suppliers won't have scrapable pages and documenting this as a known limitation.

- [ ] **Add DDG rate-limit retry logic** — DuckDuckGo can rate-limit or throw errors on rapid queries. Add exponential backoff retry (2-3 attempts) in search(), or switch to serper.dev as fallback.

- [ ] **Cache extraction results per material** — Re-running enrichment on the same material currently re-crawls and re-extracts. Cache results (e.g. in SQLite or JSON file keyed by material_name + supplier_domain) so repeat runs skip the LLM call if data already exists.

## Static Dataset Handlers

- [ ] **FDA EAFUS** — Download CSV from https://www.cfsanappsexternal.fda.gov/scripts/fdcc/?set=FoodSubstances, load into local SQLite or in-memory dict at startup. Provides: regulatory_status (GRAS status, regulatory citations). ~10K substances.

- [ ] **EFSA Food Additives DB** — Download CSV from EFSA, load at startup. Provides: regulatory_status (EU-approved, permitted uses, E-numbers). ~350 authorized additives.

## Engine — Handler Result Caching (DONE)

- [x] **Cache handler results within a single enrichment run** — Implemented in engine.py via `_handler_cache`.

## API Fixes

- [ ] **NIH DSLD endpoint returning empty responses** — Every DSLD call fails with `JSONDecodeError: line 1 column 1`. The API is returning HTML or empty body instead of JSON. The endpoint URL (`api.ods.od.nih.gov/dsld/v9/products`) likely changed. Research current DSLD API docs and update the endpoint.

- [ ] **Open Food Facts 503 errors** — OFF returns `503 Service Temporarily Unavailable` intermittently. Add retry with backoff (1-2 retries), or respect rate limits more carefully (currently no delay between calls).

## Retail Page Handler

- [ ] **retail_page** — Web scraping + LLM extraction from retail/marketplace pages (iHerb, Amazon, etc.). Similar architecture to supplier_website handler. Trust tier: probable. Provides: * (any property).

## New Source Ideas (from 2026-04-18 test of 10 materials)

Test showed only `openfda` (10/10) and `llm_knowledge` reliably produce data. All other verified sources failed or returned nothing. Key ideas:

- [ ] **USDA FoodData Central API** — Free, no key needed. Covers functional role, allergens, dietary info for thousands of food ingredients. Endpoint: `https://api.nal.usda.gov/fdc/v1/foods/search`. Trust tier: verified.

- [ ] **PubChem API** — Already commented out in config. Provides chemical_identity (CAS, formula, synonyms) and functional_role for well-known compounds. Revisit — was excluded for being slow, but could be valuable for the properties nothing else fills.

- [ ] **Rethink supplier_website product page discovery** — Current DDG `site:` search returns wrong pages (category pages, FAQs, nav menus) in 9/10 cases. The LLM extraction works great when given the right page. Ideas: search DDG for `"{material}" specifications` globally without `site:` restriction, then filter results to known supplier domains; or try the supplier's own site search (`/search?q=...`).

- [ ] **Fix open_food_facts** — 503 on every call during this test. Either the service is temporarily down or we're hitting rate limits. Add retry with backoff, or check if the endpoint URL changed.

- [ ] **Fix nih_dsld** — Empty JSON on every call. API likely changed endpoints. Research current DSLD API docs and update.

- [ ] **chebi and foodb produce nothing** — Investigate whether these handlers are functional or just stubs returning []. If the APIs exist, verify endpoint URLs and response parsing. If they don't have useful data for our materials, remove from the source list.
