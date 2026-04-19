# Compliance Benchmark Results

**Run:** 2026-04-19 12:53 UTC  
**K:** 5  
**Cases:** 236 | **Passed:** 138 | **Failed:** 98

## Configuration

| Component | Provider | Model | Temperature | Reasoning effort |
|-----------|----------|-------|-------------|------------------|
| Engine (benchmarked) | openai | `gpt-4o` | 0 | — |

## Aggregate Metrics (K=5)

| Metric | Score |
|--------|-------|
| Precision@5 | 0.3034 |
| Recall@5 | 0.2975 |
| F1@5 | 0.2995 |
| MRR | 0.5068 |
| NDCG@5 | 0.3359 |
| Pass Rate | 0.5847 |

## Order-Independent Set Overlap (K=5)

_Compares `returned_ids` and `expected_ids` as sets — rank order is ignored._

| Metric | Score |
|--------|-------|
| Precision@5 (set) | 0.3034 |
| Recall@5 (set) | 0.2975 |
| F1@5 (set) | 0.2995 |
| Jaccard@5 | 0.4107 |

## Order-Dependent Ranking (K=5)

_Rewards the engine for placing matches near the top of its ranking._

| Metric | Score |
|--------|-------|
| MRR | 0.5068 |
| NDCG@5 | 0.3359 |
| MAP@5 | 0.4496 |
| Hit@1 | 0.4534 |
| Hit@3 | 0.5551 |

## Excluding Errored Cases (K=5)

_Same metrics computed on **192** successful cases (excluded: 44 errored out of 236)._

| Metric | Score |
|--------|-------|
| Precision@5 | 0.3729 |
| Recall@5 | 0.3656 |
| F1@5 | 0.3681 |
| Jaccard@5 | 0.2757 |
| MRR | 0.6229 |
| NDCG@5 | 0.4129 |
| MAP@5 | 0.3235 |
| Hit@1 | 0.5573 |
| Hit@3 | 0.6823 |
| Pass Rate | 0.7188 |

## By Difficulty

| Difficulty | Precision | Recall | F1 | MRR | NDCG | Passed |
|------------|-----------|--------|-----|-----|------|--------|
| easy | 0.29 | 0.29 | 0.29 | 0.45 | 0.31 | 74/135 |
| medium | 0.32 | 0.31 | 0.31 | 0.59 | 0.37 | 64/101 |

## Per-Case Results

| Case ID | Difficulty | Precision | Recall | F1 | MRR | NDCG | Pass |
|---------|------------|-----------|--------|-----|-----|------|------|
| dipotassium-phosphate-001 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| dipotassium-phosphate-002 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| dipotassium-phosphate-003 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| dipotassium-phosphate-004 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| dipotassium-phosphate-005 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| potassium-citrate-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| potassium-citrate-002 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| potassium-citrate-003 | medium | 0.20 | 0.20 | 0.20 | 0.25 | 0.15 | ✓ |
| potassium-citrate-004 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| potassium-citrate-005 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| salt-001 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| salt-002 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| salt-003 | medium | 0.80 | 0.80 | 0.80 | 1.00 | 0.85 | ✓ |
| salt-004 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| salt-005 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| sodium-citrate-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| sodium-citrate-002 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| sodium-citrate-003 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| sodium-citrate-004 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| sodium-citrate-005 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| vitamin-b12-cyanocobalamin-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b12-cyanocobalamin-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b12-cyanocobalamin-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b12-cyanocobalamin-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b12-cyanocobalamin-005 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b3-niacinamide-001 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| vitamin-b3-niacinamide-002 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| vitamin-b3-niacinamide-003 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| vitamin-b3-niacinamide-004 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| vitamin-b3-niacinamide-005 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| vitamin-b5-d-calcium-pantothenate-001 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.85 | ✓ |
| vitamin-b5-d-calcium-pantothenate-002 | easy | 0.80 | 0.80 | 0.80 | 0.50 | 0.66 | ✓ |
| vitamin-b5-d-calcium-pantothenate-003 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-b5-d-calcium-pantothenate-004 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| vitamin-b5-d-calcium-pantothenate-005 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| vitamin-b6-pyridoxine-hydrochloride-001 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| vitamin-b6-pyridoxine-hydrochloride-002 | easy | 0.60 | 0.60 | 0.60 | 0.33 | 0.45 | ✓ |
| vitamin-b6-pyridoxine-hydrochloride-003 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.85 | ✓ |
| vitamin-b6-pyridoxine-hydrochloride-004 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| vitamin-b6-pyridoxine-hydrochloride-005 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| vitamin-c-ascorbic-acid-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-ascorbic-acid-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-ascorbic-acid-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-ascorbic-acid-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-ascorbic-acid-005 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| ascorbic-acid-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-citrate-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-d-pantothenate-001 | easy | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ |
| cyanocobalamin-001 | easy | 0.20 | 0.20 | 0.20 | 0.50 | 0.21 | ✓ |
| magnesium-citrate-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| manganese-chelate-001 | medium | 0.80 | 0.80 | 0.80 | 1.00 | 0.79 | ✓ |
| niacin-001 | easy | 0.40 | 0.40 | 0.40 | 0.50 | 0.38 | ✓ |
| pink-himalayan-salt-001 | easy | 0.20 | 0.20 | 0.20 | 0.25 | 0.15 | ✓ |
| potassium-citrate-006 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| pyridoxine-hcl-001 | easy | 0.60 | 0.60 | 0.60 | 1.00 | 0.64 | ✓ |
| sodium-chloride-001 | easy | 0.60 | 0.60 | 0.60 | 1.00 | 0.68 | ✓ |
| zinc-oxide-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| biotin-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| b-vitamins-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| folate-001 | easy | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| folate-002 | easy | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| niacin-002 | easy | 0.40 | 0.40 | 0.40 | 0.50 | 0.38 | ✓ |
| niacin-003 | easy | 0.40 | 0.40 | 0.40 | 0.50 | 0.38 | ✓ |
| pantothenic-acid-001 | easy | 0.20 | 0.20 | 0.20 | 0.50 | 0.21 | ✓ |
| pantothenic-acid-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| thiamin-001 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.83 | ✓ |
| thiamin-002 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| vitamin-a-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-a-002 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b12-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b12-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b6-001 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-b6-002 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-c-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-002 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-003 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-d3-001 | easy | 0.20 | 0.20 | 0.20 | 0.20 | 0.13 | ✓ |
| vitamin-d3-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| vitamin-d3-003 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| vitamin-e-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| vitamin-e-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| vitamin-k-001 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-k-002 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| ascorbic-acid-002 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| ascorbic-acid-003 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| ascorbic-acid-004 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| ascorbic-acid-005 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| ascorbic-acid-006 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| beta-carotene-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| beta-carotene-002 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| beta-carotene-003 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| beta-carotene-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| beta-carotene-005 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| biotin-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-005 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-006 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-007 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-008 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-009 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| biotin-010 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| calcium-carbonate-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-carbonate-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-carbonate-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-carbonate-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-carbonate-005 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-carbonate-006 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-carbonate-007 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| calcium-carbonate-008 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| cholecalciferol-001 | easy | 0.20 | 0.20 | 0.20 | 0.25 | 0.15 | ✓ |
| cholecalciferol-002 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.49 | ✓ |
| cholecalciferol-003 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.49 | ✓ |
| cholecalciferol-004 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.49 | ✓ |
| cholecalciferol-005 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.49 | ✓ |
| chromium-chloride-001 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| chromium-chloride-002 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| chromium-chloride-003 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| chromium-chloride-004 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| chromium-chloride-005 | easy | 0.20 | 0.20 | 0.20 | 0.20 | 0.13 | ✓ |
| copper-sulfate-001 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.70 | ✓ |
| copper-sulfate-002 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| copper-sulfate-003 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.70 | ✓ |
| copper-sulfate-004 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.70 | ✓ |
| copper-sulfate-005 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| cyanocobalamin-002 | easy | 0.20 | 0.20 | 0.20 | 0.50 | 0.21 | ✓ |
| cyanocobalamin-003 | easy | 0.20 | 0.20 | 0.20 | 0.50 | 0.21 | ✓ |
| cyanocobalamin-004 | easy | 0.20 | 0.20 | 0.20 | 0.50 | 0.21 | ✓ |
| cyanocobalamin-005 | easy | 0.20 | 0.20 | 0.20 | 0.50 | 0.21 | ✓ |
| cyanocobalamin-006 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| d-calcium-pantothenate-001 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| d-calcium-pantothenate-002 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| d-calcium-pantothenate-003 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| d-calcium-pantothenate-004 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| d-calcium-pantothenate-005 | easy | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| dl-alpha-tocopheryl-acetate-001 | medium | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| dl-alpha-tocopheryl-acetate-002 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| dl-alpha-tocopheryl-acetate-003 | medium | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| dl-alpha-tocopheryl-acetate-004 | medium | 0.80 | 0.80 | 0.80 | 1.00 | 0.87 | ✓ |
| dl-alpha-tocopheryl-acetate-005 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| folic-acid-001 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| folic-acid-002 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| folic-acid-003 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| folic-acid-004 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| folic-acid-005 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| folic-acid-006 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| manganese-sulfate-001 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| manganese-sulfate-002 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| manganese-sulfate-003 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| manganese-sulfate-004 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| manganese-sulfate-005 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| niacin-004 | easy | 0.40 | 0.40 | 0.40 | 0.50 | 0.38 | ✓ |
| niacin-005 | easy | 0.40 | 0.40 | 0.40 | 0.50 | 0.38 | ✓ |
| niacinamide-001 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| niacinamide-002 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| niacinamide-003 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| niacinamide-004 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| niacinamide-005 | easy | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| pantothenic-acid-003 | easy | 0.20 | 0.20 | 0.20 | 0.33 | 0.17 | ✓ |
| potassium-iodide-001 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| potassium-iodide-002 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| potassium-iodide-003 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| potassium-iodide-004 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| potassium-iodide-005 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| pyridoxine-hydrochloride-001 | easy | 0.60 | 0.60 | 0.60 | 0.33 | 0.45 | ✓ |
| pyridoxine-hydrochloride-002 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.68 | ✓ |
| pyridoxine-hydrochloride-003 | easy | 0.60 | 0.60 | 0.60 | 0.33 | 0.45 | ✓ |
| pyridoxine-hydrochloride-004 | easy | 0.60 | 0.60 | 0.60 | 0.33 | 0.45 | ✓ |
| pyridoxine-hydrochloride-005 | easy | 0.60 | 0.60 | 0.60 | 0.33 | 0.45 | ✓ |
| riboflavin-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-005 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-006 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-007 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-008 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| riboflavin-009 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| sodium-selenite-001 | medium | 0.40 | 0.40 | 0.40 | 0.50 | 0.35 | ✓ |
| sodium-selenite-002 | medium | 0.40 | 0.40 | 0.40 | 0.50 | 0.35 | ✓ |
| sodium-selenite-003 | medium | 0.40 | 0.40 | 0.40 | 0.50 | 0.35 | ✓ |
| sodium-selenite-004 | medium | 0.40 | 0.40 | 0.40 | 0.50 | 0.35 | ✓ |
| sodium-selenite-005 | medium | 0.40 | 0.40 | 0.40 | 0.50 | 0.35 | ✓ |
| thiamin-003 | easy | 0.40 | 0.40 | 0.40 | 0.25 | 0.28 | ✓ |
| thiamin-004 | easy | 0.60 | 0.60 | 0.60 | 1.00 | 0.68 | ✓ |
| thiamine-mononitrate-001 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.70 | ✓ |
| thiamine-mononitrate-002 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| thiamine-mononitrate-003 | medium | 0.20 | 0.20 | 0.20 | 0.20 | 0.13 | ✓ |
| thiamine-mononitrate-004 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.70 | ✓ |
| thiamine-mononitrate-005 | easy | 0.60 | 0.60 | 0.60 | 1.00 | 0.70 | ✓ |
| vitamin-a-003 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-a-004 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-a-005 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-a-006 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-a-007 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-a-acetate-001 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| vitamin-a-acetate-002 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.65 | ✓ |
| vitamin-a-acetate-003 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-a-acetate-004 | medium | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-a-acetate-005 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.68 | ✓ |
| vitamin-b12-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b12-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-b6-003 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-b6-004 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-c-004 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-005 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-006 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-007 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-c-008 | medium | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-d-001 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-d-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-d-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-d-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ⚠ error |
| vitamin-e-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| vitamin-e-004 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-e-005 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-e-006 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-e-007 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| vitamin-k-003 | easy | 0.20 | 0.20 | 0.20 | 1.00 | 0.34 | ✓ |
| vitamin-k-004 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| zinc-oxide-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| zinc-oxide-003 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| zinc-oxide-004 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| zinc-oxide-005 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| zinc-oxide-006 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| ascorbic-acid-vitamin-c-001 | medium | 0.80 | 0.80 | 0.80 | 1.00 | 0.83 | ✓ |
| cyanocobalamin-vitamin-b12-001 | medium | 0.60 | 0.60 | 0.60 | 0.50 | 0.51 | ✓ |
| d-alpha-tocopheryl-acetate-vitamin-e-001 | medium | 0.60 | 0.60 | 0.60 | 1.00 | 0.72 | ✓ |
| dipotassium-phosphate-006 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.55 | ✓ |
| l-isoleucine-001 | medium | 1.00 | 0.60 | 0.75 | 1.00 | 0.72 | ✓ |
| l-leucine-001 | medium | 1.00 | 0.60 | 0.75 | 1.00 | 0.72 | ✓ |
| l-valine-001 | medium | 1.00 | 0.40 | 0.57 | 1.00 | 0.55 | ✓ |
| magnesium-citrate-002 | easy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✗ |
| pyridoxine-hydrochloride-vitamin-b6-001 | easy | 0.80 | 0.80 | 0.80 | 1.00 | 0.79 | ✓ |
| retinyl-palmitate-vitamin-a-001 | medium | 0.80 | 0.80 | 0.80 | 1.00 | 0.79 | ✓ |
| sea-salt-001 | medium | 0.40 | 0.40 | 0.40 | 1.00 | 0.49 | ✓ |

## Case Details

### dipotassium-phosphate-001
_Replace dipotassium-phosphate in FG-iherb-105065 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [786, 878, 514, 695, 1017] (scores: [85, 84, 70, 68, 67])
- **Expected IDs:** [704, 997, 493, 878, 786]

### dipotassium-phosphate-002
_Replace dipotassium-phosphate in FG-target-a-81806945 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [786, 878, 514, 695, 1017] (scores: [85, 84, 75, 70, 68])
- **Expected IDs:** [704, 997, 493, 878, 786]

### dipotassium-phosphate-003
_Replace dipotassium-phosphate in FG-walgreens-300411121 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [786, 878, 514, 695, 1017] (scores: [85, 84, 75, 70, 68])
- **Expected IDs:** [704, 997, 493, 878, 786]

### dipotassium-phosphate-004
_Replace dipotassium-phosphate in FG-walgreens-300447518 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [786, 878, 514, 695, 1017] (scores: [85, 84, 75, 70, 68])
- **Expected IDs:** [704, 997, 493, 878, 786]

### dipotassium-phosphate-005
_Replace dipotassium-phosphate in FG-walmart-270357039 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [786, 878, 493, 695, 514] (scores: [85, 84, 78, 75, 70])
- **Expected IDs:** [704, 997, 493, 878, 786]

### potassium-citrate-001
_Replace potassium-citrate in FG-iherb-105065 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [611, 878, 997, 1026, 786] (scores: [85, 80, 78, 75, 74])
- **Expected IDs:** [717, 785, 497, 1017, 575]

### potassium-citrate-002
_Replace potassium-citrate in FG-target-a-81806945 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [611, 878, 997, 490, 786] (scores: [85, 80, 78, 78, 78])
- **Expected IDs:** [328, 717, 785, 1017, 575]

### potassium-citrate-003
_Replace potassium-citrate in FG-walgreens-300411121 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [611, 878, 997, 328, 569] (scores: [85, 80, 78, 75, 70])
- **Expected IDs:** [328, 717, 785, 1017, 575]

### potassium-citrate-004
_Replace potassium-citrate in FG-walgreens-300447518 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [611, 878, 997, 490, 786] (scores: [85, 80, 78, 78, 78])
- **Expected IDs:** [717, 785, 497, 1017, 575]

### potassium-citrate-005
_Replace potassium-citrate in FG-walmart-270357039 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [611, 878, 997, 490, 786] (scores: [85, 80, 78, 78, 78])
- **Expected IDs:** [328, 717, 785, 1017, 575]

### salt-001
_Replace salt in FG-iherb-105065 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [486, 880, 577, 214, 612] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [486, 712, 880, 439, 696]

### salt-002
_Replace salt in FG-target-a-81806945 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [486, 880, 439, 712, 696] (scores: [98, 98, 95, 95, 95])
- **Expected IDs:** [486, 712, 880, 439, 696]

### salt-003
_Replace salt in FG-walgreens-300411121 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [486, 880, 439, 577, 214] (scores: [95, 95, 90, 90, 90])
- **Expected IDs:** [486, 880, 214, 439, 696]

### salt-004
_Replace salt in FG-walgreens-300447518 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [486, 880, 577, 214, 612] (scores: [95, 95, 95, 95, 95])
- **Expected IDs:** [486, 712, 880, 439, 696]

### salt-005
_Replace salt in FG-walmart-270357039 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [486, 880, 577, 214, 612] (scores: [95, 95, 95, 95, 95])
- **Expected IDs:** [486, 712, 880, 439, 696]

### sodium-citrate-001
_Replace sodium-citrate in FG-iherb-105065 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [917, 991, 715, 778, 488] (scores: [85, 84, 83, 82, 81])
- **Expected IDs:** [321, 1026, 328, 186, 252]

### sodium-citrate-002
_Replace sodium-citrate in FG-target-a-81806945 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [917, 991, 715, 778, 488] (scores: [85, 84, 83, 82, 81])
- **Expected IDs:** [321, 1026, 328, 186, 252]

### sodium-citrate-003
_Replace sodium-citrate in FG-walgreens-300411121 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [917, 991, 715, 778, 488] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [321, 1026, 328, 186, 252]

### sodium-citrate-004
_Replace sodium-citrate in FG-walgreens-300447518 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [917, 991, 715, 778, 488] (scores: [85, 84, 83, 82, 81])
- **Expected IDs:** [321, 1026, 328, 186, 252]

### sodium-citrate-005
_Replace sodium-citrate in FG-walmart-270357039 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [917, 991, 715, 778, 488] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [321, 1026, 328, 186, 252]

### vitamin-b12-cyanocobalamin-001

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137655 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b12-cyanocobalamin-002

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137654 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b12-cyanocobalamin-003

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137656 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b12-cyanocobalamin-004

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137656 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b12-cyanocobalamin-005

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137654 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b3-niacinamide-001
_Replace vitamin-b3-niacinamide in FG-iherb-105065 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 173, 1012, 647, 300] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [647, 300, 173, 1012, 1013]

### vitamin-b3-niacinamide-002
_Replace vitamin-b3-niacinamide in FG-target-a-81806945 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 173, 1012, 647, 300] (scores: [95, 95, 95, 95, 95])
- **Expected IDs:** [647, 300, 173, 1012, 1013]

### vitamin-b3-niacinamide-003
_Replace vitamin-b3-niacinamide in FG-walgreens-300411121 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 173, 1012, 647, 300] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [647, 300, 173, 1012, 1013]

### vitamin-b3-niacinamide-004
_Replace vitamin-b3-niacinamide in FG-walgreens-300447518 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 173, 1012, 647, 300] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [647, 300, 173, 1012, 1013]

### vitamin-b3-niacinamide-005
_Replace vitamin-b3-niacinamide in FG-walmart-270357039 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 173, 1012, 647, 300] (scores: [95, 95, 95, 95, 95])
- **Expected IDs:** [647, 300, 173, 1012, 1013]

### vitamin-b5-d-calcium-pantothenate-001
_Replace vitamin-b5-d-calcium-pantothenate in FG-iherb-105065 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [986, 167, 632, 936, 568] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [167, 632, 568, 986, 350]

### vitamin-b5-d-calcium-pantothenate-002
_Replace vitamin-b5-d-calcium-pantothenate in FG-target-a-81806945 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [986, 167, 350, 632, 936] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [167, 936, 632, 568, 350]

### vitamin-b5-d-calcium-pantothenate-003
_Replace vitamin-b5-d-calcium-pantothenate in FG-walgreens-300411121 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [986, 167, 350, 632, 936] (scores: [92, 91, 90, 89, 88])
- **Expected IDs:** [589, 301, 371, 568, 986]

### vitamin-b5-d-calcium-pantothenate-004
_Replace vitamin-b5-d-calcium-pantothenate in FG-walgreens-300447518 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [986, 167, 350, 632, 936] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [167, 632, 568, 986, 350]

### vitamin-b5-d-calcium-pantothenate-005
_Replace vitamin-b5-d-calcium-pantothenate in FG-walmart-270357039 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [986, 167, 350, 632, 936] (scores: [95, 94, 94, 94, 94])
- **Expected IDs:** [167, 632, 568, 986, 350]

### vitamin-b6-pyridoxine-hydrochloride-001
_Replace vitamin-b6-pyridoxine-hydrochloride in FG-iherb-105065 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [177, 576, 310, 400, 596] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [576, 710, 177, 377, 1019]

### vitamin-b6-pyridoxine-hydrochloride-002
_Replace vitamin-b6-pyridoxine-hydrochloride in FG-target-a-81806945 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1019, 710, 177, 400, 310] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [576, 400, 177, 596, 310]

### vitamin-b6-pyridoxine-hydrochloride-003
_Replace vitamin-b6-pyridoxine-hydrochloride in FG-walgreens-300411121 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [310, 400, 596, 1037, 177] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [576, 400, 177, 596, 310]

### vitamin-b6-pyridoxine-hydrochloride-004
_Replace vitamin-b6-pyridoxine-hydrochloride in FG-walgreens-300447518 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [310, 400, 596, 177, 576] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [576, 400, 177, 596, 310]

### vitamin-b6-pyridoxine-hydrochloride-005
_Replace vitamin-b6-pyridoxine-hydrochloride in FG-walmart-270357039 (company: Liquid I.V., current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [177, 576, 310, 400, 596] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [576, 400, 177, 596, 310]

### vitamin-c-ascorbic-acid-001

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 186157 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-ascorbic-acid-002

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 186156 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-ascorbic-acid-003

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 186158 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-ascorbic-acid-004

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 186158 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-ascorbic-acid-005

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 186156 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### ascorbic-acid-001
_Replace ascorbic-acid in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [699, 982, 614, 503, 830] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [160, 457, 236, 622, 335]

### calcium-citrate-001
_Replace calcium-citrate in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [866, 397, 351, 514, 609] (scores: [85, 82, 80, 78, 75])
- **Expected IDs:** [777, 265, 460, 340, 150]

### calcium-d-pantothenate-001
_Replace calcium-d-pantothenate in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [167, 350, 632, 936, 986] (scores: [85, 85, 85, 85, 84])
- **Expected IDs:** [167, 936, 632, 986, 350]

### cyanocobalamin-001
_Replace cyanocobalamin in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [995, 702, 499, 595, 399] (scores: [95, 95, 95, 95, 95])
- **Expected IDs:** [165, 935, 631, 349, 702]

### magnesium-citrate-001
_Replace magnesium-citrate in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [813, 531, 1003, 1005, 811] (scores: [85, 80, 80, 75, 70])
- **Expected IDs:** [708, 780, 532, 442, 508]

### manganese-chelate-001
_Replace manganese-chelate in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [871, 942, 365, 642, 272] (scores: [85, 83, 82, 81, 80])
- **Expected IDs:** [642, 871, 365, 782, 272]

### niacin-001
_Replace niacin in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [647, 300, 173, 1012, 1013] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [646, 585, 300, 173, 369]

### pink-himalayan-salt-001
_Replace pink-himalayan-salt in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [439, 696, 712, 880, 749] (scores: [90, 89, 88, 87, 86])
- **Expected IDs:** [486, 327, 784, 880, 723]

### potassium-citrate-006
_Replace potassium-citrate in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [611, 878, 997, 786, 1026] (scores: [85, 80, 78, 78, 75])
- **Expected IDs:** [717, 493, 569, 785, 1017]

### pyridoxine-hcl-001
_Replace pyridoxine-hcl in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [502, 1037, 596, 310, 400] (scores: [95, 95, 95, 95, 95])
- **Expected IDs:** [400, 177, 596, 662, 502]

### sodium-chloride-001
_Replace sodium-chloride in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [880, 486, 677, 495, 241] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [612, 486, 880, 241, 214]

### zinc-oxide-001
_Replace zinc-oxide in FG-target-a-1003257378 (company: Nature's Nutrition, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [615, 881, 791, 748, 249] (scores: [85, 80, 78, 76, 75])
- **Expected IDs:** [405, 280, 250, 668, 957]

### biotin-001

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148282 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-002

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148178 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### b-vitamins-001

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 136685 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### folate-001
_Replace folate in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [633, 937, 356, 355, 464] (scores: [85, 85, 85, 50, 50])
- **Expected IDs:** [291, 356, 998, 937, 633]

### folate-002
_Replace folate in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [633, 937, 356, 355, 464] (scores: [85, 85, 85, 45, 45])
- **Expected IDs:** [291, 356, 998, 937, 633]

### niacin-002
_Replace niacin in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [647, 300, 173, 1012, 1013] (scores: [90, 89, 88, 87, 86])
- **Expected IDs:** [646, 300, 173, 369, 573]

### niacin-003
_Replace niacin in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [647, 300, 173, 1012, 1013] (scores: [90, 90, 90, 90, 90])
- **Expected IDs:** [646, 300, 173, 369, 573]

### pantothenic-acid-001
_Replace pantothenic-acid in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [568, 986, 350, 501, 632] (scores: [88, 86, 85, 84, 83])
- **Expected IDs:** [648, 301, 371, 1014, 986]

### pantothenic-acid-002
_Replace pantothenic-acid in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [568] (scores: [89])
- **Expected IDs:** [648, 301, 371, 1014, 986]

### riboflavin-001
_Replace riboflavin in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [178, 379, 309, 303]

### riboflavin-002
_Replace riboflavin in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [652, 303, 178, 309, 379]

### thiamin-001
_Replace thiamin in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [393, 305, 183, 658, 394] (scores: [95, 94, 92, 90, 89])
- **Expected IDs:** [393, 394, 305, 658, 307]

### thiamin-002
_Replace thiamin in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [393, 305, 183, 658, 394] (scores: [95, 94, 92, 90, 89])
- **Expected IDs:** [393, 1033, 657, 305, 307]

### vitamin-a-001

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137361 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-a-002

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137257 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b12-001

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 197047 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b12-002

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 196943 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b6-001
_Replace vitamin-b6 in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [502, 862, 1019, 710, 177] (scores: [95, 85, 80, 78, 75])
- **Expected IDs:** [1037, 400, 310, 662, 502]

### vitamin-b6-002
_Replace vitamin-b6 in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [502, 862, 177, 576, 1019] (scores: [95, 90, 90, 90, 85])
- **Expected IDs:** [1037, 400, 662, 310, 502]

### vitamin-c-001

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141930 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-002

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141826 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-003

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141813 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-d3-001
_Replace vitamin-d3 in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [553, 266, 626, 342, 159] (scores: [85, 83, 82, 82, 81])
- **Expected IDs:** [402, 245, 246, 476, 159]

### vitamin-d3-002
_Replace vitamin-d3 in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [553, 266, 626, 342, 159] (scores: [85, 83, 82, 82, 81])
- **Expected IDs:** [552, 911, 402, 246, 476]

### vitamin-d3-003
_Replace vitamin-d3 in FG-thrive-market-new-chapter-mens-advanced-multivitamin (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [553, 266, 626, 342, 475] (scores: [90, 88, 87, 86, 85])
- **Expected IDs:** [552, 402, 246, 476, 159]

### vitamin-e-001
_Replace vitamin-e in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [703, 746, 843, 278, 396] (scores: [90, 88, 86, 84, 82])
- **Expected IDs:** [313, 554, 403, 665, 478]

### vitamin-e-002
_Replace vitamin-e in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [703, 746, 843, 278, 166] (scores: [89, 87, 85, 83, 81])
- **Expected IDs:** [313, 554, 403, 665, 478]

### vitamin-k-001
_Replace vitamin-k in FG-iherb-52816 (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [315, 372, 834, 555, 747] (scores: [92, 88, 85, 83, 82])
- **Expected IDs:** [404, 666, 314, 315, 479]

### vitamin-k-002
_Replace vitamin-k in FG-thrive-market-new-chapter-every-womans-one-daily-multivitamin-40-plus (company: New Chapter, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [315, 372, 834, 555, 946] (scores: [92, 88, 85, 83, 82])
- **Expected IDs:** [404, 666, 314, 315, 479]

### ascorbic-acid-002
_Replace ascorbic-acid in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [699, 982, 614, 503, 865] (scores: [98, 97, 96, 95, 85])
- **Expected IDs:** [160, 614, 982, 503, 699]

### ascorbic-acid-003
_Replace ascorbic-acid in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [699, 982, 614, 503, 865] (scores: [98, 97, 96, 95, 94])
- **Expected IDs:** [160, 614, 982, 503, 699]

### ascorbic-acid-004
_Replace ascorbic-acid in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [699, 982, 614, 503, 830] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [160, 614, 982, 503, 699]

### ascorbic-acid-005
_Replace ascorbic-acid in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [699, 982, 614, 503, 865] (scores: [98, 98, 98, 98, 95])
- **Expected IDs:** [160, 614, 982, 503, 699]

### ascorbic-acid-006
_Replace ascorbic-acid in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [699, 982, 614, 503, 865] (scores: [98, 97, 96, 95, 85])
- **Expected IDs:** [160, 614, 982, 503, 699]

### beta-carotene-001
_Replace beta-carotene in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [286, 339, 580, 624, 929] (scores: [45, 45, 45, 45, 45])
- **Expected IDs:** [864, 161, 928, 711, 338]

### beta-carotene-002
_Replace beta-carotene in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [286] (scores: [45])
- **Expected IDs:** [864, 161, 928, 338, 703]

### beta-carotene-003
_Replace beta-carotene in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [286, 339, 580, 624, 929] (scores: [45, 45, 45, 45, 45])
- **Expected IDs:** [864, 161, 928, 711, 338]

### beta-carotene-004
_Replace beta-carotene in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [286, 339, 580, 624, 929] (scores: [45, 45, 45, 45, 45])
- **Expected IDs:** [864, 161, 338, 928]

### beta-carotene-005
_Replace beta-carotene in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [286, 339, 580, 624, 929] (scores: [45, 45, 45, 45, 45])
- **Expected IDs:** [864, 161, 928, 711, 338]

### biotin-003

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148287 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-004

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148286 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-005

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148286 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-006

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148286 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-007

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148289 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-008

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148287 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-009

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148288 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### biotin-010

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 148288 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### calcium-carbonate-001
_Replace calcium-carbonate in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 609] (scores: [88, 87, 86, 85, 84])
- **Expected IDs:** [520, 265, 459, 340, 607]

### calcium-carbonate-002
_Replace calcium-carbonate in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 397] (scores: [88, 88, 88, 88, 87])
- **Expected IDs:** [520, 265, 459, 340, 607]

### calcium-carbonate-003
_Replace calcium-carbonate in FG-cvs-410537 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 397] (scores: [85, 85, 85, 85, 84])
- **Expected IDs:** [520, 265, 459, 340, 607]

### calcium-carbonate-004
_Replace calcium-carbonate in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 609] (scores: [88, 88, 88, 88, 85])
- **Expected IDs:** [520, 265, 459, 340, 607]

### calcium-carbonate-005
_Replace calcium-carbonate in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 609] (scores: [90, 89, 88, 87, 85])
- **Expected IDs:** [520, 265, 459, 340, 607]

### calcium-carbonate-006
_Replace calcium-carbonate in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 397] (scores: [88, 88, 88, 88, 87])
- **Expected IDs:** [520, 265, 459, 340, 607]

### calcium-carbonate-007
_Replace calcium-carbonate in FG-walgreens-prod6028865 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 397] (scores: [88, 88, 88, 88, 87])
- **Expected IDs:** [520, 265, 459, 340, 607]

### calcium-carbonate-008
_Replace calcium-carbonate in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [569, 777, 460, 150, 609] (scores: [85, 84, 83, 82, 81])
- **Expected IDs:** [520, 265, 459, 340, 607]

### cholecalciferol-001
_Replace cholecalciferol in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [266, 912, 553, 159, 517] (scores: [90, 88, 88, 88, 88])
- **Expected IDs:** [932, 455, 431, 342, 159]

### cholecalciferol-002
_Replace cholecalciferol in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [266, 912, 553, 159, 517] (scores: [90, 88, 88, 88, 88])
- **Expected IDs:** [932, 266, 431, 342, 159]

### cholecalciferol-003
_Replace cholecalciferol in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [266, 912, 553, 159, 517] (scores: [90, 89, 89, 89, 89])
- **Expected IDs:** [932, 266, 431, 342, 159]

### cholecalciferol-004
_Replace cholecalciferol in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [266, 912, 553, 159, 517] (scores: [90, 88, 87, 86, 85])
- **Expected IDs:** [932, 266, 431, 342, 159]

### cholecalciferol-005
_Replace cholecalciferol in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [266, 912, 553, 159, 517] (scores: [90, 89, 88, 87, 86])
- **Expected IDs:** [932, 266, 431, 342, 159]

### chromium-chloride-001
_Replace chromium-chloride in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [990, 289, 343, 461, 608] (scores: [85, 85, 85, 85, 75])
- **Expected IDs:** [289, 461, 343, 344, 990]

### chromium-chloride-002
_Replace chromium-chloride in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [990, 343, 461, 289, 608] (scores: [85, 85, 85, 85, 80])
- **Expected IDs:** [289, 461, 343, 344, 990]

### chromium-chloride-003
_Replace chromium-chloride in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [990, 289, 343, 461, 608] (scores: [85, 85, 85, 85, 75])
- **Expected IDs:** [289, 461, 343, 344, 990]

### chromium-chloride-004
_Replace chromium-chloride in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [753, 251, 288, 848, 343] (scores: [78, 78, 78, 78, 77])
- **Expected IDs:** [608, 289, 933, 344, 345]

### chromium-chloride-005
_Replace chromium-chloride in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [753, 251, 288, 848, 343] (scores: [85, 85, 85, 85, 80])
- **Expected IDs:** [289, 461, 343, 344, 990]

### copper-sulfate-001
_Replace copper-sulfate in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [348, 934, 860, 615, 642] (scores: [85, 85, 80, 78, 77])
- **Expected IDs:** [934, 615, 267, 628, 348]

### copper-sulfate-002
_Replace copper-sulfate in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [348, 934, 860, 615, 642] (scores: [85, 85, 80, 78, 77])
- **Expected IDs:** [290, 934, 267, 462, 348]

### copper-sulfate-003
_Replace copper-sulfate in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [348, 934, 860, 615, 642] (scores: [85, 85, 80, 78, 77])
- **Expected IDs:** [934, 615, 267, 347, 348]

### copper-sulfate-004
_Replace copper-sulfate in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [348, 934, 860, 615, 642] (scores: [85, 85, 80, 78, 77])
- **Expected IDs:** [934, 615, 267, 272, 348]

### copper-sulfate-005
_Replace copper-sulfate in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [348, 934, 860, 615, 642] (scores: [85, 85, 80, 78, 77])
- **Expected IDs:** [290, 934, 267, 462, 348]

### cyanocobalamin-002
_Replace cyanocobalamin in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [995, 702, 499, 595, 399] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [165, 935, 570, 349, 702]

### cyanocobalamin-003
_Replace cyanocobalamin in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [995, 702, 499, 595, 399] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [165, 935, 570, 349, 702]

### cyanocobalamin-004
_Replace cyanocobalamin in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [995, 702, 499, 595, 399] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [165, 935, 570, 349, 702]

### cyanocobalamin-005
_Replace cyanocobalamin in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [995, 702, 499, 595, 399] (scores: [95, 95, 95, 95, 95])
- **Expected IDs:** [165, 935, 570, 349, 702]

### cyanocobalamin-006
_Replace cyanocobalamin in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [995] (scores: [95])
- **Expected IDs:** [165, 935, 570, 349, 702]

### d-calcium-pantothenate-001
_Replace d-calcium-pantothenate in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [568, 501, 986, 1014, 589] (scores: [95, 90, 85, 80, 75])
- **Expected IDs:** [167, 501, 568, 986, 350]

### d-calcium-pantothenate-002
_Replace d-calcium-pantothenate in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [568, 501, 986, 1014, 301] (scores: [95, 90, 85, 80, 75])
- **Expected IDs:** [167, 501, 568, 986, 350]

### d-calcium-pantothenate-003
_Replace d-calcium-pantothenate in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [568, 986, 501, 1014, 589] (scores: [95, 90, 85, 80, 75])
- **Expected IDs:** [167, 501, 568, 986, 350]

### d-calcium-pantothenate-004
_Replace d-calcium-pantothenate in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [568, 501, 986, 1014, 589] (scores: [92, 88, 85, 80, 78])
- **Expected IDs:** [167, 501, 568, 986, 350]

### d-calcium-pantothenate-005
_Replace d-calcium-pantothenate in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [568, 501, 986, 1014, 301] (scores: [95, 90, 85, 80, 75])
- **Expected IDs:** [167, 501, 568, 986, 350]

### dl-alpha-tocopheryl-acetate-001
_Replace dl-alpha-tocopheryl-acetate in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [703, 843, 406, 746, 166] (scores: [88, 86, 84, 82, 80])
- **Expected IDs:** [746, 843, 406, 407, 703]

### dl-alpha-tocopheryl-acetate-002
_Replace dl-alpha-tocopheryl-acetate in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [703, 406, 843, 746, 166] (scores: [88, 85, 83, 81, 79])
- **Expected IDs:** [407, 843, 278, 406, 703]

### dl-alpha-tocopheryl-acetate-003
_Replace dl-alpha-tocopheryl-acetate in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [703, 406, 843, 746, 166] (scores: [88, 85, 83, 80, 78])
- **Expected IDs:** [746, 843, 406, 407, 703]

### dl-alpha-tocopheryl-acetate-004
_Replace dl-alpha-tocopheryl-acetate in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [703, 406, 843, 746, 166] (scores: [88, 85, 83, 81, 79])
- **Expected IDs:** [746, 843, 406, 407, 703]

### dl-alpha-tocopheryl-acetate-005
_Replace dl-alpha-tocopheryl-acetate in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [703, 406, 843, 746, 166] (scores: [88, 85, 83, 81, 79])
- **Expected IDs:** [407, 396, 278, 406, 703]

### folic-acid-001
_Replace folic-acid in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [291, 998, 583, 457, 160] (scores: [85, 84, 83, 60, 59])
- **Expected IDs:** [291, 356, 998, 583, 937]

### folic-acid-002
_Replace folic-acid in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [291, 998, 583, 457, 160] (scores: [85, 84, 83, 70, 69])
- **Expected IDs:** [291, 356, 998, 583, 937]

### folic-acid-003
_Replace folic-acid in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [291, 998, 583, 457, 160] (scores: [85, 84, 83, 70, 69])
- **Expected IDs:** [291, 356, 998, 583, 937]

### folic-acid-004
_Replace folic-acid in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [291, 998, 583, 457, 160] (scores: [85, 85, 85, 70, 70])
- **Expected IDs:** [291, 356, 998, 583, 937]

### folic-acid-005
_Replace folic-acid in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [291, 998, 583, 457, 160] (scores: [85, 84, 83, 60, 59])
- **Expected IDs:** [291, 356, 998, 583, 937]

### folic-acid-006
_Replace folic-acid in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [291, 998, 583, 457, 160] (scores: [85, 84, 83, 60, 59])
- **Expected IDs:** [291, 356, 998, 583, 937]

### manganese-sulfate-001
_Replace manganese-sulfate in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [469, 721, 1008, 172, 298] (scores: [90, 89, 88, 87, 86])
- **Expected IDs:** [871, 365, 942, 272, 572]

### manganese-sulfate-002
_Replace manganese-sulfate in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [871, 469, 721, 1008, 172] (scores: [90, 88, 87, 86, 85])
- **Expected IDs:** [871, 365, 942, 272, 572]

### manganese-sulfate-003
_Replace manganese-sulfate in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [871, 469, 721, 1008, 172] (scores: [90, 88, 87, 86, 85])
- **Expected IDs:** [871, 365, 942, 272, 572]

### manganese-sulfate-004
_Replace manganese-sulfate in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [469, 721, 1008, 172, 298] (scores: [90, 89, 88, 87, 86])
- **Expected IDs:** [871, 365, 942, 272, 572]

### manganese-sulfate-005
_Replace manganese-sulfate in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [469, 721, 1008, 172, 298] (scores: [90, 89, 88, 87, 86])
- **Expected IDs:** [871, 365, 942, 272, 572]

### niacin-004
_Replace niacin in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [647, 300, 173, 1012, 1013] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [585, 300, 173, 369, 573]

### niacin-005
_Replace niacin in FG-walgreens-prod6028865 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [647, 300, 173, 1012, 1013] (scores: [90, 90, 90, 90, 90])
- **Expected IDs:** [585, 300, 173, 369, 573]

### niacinamide-001
_Replace niacinamide in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 500, 370, 945, 369] (scores: [95, 95, 90, 90, 85])
- **Expected IDs:** [300, 173, 1012, 1013, 500]

### niacinamide-002
_Replace niacinamide in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 500, 370, 945, 369] (scores: [95, 94, 90, 89, 85])
- **Expected IDs:** [300, 173, 1012, 1013, 500]

### niacinamide-003
_Replace niacinamide in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 500, 370, 369, 658] (scores: [95, 94, 90, 85, 70])
- **Expected IDs:** [300, 173, 1012, 1013, 500]

### niacinamide-004
_Replace niacinamide in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 500, 370, 945, 369] (scores: [95, 94, 90, 89, 85])
- **Expected IDs:** [300, 173, 1012, 1013, 500]

### niacinamide-005
_Replace niacinamide in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [1013, 500, 370, 945, 369] (scores: [95, 94, 92, 91, 85])
- **Expected IDs:** [300, 173, 1012, 1013, 500]

### pantothenic-acid-003
_Replace pantothenic-acid in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [568, 350, 986, 632, 501] (scores: [88, 86, 84, 82, 80])
- **Expected IDs:** [589, 301, 371, 1014, 986]

### potassium-iodide-001
_Replace potassium-iodide in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [293, 899, 194, 224, 256] (scores: [78, 72, 72, 72, 72])
- **Expected IDs:** [293, 878, 786, 375, 376]

### potassium-iodide-002
_Replace potassium-iodide in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [293, 899, 194, 224, 256] (scores: [80, 75, 75, 75, 75])
- **Expected IDs:** [293, 878, 786, 375, 376]

### potassium-iodide-003
_Replace potassium-iodide in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [293, 899, 194, 224, 256] (scores: [85, 75, 74, 73, 72])
- **Expected IDs:** [293, 878, 786, 375, 376]

### potassium-iodide-004
_Replace potassium-iodide in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [293, 899, 194, 224, 256] (scores: [85, 75, 75, 75, 75])
- **Expected IDs:** [293, 878, 786, 375, 376]

### potassium-iodide-005
_Replace potassium-iodide in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [293, 899, 194, 224, 256] (scores: [85, 75, 74, 73, 72])
- **Expected IDs:** [293, 878, 786, 375, 376]

### pyridoxine-hydrochloride-001
_Replace pyridoxine-hydrochloride in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [710, 1019, 177, 576, 502] (scores: [95, 95, 94, 94, 94])
- **Expected IDs:** [576, 177, 948, 502, 377]

### pyridoxine-hydrochloride-002
_Replace pyridoxine-hydrochloride in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [710, 1019, 177, 576, 502] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [710, 948, 502, 377, 1019]

### pyridoxine-hydrochloride-003
_Replace pyridoxine-hydrochloride in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [710, 1019, 177, 502, 576] (scores: [95, 95, 93, 93, 93])
- **Expected IDs:** [576, 177, 948, 502, 377]

### pyridoxine-hydrochloride-004
_Replace pyridoxine-hydrochloride in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [710, 1019, 177, 576, 502] (scores: [95, 94, 92, 91, 90])
- **Expected IDs:** [576, 177, 948, 502, 377]

### pyridoxine-hydrochloride-005
_Replace pyridoxine-hydrochloride in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [710, 1019, 177, 502, 576] (scores: [95, 95, 93, 93, 93])
- **Expected IDs:** [576, 177, 948, 502, 377]

### riboflavin-003
_Replace riboflavin in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [590, 303, 178, 309, 379]

### riboflavin-004
_Replace riboflavin in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [590, 303, 178, 309, 379]

### riboflavin-005
_Replace riboflavin in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [590, 303, 178, 309, 379]

### riboflavin-006
_Replace riboflavin in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [590, 303, 178, 309, 379]

### riboflavin-007
_Replace riboflavin in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [590, 303, 178, 309, 379]

### riboflavin-008
_Replace riboflavin in FG-walgreens-prod6028865 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [590, 303, 178, 309, 379]

### riboflavin-009
_Replace riboflavin in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** [590, 303, 178, 309, 379]

### sodium-selenite-001
_Replace sodium-selenite in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [653, 304, 902, 591, 472] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [386, 472, 304, 952, 380]

### sodium-selenite-002
_Replace sodium-selenite in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [653, 304, 902, 591, 472] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [386, 472, 304, 952, 380]

### sodium-selenite-003
_Replace sodium-selenite in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [653, 304, 902, 591, 472] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [386, 472, 304, 952, 380]

### sodium-selenite-004
_Replace sodium-selenite in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [653, 304, 902, 591, 472] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [386, 472, 304, 952, 380]

### sodium-selenite-005
_Replace sodium-selenite in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [653, 304, 902, 591, 472] (scores: [85, 85, 85, 85, 85])
- **Expected IDs:** [386, 472, 304, 952, 380]

### thiamin-003
_Replace thiamin in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [393, 305, 183, 658, 394] (scores: [95, 94, 92, 90, 89])
- **Expected IDs:** [1033, 394, 593, 658, 956]

### thiamin-004
_Replace thiamin in FG-walgreens-prod6028865 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [393, 305, 183, 658, 307] (scores: [95, 94, 92, 90, 89])
- **Expected IDs:** [393, 1033, 593, 305, 307]

### thiamine-mononitrate-001
_Replace thiamine-mononitrate in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [393, 305, 183, 307, 1033] (scores: [88, 88, 88, 88, 87])
- **Expected IDs:** [393, 394, 305, 307, 956]

### thiamine-mononitrate-002
_Replace thiamine-mononitrate in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [393, 305, 183, 307, 1033] (scores: [88, 88, 87, 87, 85])
- **Expected IDs:** [393, 394, 305, 183, 956]

### thiamine-mononitrate-003
_Replace thiamine-mononitrate in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [393, 305, 183, 307, 1033] (scores: [88, 88, 87, 87, 86])
- **Expected IDs:** [1033, 394, 593, 657, 956]

### thiamine-mononitrate-004
_Replace thiamine-mononitrate in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [393, 305, 183, 307, 1033] (scores: [88, 88, 87, 87, 86])
- **Expected IDs:** [393, 394, 305, 307, 956]

### thiamine-mononitrate-005
_Replace thiamine-mononitrate in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [393, 305, 183, 307, 1033] (scores: [88, 88, 87, 87, 85])
- **Expected IDs:** [393, 394, 305, 307, 956]

### vitamin-a-003

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137364 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-a-004

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137364 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-a-005

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137367 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-a-006

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137366 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-a-007

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 137366 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-a-acetate-001
_Replace vitamin-a-acetate in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [743, 378, 711, 306, 1036] (scores: [85, 83, 82, 81, 80])
- **Expected IDs:** [743, 407, 378, 669, 703]

### vitamin-a-acetate-002
_Replace vitamin-a-acetate in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [378, 711, 306, 474, 1036] (scores: [85, 82, 80, 80, 80])
- **Expected IDs:** [743, 378, 398, 306, 474]

### vitamin-a-acetate-003
_Replace vitamin-a-acetate in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [378, 711, 184, 1036, 474] (scores: [85, 82, 80, 78, 76])
- **Expected IDs:** [743, 407, 378, 669, 703]

### vitamin-a-acetate-004
_Replace vitamin-a-acetate in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [743, 306, 1036, 474, 550] (scores: [85, 84, 83, 82, 81])
- **Expected IDs:** [743, 407, 378, 669, 703]

### vitamin-a-acetate-005
_Replace vitamin-a-acetate in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [743, 378, 184, 711, 306] (scores: [85, 83, 81, 80, 79])
- **Expected IDs:** [743, 378, 398, 306, 474]

### vitamin-b12-003

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 197053 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b12-004

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 197052 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-b6-003
_Replace vitamin-b6 in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [502, 862, 1019, 710, 177] (scores: [95, 85, 80, 78, 75])
- **Expected IDs:** [1037, 400, 596, 310, 502]

### vitamin-b6-004
_Replace vitamin-b6 in FG-walgreens-prod6028865 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [502, 862, 1019, 710, 177] (scores: [95, 85, 80, 78, 75])
- **Expected IDs:** [1037, 400, 596, 310, 502]

### vitamin-c-004

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141934 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-005

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141934 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-006

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141937 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-007

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141936 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-c-008

- **Difficulty:** medium
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 141936 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-d-001

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 153095 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-d-002

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 153098 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-d-003

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 153097 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-d-004

- **Difficulty:** easy
- **Returned IDs:** [] (scores: [])
- **Expected IDs:** []
- **Error:** Error code: 400 - {'error': {'message': "This model's maximum context length is 128000 tokens. However, your messages resulted in 153097 tokens (including 348 in the response_format schemas.). Please reduce the length of the messages or schemas.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

### vitamin-e-003
_Replace vitamin-e in FG-cvs-410537 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [703, 746, 843, 278, 396] (scores: [90, 88, 86, 84, 82])
- **Expected IDs:** [554, 403, 599, 313, 478]

### vitamin-e-004
_Replace vitamin-e in FG-cvs-880579 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [703, 746, 843, 278, 396] (scores: [89, 87, 85, 83, 81])
- **Expected IDs:** [554, 403, 313, 478, 703]

### vitamin-e-005
_Replace vitamin-e in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [703, 746, 843, 278, 396] (scores: [90, 88, 86, 84, 82])
- **Expected IDs:** [554, 403, 313, 478, 703]

### vitamin-e-006
_Replace vitamin-e in FG-walgreens-300413257 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [703, 746, 843, 278, 166] (scores: [90, 88, 86, 84, 82])
- **Expected IDs:** [554, 403, 313, 478, 703]

### vitamin-e-007
_Replace vitamin-e in FG-walgreens-prod6028865 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [703, 746, 843, 278, 166] (scores: [89, 87, 85, 83, 81])
- **Expected IDs:** [554, 403, 599, 313, 478]

### vitamin-k-003
_Replace vitamin-k in FG-sams-club-prod15990273 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [315, 372, 834, 555, 946] (scores: [90, 85, 80, 78, 77])
- **Expected IDs:** [404, 600, 314, 315, 479]

### vitamin-k-004
_Replace vitamin-k in FG-walgreens-prod6028865 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [315, 372, 834, 555, 946] (scores: [90, 85, 80, 78, 75])
- **Expected IDs:** [404, 372, 314, 315, 479]

### zinc-oxide-002
_Replace zinc-oxide in FG-costco-100143268 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [615, 881, 791, 748, 249] (scores: [90, 85, 83, 82, 80])
- **Expected IDs:** [578, 405, 280, 250, 957]

### zinc-oxide-003
_Replace zinc-oxide in FG-cvs-246284 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [615, 791, 881, 748, 249] (scores: [90, 85, 83, 82, 80])
- **Expected IDs:** [578, 405, 280, 250, 957]

### zinc-oxide-004
_Replace zinc-oxide in FG-cvs-448437 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [615, 881, 791, 748, 249] (scores: [90, 85, 82, 80, 78])
- **Expected IDs:** [578, 405, 280, 250, 957]

### zinc-oxide-005
_Replace zinc-oxide in FG-target-a-10996455 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [615, 881, 791, 748, 249] (scores: [90, 85, 82, 80, 78])
- **Expected IDs:** [578, 405, 280, 250, 957]

### zinc-oxide-006
_Replace zinc-oxide in FG-walgreens-prod6083374 (company: One A Day, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [615, 791, 881, 748, 249] (scores: [90, 85, 83, 82, 80])
- **Expected IDs:** [578, 405, 280, 250, 957]

### ascorbic-acid-vitamin-c-001
_Replace ascorbic-acid-vitamin-c in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [503, 335, 622, 236, 160] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [160, 236, 335, 982, 503]

### cyanocobalamin-vitamin-b12-001
_Replace cyanocobalamin-vitamin-b12 in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [935, 349, 570, 631, 165] (scores: [98, 98, 98, 98, 98])
- **Expected IDs:** [995, 165, 499, 570, 349]

### d-alpha-tocopheryl-acetate-vitamin-e-001
_Replace d-alpha-tocopheryl-acetate-vitamin-e in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [843, 166, 746, 407, 1041] (scores: [85, 82, 80, 78, 76])
- **Expected IDs:** [166, 746, 843, 403, 313]

### dipotassium-phosphate-006
_Replace dipotassium-phosphate in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [786, 878, 695, 514, 1017] (scores: [85, 85, 75, 70, 65])
- **Expected IDs:** [997, 490, 493, 878, 786]

### l-isoleucine-001
_Replace l-isoleucine in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [707, 706, 839] (scores: [85, 83, 81])
- **Expected IDs:** [706, 707, 295, 839, 219]

### l-leucine-001
_Replace l-leucine in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [839, 705, 707] (scores: [85, 78, 76])
- **Expected IDs:** [705, 707, 295, 808, 839]

### l-valine-001
_Replace l-valine in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [705, 706] (scores: [85, 84])
- **Expected IDs:** [705, 706, 839, 308, 221]

### magnesium-citrate-002
_Replace magnesium-citrate in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [813, 531, 1003, 1002, 1005] (scores: [85, 80, 80, 75, 70])
- **Expected IDs:** [780, 532, 442, 571, 508]

### pyridoxine-hydrochloride-vitamin-b6-001
_Replace pyridoxine-hydrochloride-vitamin-b6 in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** easy
- **Returned IDs:** [651, 948, 502, 377, 576] (scores: [95, 95, 94, 94, 93])
- **Expected IDs:** [576, 651, 177, 502, 377]

### retinyl-palmitate-vitamin-a-001
_Replace retinyl-palmitate-vitamin-a in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [660, 184, 743, 378, 703] (scores: [90, 85, 80, 75, 70])
- **Expected IDs:** [743, 660, 949, 378, 703]

### sea-salt-001
_Replace sea-salt in FG-amazon-b0ft5z9k9n (company: PRIME HYDRATION+, current supplier: PureBulk)._

- **Difficulty:** medium
- **Returned IDs:** [880, 612, 214, 486, 327] (scores: [95, 94, 93, 92, 91])
- **Expected IDs:** [486, 880, 241, 439, 696]
