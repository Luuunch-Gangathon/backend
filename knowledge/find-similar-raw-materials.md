# `find_similar_raw_materials` — pgvector similarity search

Repo function at `app/data/repo.py:59`. Returns raw materials that are
semantically close to a given source raw material, using pgvector cosine
similarity over embeddings stored in `substitution_groups.embedding`.

## What it does

1. Accepts a raw-material id and returns a ranked list of *other* raw materials
   whose embedding is ≥ the similarity threshold.
2. Similarity is **cosine similarity** computed as `1 - (a <=> b)` where `<=>`
   is pgvector's cosine-distance operator.
3. Threshold is `SIMILARITY_THRESHOLD = 0.75` (defined at the top of `repo.py`).
   Only results with `similarity_score >= 0.75` are returned.
4. The source raw material is excluded from its own results.
5. Results are sorted **descending** by `similarity_score`.

## Input

| Param             | Type  | Notes                                                  |
| ----------------- | ----- | ------------------------------------------------------ |
| `raw_material_id` | `str` | Must match the DB-backed id pattern `rm_db_<int>`.     |

Only DB-backed ids are supported. Fixture ids (e.g. `rm_1`) and malformed
strings (`""`, `"rm_db_"`, `"rm_db_abc"`) return `[]` without hitting the DB.

## Output

```python
list[SimilarRawMaterial]
```

Where `SimilarRawMaterial` (from `app/schemas/similar_raw_material.py`) is:

```json
{
  "raw_material_id":    "rm_db_42",   // DB-id format, same namespace as input
  "similarity_score":   0.87          // float in [SIMILARITY_THRESHOLD, 1.0]
}
```

`extra="forbid"` on the Pydantic model — no additional fields allowed.

## Empty-result cases

Any of these return `[]`:

- malformed or non-DB id (`rm_db_` prefix missing or not followed by digits),
- `raw_material_id` not present in `raw_material_map`,
- source row has no matching `substitution_groups` entry (no embedding),
- no other raw materials score ≥ 0.75,
- any DB exception is swallowed → `[]` (non-raising contract).

## SQL (reference)

```sql
WITH source AS (
    SELECT sg.raw_material_name, sg.embedding
    FROM raw_material_map rmm
    JOIN substitution_groups sg
      ON sg.raw_material_name = rmm.raw_material_name
    WHERE rmm.raw_material_id = $1
    LIMIT 1
)
SELECT rmm.raw_material_id,
       1 - (sg.embedding <=> (SELECT embedding FROM source)) AS score
FROM   substitution_groups sg
JOIN   raw_material_map    rmm ON rmm.raw_material_name = sg.raw_material_name
WHERE  sg.raw_material_name <> (SELECT raw_material_name FROM source)
  AND  1 - (sg.embedding <=> (SELECT embedding FROM source)) >= $2
ORDER  BY score DESC
```

Source exclusion is by **name**, not id — so duplicate `raw_material_map` rows
that share the source's `raw_material_name` are all filtered out.

## Prerequisites (data)

- `substitution_groups` must be populated with `embedding` (vector(1536)).
  Rows are written by the agent/LLM step — a raw material with no group row
  is invisible to this function.
- `raw_material_map` joins by `raw_material_name`; the name is the canonical
  key between the two tables.

## Tests

Integration tests at `tests/test_find_similar_raw_materials.py` run against a
real Postgres (`docker compose up -d`). Each test seeds its own rows inside a
transaction that rolls back on teardown, so state never leaks between tests.
Covers: malformed ids, unknown id, missing embedding, threshold boundary
(inclusive), ordering, name-based source exclusion across duplicate rows,
and DB-unavailable → `[]`.

## Wire contract note

When this function is wired to a router, update the canonical API contract in
`../../frontend/knowledge/api-contract.md` and regenerate frontend types:

```bash
cd ../frontend && yarn gen:types
```
