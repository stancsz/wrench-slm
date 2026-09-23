"""Audit a revised abstain-only preflight against an already consumed suite.

This is a posthoc regression, never a fresh holdout or a latency measurement.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.system_one_preflight import explicit_abstain_reason


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("output exists")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
    if (digest(args.cases) != manifest["cases_sha256"]
            or evaluation["cases_sha256"] != manifest["cases_sha256"]
            or evaluation["status"] != "CLASSIFIER_SUITE_COMPLETE"
            or evaluation["case_count"] != 5600):
        raise ValueError("consumed suite receipt mismatch")
    cases = rows(args.cases)
    predictions = rows(args.predictions)
    if (len(cases) != 5600 or len(predictions) != 5600
            or [row["id"] for row in cases] != [row["id"] for row in predictions]):
        raise ValueError("prediction alignment mismatch")
    before = Counter()
    after = Counter()
    newly_vetoed = Counter()
    reasons = Counter()
    for case, prediction in zip(cases, predictions):
        expected = "not_abstain" if case["label"] == "wrench" else "abstain"
        if not prediction["correct"] == (prediction["decision"] == expected):
            raise ValueError("stored prediction correctness mismatch")
        reason = explicit_abstain_reason(case["prompt"])
        decision = "abstain" if reason else prediction["decision"]
        before[(case["label"], prediction["decision"])] += 1
        after[(case["label"], decision)] += 1
        if reason and prediction["decision"] != "abstain":
            newly_vetoed[case["label"]] += 1
            reasons[reason] += 1
    if (before[("abstain", "not_abstain")] != evaluation["false_wrench"]
            or before[("wrench", "abstain")] != evaluation["false_abstain"]):
        raise ValueError("recorded errors disagree with evaluation receipt")
    correct = after[("abstain", "abstain")] + after[("wrench", "not_abstain")]
    result = {
        "schema": "wrench.system-one-replacement-posthoc.v1",
        "status": "POSTHOC_CONSUMED_SUITE_REGRESSION",
        "cases_sha256": digest(args.cases),
        "predictions_sha256": digest(args.predictions),
        "evaluation_sha256": digest(args.evaluation),
        "preflight_sha256": digest(Path(__file__).resolve().parents[1] /
                                   "src/wrench_harness/system_one_preflight.py"),
        "rows": 5600, "newly_vetoed": dict(newly_vetoed),
        "new_veto_reasons": dict(reasons),
        "false_wrench_before": before[("abstain", "not_abstain")],
        "false_wrench_after": after[("abstain", "not_abstain")],
        "false_abstain_before": before[("wrench", "abstain")],
        "false_abstain_after": after[("wrench", "abstain")],
        "abstain_recall_after": after[("abstain", "abstain")] / 5000,
        "wrench_coverage_after": after[("wrench", "not_abstain")] / 600,
        "balanced_accuracy_after": (after[("abstain", "abstain")] / 5000 +
                                    after[("wrench", "not_abstain")] / 600) / 2,
        "overall_accuracy_after": correct / 5600,
        "latency_measured_after_change": False,
        "independent_holdout": False,
        "real_workflow_validated": False,
        "production_enabled": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
