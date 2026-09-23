"""Compare small lexical readouts on unsealed, group-heldout Qwen training rows.

Never opens the 5,600-case suite, the independent 60, or the sealed final split.
This is candidate selection, not an independent accuracy claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix


def load_rows(base: Path, extra: Path) -> list[dict]:
    rows = [json.loads(line) for line in base.read_text(encoding="utf-8").splitlines() if line]
    rows += [json.loads(line) for line in extra.read_text(encoding="utf-8").splitlines() if line]
    seen = set()
    result = []
    for row in rows:
        norm = " ".join(row["prompt"].casefold().split())
        if norm not in seen:
            seen.add(norm)
            result.append(row)
    return result


def score(model, x, y, indices):
    truth = y[indices]
    prediction = model.predict(x[indices])
    tn, fp, fn, tp = confusion_matrix(truth, prediction, labels=[0, 1]).ravel()
    return {"accuracy": round(float((prediction == truth).mean()), 4),
            "unsafe_passes": int(fp), "abstain_total": int(tn + fp),
            "wrench_coverage": round(float(tp / (tp + fn)), 4),
            "balanced_accuracy": round(float((tn / (tn + fp) + tp / (tp + fn)) / 2), 4)}


def main(args):
    import torch
    checkpoint = torch.load(args.features, map_location="cpu", weights_only=True)
    rows = load_rows(args.base, args.extra)
    if len(rows) * 2 != len(checkpoint["labels"]):
        raise ValueError("row and Qwen feature count differ")
    prompts = [row["prompt"] for row in rows for _ in (0, 1)]
    labels = checkpoint["labels"].numpy()
    train = np.array(checkpoint["train_indexes"], dtype=int)
    cal = np.array(checkpoint["calibration_indexes"], dtype=int)
    plain = cal[cal % 2 == 1]
    if len(set(train).intersection(cal)) or not {0, 1} <= set(labels[plain]):
        raise ValueError("invalid split")
    qwen = checkpoint["features"].numpy()
    report = {"scope": "unsealed group-heldout candidate selection", "rows": len(rows),
              "training_rows": len(train) // 2, "calibration_rows": len(cal) // 2,
              "models": []}
    for kind in ("word", "char"):
        vectorizer = (TfidfVectorizer(ngram_range=(1, 2), min_df=2,
                                    token_pattern=r"(?u)\b\w+\b", sublinear_tf=True)
                      if kind == "word" else
                      TfidfVectorizer(analyzer="char", ngram_range=(2, 5),
                                      min_df=3, max_features=20000, sublinear_tf=True))
        sparse = vectorizer.fit_transform([prompts[i] for i in train])
        all_sparse = vectorizer.transform(prompts)
        for qwen_scale in (0, .25, 1, 4):
            features = all_sparse if qwen_scale == 0 else hstack(
                [all_sparse, csr_matrix(qwen * qwen_scale)], format="csr")
            for c in (.1, 1, 10):
                clf = LogisticRegression(C=c, max_iter=1000, class_weight="balanced")
                clf.fit(features[train], labels[train])
                item = {"vectorizer": kind, "lexical_features": int(all_sparse.shape[1]),
                        "qwen_scale": qwen_scale, "C": c,
                        "plain": score(clf, features, labels, plain),
                        "all_formats": score(clf, features, labels, cal)}
                report["models"].append(item)
    report["models"].sort(key=lambda x: (-x["plain"]["balanced_accuracy"],
                                            x["plain"]["unsafe_passes"],
                                            x["lexical_features"]))
    best = report["models"][0]
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3,
                                 max_features=20000, sublinear_tf=True)
    vectorizer.fit([prompts[i] for i in train])
    all_sparse = vectorizer.transform(prompts)
    features = hstack([all_sparse, csr_matrix(qwen * 4)], format="csr")
    classifier = LogisticRegression(C=10, max_iter=1000, class_weight="balanced")
    classifier.fit(features[train], labels[train])
    probabilities = classifier.predict_proba(features[plain])[:, 1]
    report["best_plain_errors"] = [
        {"id": rows[index // 2]["id"], "template_id": rows[index // 2]["template_id"],
         "prompt": prompts[index], "expected": "not_abstain" if labels[index] else "abstain",
         "prob_not_abstain": round(float(probability), 6)}
        for index, probability in zip(plain, probabilities)
        if (probability >= .5) != bool(labels[index])]
    negatives = probabilities[labels[plain] == 0]
    positives = probabilities[labels[plain] == 1]
    safe_threshold = float(max(negatives) + 1e-6)
    report["best_zero_unsafe_threshold"] = {
        "threshold": round(safe_threshold, 6),
        "wrench_coverage": round(float((positives >= safe_threshold).mean()), 4),
        "abstain_cases": int(len(negatives)), "wrench_cases": int(len(positives))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["models"][:12], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("evals/wrench-expanded-v2/calibration.jsonl"))
    parser.add_argument("--extra", type=Path, default=Path("phases/system-one-training-augmented-20260922/train-extra.jsonl"))
    parser.add_argument("--features", type=Path, default=Path("artifacts/system-one-readiness/mlp-v1/training-features.pt"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/system-one-readiness/sparse-probe.json"))
    main(parser.parse_args())
