"""Posthoc same-suite check of abstain-only preflight over frozen predictions."""
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.system_one_preflight import explicit_abstain_reason


def main(args):
    root = Path(__file__).resolve().parents[1]
    cases = [json.loads(line) for line in (root / "phases/system-one-binary-5k-20260922/cases.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    predictions = [json.loads(line) for line in args.predictions.read_text(
        encoding="utf-8").splitlines() if line]
    if len(cases) != 5600 or len(predictions) != 5600:
        raise ValueError("case and prediction counts differ")
    groups = defaultdict(Counter)
    vetoes = Counter()
    for case, prediction in zip(cases, predictions):
        if case["id"] != prediction["id"]:
            raise ValueError("case and prediction order differ")
        reason = explicit_abstain_reason(case["prompt"])
        if reason:
            vetoes[(case["label"], reason)] += 1
        result = "abstain" if reason else prediction["decision"]
        expected = "not_abstain" if case["label"] == "wrench" else "abstain"
        bucket = groups[case["category"]]
        bucket["rows"] += 1
        bucket["correct"] += int(result == expected)
        bucket["false_wrench"] += int(case["label"] == "abstain" and result != expected)
        bucket["false_abstain"] += int(case["label"] == "wrench" and result != expected)
    false_wrench = sum(bucket["false_wrench"] for bucket in groups.values())
    false_abstain = sum(bucket["false_abstain"] for bucket in groups.values())
    result = {"scope": "posthoc regression diagnostic on consumed suite",
              "false_wrench": false_wrench, "false_abstain": false_abstain,
              "abstain_recall": 1 - false_wrench / 5000,
              "wrench_coverage": 1 - false_abstain / 600,
              "balanced_accuracy": (1 - false_wrench / 5000 + 1 - false_abstain / 600) / 2,
              "vetoes": {f"{label}:{reason}": count for (label, reason), count in vetoes.items()},
              "categories": {key: dict(value) for key, value in groups.items()},
              "production_enabled": False}
    output = args.output
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("false_wrench", "false_abstain",
                                                  "abstain_recall", "wrench_coverage",
                                                  "balanced_accuracy", "vetoes")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path,
                        default=Path("artifacts/system-one-readiness/sparse-v1/evaluation-5k/predictions.jsonl"))
    parser.add_argument("--output", type=Path,
                        default=Path("artifacts/system-one-readiness/preflight-posthoc.json"))
    main(parser.parse_args())
