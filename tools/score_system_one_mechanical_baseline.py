"""Score the existing deterministic route as a binary, no-action baseline."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.mechanical import mechanical_route


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "phases/system-one-binary-5k-20260922"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    raw = (directory / "cases.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["cases_sha256"]:
        raise ValueError("frozen suite changed")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    categories = defaultdict(Counter)
    timings = []
    for row in rows:
        started = time.perf_counter()
        route = mechanical_route(row["prompt"], allowed_root=root)
        timings.append((time.perf_counter() - started) * 1000)
        decision = "not_abstain" if route is not None and route.get("schema") == "wrench.proposal.v1" else "abstain"
        expected = "not_abstain" if row["label"] == "wrench" else "abstain"
        bucket = categories[row["category"]]
        bucket["rows"] += 1
        bucket["correct"] += int(decision == expected)
        bucket["false_wrench"] += int(expected == "abstain" and decision == "not_abstain")
        bucket["false_abstain"] += int(expected == "not_abstain" and decision == "abstain")
    sorted_timing = sorted(timings)
    neg_correct = sum(v["correct"] for k, v in categories.items() if k not in {
        "read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"})
    pos_correct = sum(v["correct"] for k, v in categories.items() if k in {
        "read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"})
    report = {"schema": "wrench.system-one-mechanical-baseline.v1",
              "scope": "post-first-pass baseline, deterministic route only, no model or action execution",
              "suite_sha256": manifest["cases_sha256"], "rows": len(rows),
              "abstain_recall": neg_correct / 5000, "wrench_coverage": pos_correct / 600,
              "balanced_accuracy": (neg_correct / 5000 + pos_correct / 600) / 2,
              "false_wrench": 5000 - neg_correct, "false_abstain": 600 - pos_correct,
              "latency_ms": {"p50": statistics.median(timings),
                             "p95": sorted_timing[int(.95 * (len(timings)-1))]},
              "categories": {key: dict(value) for key, value in categories.items()},
              "model_forwards": 0, "generated_tokens": 0, "tool_actions": 0,
              "production_enabled": False}
    output = root / "artifacts/system-one-readiness/mechanical-baseline.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("abstain_recall", "wrench_coverage",
                                                  "balanced_accuracy", "false_wrench",
                                                  "false_abstain", "latency_ms")}, indent=2))


if __name__ == "__main__":
    main()
