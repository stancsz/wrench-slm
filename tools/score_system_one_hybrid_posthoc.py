"""Posthoc diagnostic: existing mechanical abstain veto plus frozen Qwen decisions."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.mechanical import mechanical_route


def main():
    root = Path(__file__).resolve().parents[1]
    cases = [json.loads(line) for line in (root / "phases/system-one-binary-5k-20260922/cases.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    predictions = [json.loads(line) for line in (root / "artifacts/system-one-readiness/sparse-v1/evaluation-5k/predictions.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    if len(cases) != 5600 or len(predictions) != 5600:
        raise ValueError("posthoc data length mismatch")
    groups = defaultdict(Counter)
    override_counts = Counter()
    for case, prediction in zip(cases, predictions):
        if case["id"] != prediction["id"]:
            raise ValueError("prediction alignment failed")
        route = mechanical_route(case["prompt"], allowed_root=root)
        explicit_abstain = route is not None and route.get("status") == "abstain"
        decision = "abstain" if explicit_abstain else prediction["decision"]
        if explicit_abstain:
            override_counts[case["label"]] += 1
        correct = decision == ("not_abstain" if case["label"] == "wrench" else "abstain")
        group = groups[case["category"]]
        group["rows"] += 1
        group["correct"] += int(correct)
        group["false_wrench"] += int(case["label"] == "abstain" and not correct)
        group["false_abstain"] += int(case["label"] == "wrench" and not correct)
    false_wrench = sum(v["false_wrench"] for v in groups.values())
    false_abstain = sum(v["false_abstain"] for v in groups.values())
    result = {"scope": "posthoc same-suite diagnostic, no independent accuracy claim",
              "false_wrench": false_wrench, "false_abstain": false_abstain,
              "abstain_recall": 1 - false_wrench / 5000,
              "wrench_coverage": 1 - false_abstain / 600,
              "balanced_accuracy": (1 - false_wrench / 5000 + 1 - false_abstain / 600) / 2,
              "mechanical_overrides": dict(override_counts),
              "categories": {key: dict(value) for key, value in groups.items()}}
    output = root / "artifacts/system-one-readiness/hybrid-posthoc.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("false_wrench", "false_abstain",
                                                  "abstain_recall", "wrench_coverage",
                                                  "balanced_accuracy", "mechanical_overrides")}, indent=2))


if __name__ == "__main__":
    main()
