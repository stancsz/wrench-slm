"""Check file and line bounds for authored positive policy contrasts."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re


def main():
    root = Path(__file__).resolve().parents[1]
    data = root / "phases/system-one-policy-contrasts-v3-20260922/train.jsonl"
    manifest = json.loads((data.parent / "manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in data.read_text(encoding="utf-8").splitlines() if line]
    paths = json.loads((root / "phases/system-one-training-augmented-20260922/manifest.json").read_text(
        encoding="utf-8"))["substitution_paths"]
    checked = Counter()
    errors = []
    for row in rows:
        if row["expected_status"] != "accepted":
            continue
        prompt = row["prompt"]
        included = [path for path in paths if path in prompt]
        if len(included) > 1:
            errors.append(f"multiple tracked paths: {row['id']}")
            continue
        if not included:
            checked["non_file_positive"] += 1
            continue
        path = root / included[0]
        if not path.is_file():
            errors.append(f"missing file: {row['id']}")
            continue
        checked["file_positive"] += 1
        for number in re.findall(r"\b([0-9][0-9,]*)\s*bytes?\b", prompt, re.IGNORECASE):
            cap = int(number.replace(",", ""))
            if cap < path.stat().st_size:
                errors.append(f"byte cap below file size: {row['id']}")
            checked["byte_bound_checked"] += 1
        for start, end in re.findall(r"\blines?\s*(\d+)\s*(?:to|through|-)\s*(\d+)",
                                     prompt, re.IGNORECASE):
            length = len(path.read_text(encoding="utf-8").splitlines())
            if not 1 <= int(start) <= int(end) <= length:
                errors.append(f"line range outside file: {row['id']}")
            checked["line_bound_checked"] += 1
    receipt = {"schema": "wrench.system-one-policy-contrast-audit.v1",
               "status": "STRUCTURAL_PASS_HUMAN_LABEL_REVIEW_PENDING" if not errors else "FAIL",
               "training_sha256": manifest["sha256"], "rows": len(rows),
               "positive_rows": sum(row["expected_status"] == "accepted" for row in rows),
               "checks": dict(checked), "errors": errors,
               "final_split_read": False, "suite_labels_used": False}
    (data.parent / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    if errors:
        raise ValueError("policy contrast structural audit failed")


if __name__ == "__main__":
    main()
