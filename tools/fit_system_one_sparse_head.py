"""Fit Qwen plus char TF-IDF binary head on unsealed group-heldout data."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.qwen_abstain import (LABELS, LEXICAL_SCHEMA, POLICY,
                                        POLICY_FEATURE, PROFILE, char_tfidf_score,
                                        sha256_file)


def rows_from(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(args):
    import torch
    if args.output.exists():
        raise ValueError("output exists")
    rows = rows_from(args.base) + rows_from(args.extra)
    seen = set()
    unique = []
    for row in rows:
        norm = " ".join(row["prompt"].casefold().split())
        if norm not in seen:
            seen.add(norm)
            unique.append(row)
    rows = unique
    cache = torch.load(args.features, map_location="cpu", weights_only=True)
    if len(rows) * 2 != len(cache["labels"]):
        raise ValueError("feature alignment mismatch")
    train = np.array(cache["train_indexes"], dtype=int)
    cal = np.array(cache["calibration_indexes"], dtype=int)
    plain = cal[cal % 2 == 1]
    prompts = [row["prompt"] for row in rows for _ in (0, 1)]
    labels = cache["labels"].numpy()
    qwen = cache["features"].numpy()
    if not np.array_equal(labels, np.array([int(row["expected_status"] == "accepted")
                                              for row in rows for _ in (0, 1)])):
        raise ValueError("label alignment mismatch")
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3,
                                 max_features=20000, sublinear_tf=True)
    vectorizer.fit([prompts[i] for i in train])
    sparse = vectorizer.transform(prompts)
    features = hstack([sparse, csr_matrix(qwen * 4)], format="csr")
    classifier = LogisticRegression(C=10, max_iter=1000, class_weight="balanced")
    classifier.fit(features[train], labels[train])
    pred = classifier.predict(features[plain])
    neg = labels[plain] == 0
    pos = ~neg
    names = vectorizer.get_feature_names_out().tolist()
    lexical_width = len(names)
    weights = classifier.coef_[0]
    packed = np.concatenate([vectorizer.idf_, weights[:lexical_width],
                             weights[lexical_width:] * 4, classifier.intercept_]).astype("<f4").tobytes()
    payload = {"schema": LEXICAL_SCHEMA, "labels": LABELS, "feature": POLICY_FEATURE,
               "head_type": "char_tfidf_logistic", "width": int(qwen.shape[1]),
               "lexical_grams": names, "head_f32le_b64": base64.b64encode(packed).decode("ascii"),
               "head_sha256": hashlib.sha256(packed).hexdigest(),
               "threshold": .5, "max_tokens": 1024, "max_chars": 8192,
               "checkpoint_sha256": cache["checkpoint_sha256"],
               "inference_profile": PROFILE, "policy_sha256": hashlib.sha256(POLICY.encode()).hexdigest(),
               "metadata": {"base_weights_frozen": True, "real_workflow_validated": False,
                            "sources": {str(path): sha256_file(path) for path in (args.base, args.extra, args.features)}}}
    for index in plain:
        lexical_expected = float(weights[:lexical_width] @ sparse[index].toarray()[0])
        actual = char_tfidf_score(prompts[index], vectorizer.vocabulary_,
                                  vectorizer.idf_.tolist(), weights[:lexical_width].tolist())
        if abs(actual - lexical_expected) > 1e-5:
            raise ValueError("runtime lexical score does not match fitted vectorizer")
    args.output.mkdir(parents=True)
    artifact = args.output / "qwen-abstain-head.json"
    artifact.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n",
                        encoding="utf-8")
    if artifact.stat().st_size > 1_048_576:
        raise ValueError("artifact exceeds runtime size cap")
    receipt = {"schema": "wrench.system-one-sparse-fit.v1", "status": "CALIBRATED_HEAD_READY",
               "scope": "unsealed group-heldout candidate selection; no independent evaluation",
               "artifact_sha256": sha256_file(artifact), "artifact_bytes": artifact.stat().st_size,
               "lexical_features": lexical_width, "qwen_width": int(qwen.shape[1]),
               "training_rows": len(train) // 2, "calibration_rows": len(plain),
               "calibration_plain": {"accuracy": float((pred == labels[plain]).mean()),
                                     "unsafe_passes": int(pred[neg].sum()),
                                     "abstain_total": int(neg.sum()),
                                     "wrench_coverage": float(pred[pos].mean())},
               "model_forwards_per_decision": 1, "generated_tokens": 0,
               "suite_5600_read": False, "independent_60_read": False,
               "final_split_read": False, "production_enabled": False}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("evals/wrench-expanded-v2/calibration.jsonl"))
    parser.add_argument("--extra", type=Path, default=Path("phases/system-one-training-augmented-20260922/train-extra.jsonl"))
    parser.add_argument("--features", type=Path, default=Path("artifacts/system-one-readiness/mlp-v1/training-features.pt"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/system-one-readiness/sparse-v1"))
    main(parser.parse_args())
