"""Compare cached Qwen layers on the same unsealed template-held-out split."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(args):
    import torch
    seen = set()
    old = []
    for row in rows(args.base):
        norm = " ".join(row["prompt"].casefold().split())
        if norm not in seen:
            seen.add(norm)
            old.append(row)
    all_rows = old + rows(args.new_data)
    features = torch.load(args.features, map_location="cpu", weights_only=True)
    if len(all_rows) != len(features["labels"]):
        raise ValueError("row feature count mismatch")
    labels = features["labels"].numpy()
    held = set(json.loads(args.v2_receipt.read_text(encoding="utf-8"))["heldout_groups"])
    train = np.array([i for i, row in enumerate(all_rows) if i < len(old) or row["template_id"] not in held])
    cal = np.array([i for i, row in enumerate(all_rows) if i >= len(old) and row["template_id"] in held])
    prompts = [row["prompt"] for row in all_rows]
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3,
                                 max_features=20000, sublinear_tf=True)
    vectorizer.fit([prompts[i] for i in train])
    sparse = vectorizer.transform(prompts)
    results = []
    for layer, tensor in features["layers"].items():
        qwen = tensor.numpy()
        combined = hstack([sparse, csr_matrix(qwen * 4)], format="csr")
        classifier = LogisticRegression(C=10, max_iter=1000, class_weight="balanced")
        classifier.fit(combined[train], labels[train])
        pred = classifier.predict(combined[cal])
        neg = labels[cal] == 0
        pos = ~neg
        results.append({"layer": layer, "accuracy": float((pred == labels[cal]).mean()),
                        "unsafe_passes": int(pred[neg].sum()),
                        "abstain_rows": int(neg.sum()),
                        "wrench_coverage": float(pred[pos].mean())})
    results.sort(key=lambda item: (-item["accuracy"], item["unsafe_passes"]))
    report = {"scope": "unsealed template-held-out model selection; not independent",
              "rows": len(all_rows), "training_rows": len(train), "calibration_rows": len(cal),
              "results": results, "suite_5600_read": False, "final_split_read": False}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("evals/wrench-expanded-v2/calibration.jsonl"))
    parser.add_argument("--new-data", type=Path, default=Path("phases/system-one-policy-contrasts-v3-20260922/train.jsonl"))
    parser.add_argument("--features", type=Path, default=Path("artifacts/system-one-readiness/layer-probe-v3/features.pt"))
    parser.add_argument("--v2-receipt", type=Path, default=Path("artifacts/system-one-readiness/sparse-v3/receipt.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/system-one-readiness/layer-probe-v3/results.json"))
    main(parser.parse_args())
