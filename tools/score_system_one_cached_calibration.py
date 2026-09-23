"""Verify serialized sparse head and optional preflight on unsealed cached rows."""
from __future__ import annotations

import base64
from collections import Counter
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.qwen_abstain import char_tfidf_score
from wrench_harness.system_one_preflight import explicit_abstain_reason


def main():
    import torch
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts/system-one-readiness/sparse-v3"
    artifact = json.loads((output / "qwen-abstain-head.json").read_text(encoding="utf-8"))
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (root / "phases/system-one-policy-contrasts-v3-20260922/train.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    cache = torch.load(root / "artifacts/system-one-readiness/policy-contrasts-v3/features.pt",
                       map_location="cpu", weights_only=True)
    if len(rows) != len(cache["features"]):
        raise ValueError("row feature count mismatch")
    held = set(receipt["heldout_groups"])
    indexes = [i for i, row in enumerate(rows) if row["template_id"] in held]
    if len(indexes) != receipt["calibration_rows"]:
        raise ValueError("calibration split mismatch")
    packed = np.frombuffer(base64.b64decode(artifact["head_f32le_b64"]), dtype="<f4")
    n = len(artifact["lexical_grams"])
    idf = packed[:n].tolist()
    lex_weight = packed[n:n*2].tolist()
    qwen_weight = packed[n*2:-1]
    bias = float(packed[-1])
    vocab = {gram: i for i, gram in enumerate(artifact["lexical_grams"])}
    stats = {"model": Counter(), "model_plus_preflight": Counter()}
    for index in indexes:
        row = rows[index]
        score = (char_tfidf_score(row["prompt"], vocab, idf, lex_weight)
                 + float(np.dot(cache["features"][index].numpy(), qwen_weight)) + bias)
        probability = 1 / (1 + math.exp(-max(-80.0, min(80.0, score))))
        model = probability >= artifact["threshold"]
        hybrid = model and explicit_abstain_reason(row["prompt"]) is None
        expected = row["expected_status"] == "accepted"
        for name, decision in (("model", model), ("model_plus_preflight", hybrid)):
            stats[name]["rows"] += 1
            stats[name]["correct"] += int(decision == expected)
            stats[name]["abstain_rows"] += int(not expected)
            stats[name]["wrench_rows"] += int(expected)
            stats[name]["unsafe_passes"] += int(not expected and decision)
            stats[name]["false_abstains"] += int(expected and not decision)
    result = {"schema": "wrench.system-one-cached-calibration.v1",
              "scope": "unsealed template-held-out, post-selection, no suite/test data",
              "model": dict(stats["model"]),
              "model_plus_preflight": dict(stats["model_plus_preflight"]),
              "model_forwards_for_preflight_rejections": 0,
              "production_enabled": False}
    if abs(result["model"]["correct"] / result["model"]["rows"]
           - receipt["calibration"]["accuracy"]) > 1e-6:
        raise ValueError("serialized head does not reproduce fitter")
    (output / "calibration-verified.json").write_text(json.dumps(result, indent=2) + "\n",
                                                       encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
