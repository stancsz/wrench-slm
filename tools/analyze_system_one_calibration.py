"""Explain errors on the unsealed group-heldout calibration vectors only."""
from __future__ import annotations

from collections import Counter, defaultdict
import base64
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evals/wrench-expanded-v2/calibration.jsonl"
EXTRA = ROOT / "phases/system-one-training-augmented-20260922/train-extra.jsonl"
RUN = ROOT / "artifacts/system-one-readiness/mlp-v1"


def read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    rows = read(BASE) + read(EXTRA)
    retained, seen = [], set()
    for row in rows:
        key = " ".join(row["prompt"].casefold().split())
        if key not in seen:
            retained.append(row)
            seen.add(key)
    rows = retained
    data = torch.load(RUN / "training-features.pt", map_location="cpu", weights_only=True)
    x, y, ci = data["features"], data["labels"], data["calibration_indexes"]
    assert len(rows) * 2 == len(x)
    obj = json.loads((RUN / "qwen-abstain-head.json").read_text(encoding="utf-8"))
    width, hidden = obj["width"], obj["hidden_width"]
    raw = base64.b64decode(obj["head_f32le_b64"])
    values = torch.frombuffer(bytearray(raw), dtype=torch.float32)
    offset = width * hidden
    w1 = values[:offset].reshape(hidden, width)
    b1 = values[offset:offset + hidden]
    offset += hidden
    w2 = values[offset:offset + hidden*2].reshape(2, hidden)
    b2 = values[offset + hidden*2:]
    with torch.inference_mode():
        logits = torch.nn.functional.linear(torch.nn.functional.gelu(
            torch.nn.functional.linear(x[ci], w1, b1)), w2, b2)
        prediction = logits.argmax(-1)
        probs = logits.softmax(-1)[:, 1]
    grouped = defaultdict(Counter)
    errors = []
    for position, feature_index in enumerate(ci):
        if feature_index % 2 != 1:
            continue
        row = rows[feature_index // 2]
        group = row["template_id"]
        grouped[group]["rows"] += 1
        incorrect = prediction[position] != y[feature_index]
        grouped[group]["errors"] += int(incorrect)
        if incorrect:
            errors.append({"id": row["id"], "template_id": group, "prompt": row["prompt"],
                           "expected": row["expected_status"], "prob_wrench": float(probs[position])})
    summary = {"schema": "wrench.system-one-calibration-error-analysis.v1",
               "scope": "unsealed calibration plain-user variant only; no independent/test/final data",
               "rows": sum(value["rows"] for value in grouped.values()),
               "errors": len(errors),
               "worst_groups": [{"group": name, **dict(value)} for name, value in
                                sorted(grouped.items(), key=lambda item: (-item[1]["errors"], item[0]))[:20]],
               "error_examples": errors[:40]}
    (RUN / "calibration-error-analysis.json").write_text(json.dumps(summary, indent=2,
                                                   ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("rows", "errors", "worst_groups")}, indent=2))


if __name__ == "__main__":
    main()
