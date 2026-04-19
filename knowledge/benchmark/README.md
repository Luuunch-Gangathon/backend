# Compliance Benchmark

Evaluation suite for the compliance engine (`check_compliance`).

## Files

| File | Purpose |
|------|---------|
| `compliance_cases.json` | Test dataset — you populate this with real cases |
| `results.json` | Machine-readable output from last run (auto-generated) |
| `results.md` | Human-readable markdown report from last run (auto-generated) |

## How to run

```bash
cd backend
source .venv/bin/activate
python scripts/benchmark.py
```

**Requirements before running:**
- Postgres running with seeded data and embeddings
- `DATABASE_URL` set in `.env`
- `OPENAI_API_KEY` set in `.env`

## How to add test cases

Edit `compliance_cases.json`. Each case needs:

```json
{
  "case_id": "short-unique-slug-001",
  "description": "What substitution this tests and why",
  "product_id": 90,
  "raw_material_id": 123,
  "expected_ids": [456, 789],
  "ideal_ranking": [456, 789],
  "difficulty": "easy"
}
```

To find real IDs: query your DB or call `GET /products` and `GET /raw-materials`.
To know what expected results should be: run compliance manually once and record what comes back, then validate those answers.

## Metrics explained

| Metric | What it measures |
|--------|-----------------|
| **Precision@K** | Of the top-K returned substitutes, what fraction were correct? |
| **Recall@K** | Of all expected substitutes, what fraction did we find in top-K? |
| **F1@K** | Harmonic mean of Precision and Recall — balanced single score |
| **MRR** | Mean Reciprocal Rank — how quickly does a correct answer appear? 1.0 = first position |
| **NDCG@K** | Ranking quality — penalizes correct answers ranked too low |

Default K=3. Override: `python scripts/benchmark.py --k 4`

## What "pass" means

A case passes if at least one expected substitute appeared in the top-K results (recall > 0).

## Expected results shape

After running, `results.md` will look like:

```
# Compliance Benchmark Results

Run: 2026-04-18 14:30 UTC
Cases: 8 | Passed: 7 | Failed: 1

## Aggregate Metrics (K=5)
| Metric      | Score  |
|-------------|--------|
| Precision@5 | 0.8500 |
| Recall@5    | 0.8000 |
| F1@5        | 0.8242 |
| MRR         | 0.9167 |
| NDCG@5      | 0.8750 |

## By Difficulty
| Difficulty | F1   | MRR  | Passed |
|------------|------|------|--------|
| easy       | 0.95 | 1.00 | 3/3    |
| medium     | 0.82 | 0.88 | 3/4    |
| hard       | 0.60 | 0.75 | 1/1    |
```

`results.json` contains the same data plus per-case returned IDs and LLM scores, useful for further analysis.
