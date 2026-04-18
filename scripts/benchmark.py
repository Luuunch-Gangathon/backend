"""Compliance engine benchmark.

Loads test cases from knowledge/benchmark/compliance_cases.json, runs each
through check_compliance(), computes precision/recall/F1/MRR/NDCG, and
prints a summary table.

Results written to:
    knowledge/benchmark/results.json  — full machine-readable output
    knowledge/benchmark/results.md    — human-readable markdown report

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/benchmark.py

Requires:
    - DATABASE_URL env var set (or .env file)
    - Running Postgres with seeded data + embeddings
    - OPENAI_API_KEY set
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow imports from app/ without installing as package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from app.data import db
from app.agents.compliance import check_compliance

logging.basicConfig(level=logging.WARNING)

BENCHMARK_DIR = Path(__file__).resolve().parents[1] / "knowledge" / "benchmark"
CASES_FILE = BENCHMARK_DIR / "compliance_cases.json"
RESULTS_JSON = BENCHMARK_DIR / "results.json"
RESULTS_MD = BENCHMARK_DIR / "results.md"


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def precision_at_k(returned: list[int], expected: set[int], k: int) -> float:
    top_k = returned[:k]
    if not top_k:
        return 0.0
    return len(set(top_k) & expected) / len(top_k)


def recall_at_k(returned: list[int], expected: set[int], k: int) -> float:
    if not expected:
        return 1.0
    top_k = returned[:k]
    return len(set(top_k) & expected) / len(expected)


def f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def mrr(returned: list[int], expected: set[int]) -> float:
    """Mean Reciprocal Rank — reciprocal of rank of first correct result."""
    for i, rid in enumerate(returned, start=1):
        if rid in expected:
            return 1.0 / i
    return 0.0


def ndcg_at_k(returned: list[int], ideal_ranking: list[int], k: int) -> float:
    """NDCG@K using binary relevance from ideal_ranking set."""
    relevant = set(ideal_ranking)

    def dcg(ids: list[int]) -> float:
        total = 0.0
        for i, rid in enumerate(ids[:k], start=1):
            if rid in relevant:
                total += 1.0 / math.log2(i + 1)
        return total

    actual_dcg = dcg(returned)
    ideal_dcg = dcg(ideal_ranking)
    if ideal_dcg == 0:
        return 1.0 if actual_dcg == 0 else 0.0
    return actual_dcg / ideal_dcg


def exclusion_violated(returned: list[int], excluded: list[int]) -> bool:
    return bool(set(returned) & set(excluded))


# ---------------------------------------------------------------------------
# Per-case evaluation
# ---------------------------------------------------------------------------

async def run_case(case: dict, k: int = 5) -> dict:
    product_id = case["product_id"]
    raw_material_id = case["raw_material_id"]
    expected_ids = set(case.get("expected_ids", []))
    excluded_ids = case.get("excluded_ids", [])
    ideal_ranking = case.get("ideal_ranking", list(expected_ids))

    try:
        proposals = await check_compliance(product_id, raw_material_id, top_x=k)
    except Exception as exc:
        return {
            "case_id": case["case_id"],
            "error": str(exc),
            "pass": False,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "mrr": 0.0,
            "ndcg": 0.0,
            "exclusion_violated": False,
            "returned_ids": [],
            "scores": [],
            "difficulty": case.get("difficulty", "unknown"),
        }

    returned_ids = [p.id for p in proposals]
    scores = [p.score for p in proposals]

    p = precision_at_k(returned_ids, expected_ids, k)
    r = recall_at_k(returned_ids, expected_ids, k)
    f = f1(p, r)
    m = mrr(returned_ids, expected_ids)
    n = ndcg_at_k(returned_ids, ideal_ranking, k)
    excluded_hit = exclusion_violated(returned_ids, excluded_ids)

    passed = (r > 0) and (not excluded_hit)

    return {
        "case_id": case["case_id"],
        "description": case.get("description", ""),
        "returned_ids": returned_ids,
        "scores": scores,
        "expected_ids": list(expected_ids),
        "excluded_ids": excluded_ids,
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1": round(f, 4),
        "mrr": round(m, 4),
        "ndcg": round(n, 4),
        "exclusion_violated": excluded_hit,
        "pass": passed,
        "difficulty": case.get("difficulty", "unknown"),
        "error": None,
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate(results: list[dict]) -> dict:
    if not results:
        return {}
    keys = ["precision", "recall", "f1", "mrr", "ndcg"]
    agg = {k: round(sum(r[k] for r in results) / len(results), 4) for k in keys}
    agg["exclusion_accuracy"] = round(
        sum(1 for r in results if not r["exclusion_violated"]) / len(results), 4
    )
    agg["pass_rate"] = round(sum(1 for r in results if r["pass"]) / len(results), 4)
    return agg


def aggregate_by_difficulty(results: list[dict]) -> dict:
    by_diff: dict[str, list[dict]] = {}
    for r in results:
        diff = r.get("difficulty", "unknown")
        by_diff.setdefault(diff, []).append(r)
    return {diff: aggregate(cases) for diff, cases in by_diff.items()}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(results: list[dict], agg: dict, by_diff: dict) -> None:
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    errors = sum(1 for r in results if r.get("error"))

    print()
    print("Compliance Benchmark")
    print("=" * 55)
    print(f"  Run at : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Cases  : {total}  |  Passed: {passed}  |  Failed: {total - passed}", end="")
    if errors:
        print(f"  |  Errors: {errors}", end="")
    print()
    print()

    if not results:
        print("  No cases to evaluate. Populate knowledge/benchmark/compliance_cases.json first.")
        print()
        return

    print("  Aggregate (K=5):")
    print(f"    Precision        {agg.get('precision', 0):.4f}")
    print(f"    Recall           {agg.get('recall', 0):.4f}")
    print(f"    F1               {agg.get('f1', 0):.4f}")
    print(f"    MRR              {agg.get('mrr', 0):.4f}")
    print(f"    NDCG@5           {agg.get('ndcg', 0):.4f}")
    print(f"    Excl. Accuracy   {agg.get('exclusion_accuracy', 0):.4f}")
    print()

    if by_diff:
        print("  By difficulty:")
        for diff in ["easy", "medium", "hard", "unknown"]:
            if diff not in by_diff:
                continue
            d = by_diff[diff]
            diff_results = [r for r in results if r.get("difficulty") == diff]
            diff_passed = sum(1 for r in diff_results if r["pass"])
            print(
                f"    {diff:<8}  F1: {d.get('f1', 0):.2f}  "
                f"MRR: {d.get('mrr', 0):.2f}  "
                f"({diff_passed}/{len(diff_results)} passed)"
            )
        print()

    print("  Per-case:")
    header = f"  {'ID':<35} {'P':>5} {'R':>5} {'F1':>5} {'MRR':>5} {'Pass':>5}"
    print(header)
    print("  " + "-" * 65)
    for r in results:
        status = "✓" if r["pass"] else "✗"
        if r.get("error"):
            status = "E"
        cid = r["case_id"][:34]
        print(
            f"  {cid:<35} {r['precision']:>5.2f} {r['recall']:>5.2f} "
            f"{r['f1']:>5.2f} {r['mrr']:>5.2f} {status:>5}"
        )
    print()


def build_markdown(results: list[dict], agg: dict, by_diff: dict, run_at: str) -> str:
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    lines: list[str] = []

    lines.append("# Compliance Benchmark Results")
    lines.append("")
    lines.append(f"**Run:** {run_at}  ")
    lines.append(f"**Cases:** {total} | **Passed:** {passed} | **Failed:** {total - passed}")
    lines.append("")

    lines.append("## Aggregate Metrics (K=5)")
    lines.append("")
    lines.append("| Metric | Score |")
    lines.append("|--------|-------|")
    lines.append(f"| Precision@5 | {agg.get('precision', 0):.4f} |")
    lines.append(f"| Recall@5 | {agg.get('recall', 0):.4f} |")
    lines.append(f"| F1@5 | {agg.get('f1', 0):.4f} |")
    lines.append(f"| MRR | {agg.get('mrr', 0):.4f} |")
    lines.append(f"| NDCG@5 | {agg.get('ndcg', 0):.4f} |")
    lines.append(f"| Exclusion Accuracy | {agg.get('exclusion_accuracy', 0):.4f} |")
    lines.append(f"| Pass Rate | {agg.get('pass_rate', 0):.4f} |")
    lines.append("")

    if by_diff:
        lines.append("## By Difficulty")
        lines.append("")
        lines.append("| Difficulty | Precision | Recall | F1 | MRR | NDCG | Passed |")
        lines.append("|------------|-----------|--------|-----|-----|------|--------|")
        for diff in ["easy", "medium", "hard", "unknown"]:
            if diff not in by_diff:
                continue
            d = by_diff[diff]
            diff_results = [r for r in results if r.get("difficulty") == diff]
            diff_passed = sum(1 for r in diff_results if r["pass"])
            lines.append(
                f"| {diff} | {d.get('precision',0):.2f} | {d.get('recall',0):.2f} | "
                f"{d.get('f1',0):.2f} | {d.get('mrr',0):.2f} | "
                f"{d.get('ndcg',0):.2f} | {diff_passed}/{len(diff_results)} |"
            )
        lines.append("")

    lines.append("## Per-Case Results")
    lines.append("")
    lines.append("| Case ID | Difficulty | Precision | Recall | F1 | MRR | NDCG | Excl. OK | Pass |")
    lines.append("|---------|------------|-----------|--------|-----|-----|------|----------|------|")
    for r in results:
        excl_ok = "✓" if not r["exclusion_violated"] else "✗"
        status = "✓" if r["pass"] else ("⚠ error" if r.get("error") else "✗")
        lines.append(
            f"| {r['case_id']} | {r.get('difficulty','?')} | "
            f"{r['precision']:.2f} | {r['recall']:.2f} | {r['f1']:.2f} | "
            f"{r['mrr']:.2f} | {r['ndcg']:.2f} | {excl_ok} | {status} |"
        )
    lines.append("")

    lines.append("## Case Details")
    lines.append("")
    for r in results:
        lines.append(f"### {r['case_id']}")
        if r.get("description"):
            lines.append(f"_{r['description']}_")
        lines.append("")
        lines.append(f"- **Difficulty:** {r.get('difficulty', '?')}")
        lines.append(f"- **Returned IDs:** {r['returned_ids']} (scores: {r['scores']})")
        lines.append(f"- **Expected IDs:** {r['expected_ids']}")
        lines.append(f"- **Excluded IDs:** {r['excluded_ids']}")
        if r.get("error"):
            lines.append(f"- **Error:** {r['error']}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    if not CASES_FILE.exists():
        print(f"Dataset not found: {CASES_FILE}")
        sys.exit(1)

    with open(CASES_FILE) as f:
        dataset = json.load(f)

    cases = dataset.get("cases", [])

    # Filter out the example placeholder (product_id == 0)
    real_cases = [c for c in cases if c.get("product_id", 0) != 0]

    if not real_cases:
        print("No real cases found. Add entries to knowledge/benchmark/compliance_cases.json.")
        print("(Entries with product_id=0 are treated as placeholder examples.)")
        sys.exit(0)

    print(f"Loading {len(real_cases)} cases...")

    await db.init_pool()

    try:
        results = []
        for i, case in enumerate(real_cases, 1):
            print(f"  [{i}/{len(real_cases)}] {case['case_id']} ...", end=" ", flush=True)
            result = await run_case(case)
            results.append(result)
            status = "✓" if result["pass"] else ("E" if result.get("error") else "✗")
            print(status)
    finally:
        await db.close_pool()

    agg = aggregate(results)
    by_diff = aggregate_by_difficulty(results)

    run_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    output = {
        "run_at": run_at,
        "dataset_version": dataset.get("version", "unknown"),
        "k": 5,
        "aggregate": agg,
        "by_difficulty": by_diff,
        "cases": results,
    }

    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_JSON, "w") as f:
        json.dump(output, f, indent=2)

    with open(RESULTS_MD, "w") as f:
        f.write(build_markdown(results, agg, by_diff, run_at))

    print_report(results, agg, by_diff)
    print(f"Results written to:")
    print(f"  {RESULTS_JSON}")
    print(f"  {RESULTS_MD}")


if __name__ == "__main__":
    asyncio.run(main())
