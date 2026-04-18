# Search Engine Sources — TODO

## Supplier Website Handler

- [ ] **Improve product page discovery for B2B suppliers** — Ashland/Colorcon return PDFs and generic articles instead of product pages. Explore: trying the supplier's own site search (/search?q=...), looking for product catalog pages, or accepting that B2B suppliers won't have scrapable pages and documenting this as a known limitation.

- [ ] **Add DDG rate-limit retry logic** — DuckDuckGo can rate-limit or throw errors on rapid queries. Add exponential backoff retry (2-3 attempts) in search(), or switch to serper.dev as fallback.

- [ ] **Cache extraction results per material** — Re-running enrichment on the same material currently re-crawls and re-extracts. Cache results (e.g. in SQLite or JSON file keyed by material_name + supplier_domain) so repeat runs skip the LLM call if data already exists.

## Static Dataset Handlers

- [ ] **FDA EAFUS** — Download CSV from https://www.cfsanappsexternal.fda.gov/scripts/fdcc/?set=FoodSubstances, load into local SQLite or in-memory dict at startup. Provides: regulatory_status (GRAS status, regulatory citations). ~10K substances.

- [ ] **EFSA Food Additives DB** — Download CSV from EFSA, load at startup. Provides: regulatory_status (EU-approved, permitted uses, E-numbers). ~350 authorized additives.

