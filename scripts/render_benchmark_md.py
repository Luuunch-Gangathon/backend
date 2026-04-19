"""Regenerate results.md from an existing results.json — no LLM/DB calls."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.benchmark import (
    BENCHMARK_DIR,
    RESULTS_JSON,
    RESULTS_MD,
    aggregate,
    aggregate_by_difficulty,
    build_markdown,
    hit_at_n,
    jaccard,
    map_at_k,
)


def main() -> None:
    if not RESULTS_JSON.exists():
        print(f"Results file not found: {RESULTS_JSON}")
        sys.exit(1)

    with open(RESULTS_JSON) as f:
        data = json.load(f)

    results = data.get("cases", [])
    run_at = data.get("run_at", "unknown")
    k = data.get("k", 5)
    dataset_metadata = data.get("dataset_metadata", {})

    for r in results:
        returned = r.get("returned_ids", [])
        expected = set(r.get("expected_ids", []))
        if "jaccard" not in r:
            r["jaccard"] = round(jaccard(returned, expected, k), 4)
        if "map" not in r:
            r["map"] = round(map_at_k(returned, expected, k), 4)
        if "hit@1" not in r:
            r["hit@1"] = round(hit_at_n(returned, expected, 1), 4)
        if "hit@3" not in r:
            r["hit@3"] = round(hit_at_n(returned, expected, 3), 4)

    agg = aggregate(results)
    by_diff = aggregate_by_difficulty(results)

    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_MD, "w") as f:
        f.write(build_markdown(results, agg, by_diff, run_at, k, dataset_metadata))

    print(f"Wrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
