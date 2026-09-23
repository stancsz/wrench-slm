"""Choose a two-token margin on unsealed calibration, report development."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def measure(rows, variant, threshold):
    positives = [row for row in rows if row["expected"] == "wrench"]
    negatives = [row for row in rows if row["expected"] == "abstain"]
    decide = lambda row: row[variant][0] - row[variant][1] >= threshold
    tp = sum(decide(row) for row in positives)
    fp = sum(decide(row) for row in negatives)
    return {"accuracy": (tp + len(negatives)-fp)/len(rows), "balanced_accuracy":
            (tp/len(positives)+(len(negatives)-fp)/len(negatives))/2,
            "wrench_coverage": tp/len(positives), "false_wrench": fp,
            "wrench_rows": len(positives), "abstain_rows": len(negatives)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.scores.read_text(encoding="utf-8"))
    results = {}
    for policy in ("base", "examples"):
        calibration = data[f"{policy}_calibration"]
        development = data[f"{policy}_development"]
        for variant in ("plain", "spaced"):
            margins = sorted({row[variant][0]-row[variant][1] for row in calibration})
            thresholds = [margins[0] - 1] + [(a+b)/2 for a,b in zip(margins, margins[1:])] + [margins[-1]+1]
            ranked = [(measure(calibration, variant, value), value) for value in thresholds]
            # Balanced accuracy chooses a threshold without favoring the
            # calibration class mix. Favor fewer unsafe passes on exact ties.
            best, threshold = max(ranked, key=lambda item: (item[0]["balanced_accuracy"],
                                                          -item[0]["false_wrench"],
                                                          item[0]["wrench_coverage"]))
            results[f"{policy}_{variant}"] = {"threshold": threshold,
                                               "calibration": best,
                                               "development": measure(development, variant, threshold),
                                               "calibration_margin_range": [margins[0], margins[-1]]}
    receipt = {"schema": "wrench.verbalizer-unsealed-threshold.v1",
               "scope": "calibration threshold, unsealed development report",
               "independent_60_read": False, "suite_5600_read": False, "final_split_read": False,
               "results": results}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
