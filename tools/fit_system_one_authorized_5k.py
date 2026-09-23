"""Fit a Qwen layer-8 binary readout on owner-authorized synthetic cases.

This retires the old 5,600-case suite as evaluation material. Selection uses
only a group-held-out slice of that training corpus. The sealed final split
and any future replacement test suite are not opened.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.qwen_abstain import (LABELS, LEXICAL_SCHEMA, LAYER8_FEATURE,
                                        POLICY, PROFILE, char_tfidf_score,
                                        sha256_file)
from wrench_harness.system_one_preflight import explicit_abstain_reason


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def legacy_rows(base: Path, contrasts: Path) -> list[dict]:
    seen = set()
    rows = []
    for row in read_rows(base):
        key = " ".join(row["prompt"].casefold().split())
        if key not in seen:
            seen.add(key)
            rows.append(row)
    if len(rows) != 122:
        raise ValueError("legacy base inventory changed")
    extra = read_rows(contrasts)
    if len(extra) != 806 or any(" ".join(row["prompt"].casefold().split()) in seen
                                for row in extra):
        raise ValueError("legacy contrast inventory changed")
    return rows + extra


def rates(labels: np.ndarray, predictions: np.ndarray) -> dict:
    negative = labels == 0
    positive = ~negative
    unsafe = int(predictions[negative].sum())
    missed = int((~predictions[positive]).sum())
    abstain_recall = 1 - unsafe / int(negative.sum())
    wrench_coverage = 1 - missed / int(positive.sum())
    return {"rows": len(labels), "abstain": int(negative.sum()),
            "wrench": int(positive.sum()), "false_wrench": unsafe,
            "false_abstain": missed, "abstain_recall": abstain_recall,
            "wrench_coverage": wrench_coverage,
            "balanced_accuracy": (abstain_recall + wrench_coverage) / 2}


def main(args):
    import torch

    if args.output.exists():
        raise ValueError("output exists")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("cases_sha256") != sha256_file(args.cases):
        raise ValueError("approved suite hash mismatch")
    cases = read_rows(args.cases)
    if (len(cases) != 5600 or Counter(case["label"] for case in cases)
            != {"abstain": 5000, "wrench": 600}):
        raise ValueError("approved suite inventory changed")
    encoded = torch.load(args.features, map_location="cpu", weights_only=True)
    if (encoded.get("source_sha256") != sha256_file(args.cases)
            or encoded.get("layer") != 8
            or encoded.get("ids") != [case["id"] for case in cases]
            or not np.array_equal(encoded["labels"].numpy(),
                                  [int(case["label"] == "wrench") for case in cases])):
        raise ValueError("approved suite feature alignment mismatch")
    old = legacy_rows(args.base, args.contrasts)
    old_encoded = torch.load(args.old_features, map_location="cpu", weights_only=True)
    if (len(old_encoded["labels"]) != len(old)
            or old_encoded["checkpoint_sha256"] != encoded["checkpoint_sha256"]
            or old_encoded.get("source_sha256", {}).get(str(args.contrasts))
            != sha256_file(args.contrasts)
            or 8 not in old_encoded["layers"]):
        raise ValueError("legacy feature alignment mismatch")
    old_labels = np.array([int(row["expected_status"] == "accepted") for row in old])
    if not np.array_equal(old_labels, old_encoded["labels"].numpy()):
        raise ValueError("legacy feature labels mismatch")
    prompts = [row["prompt"] for row in old + cases]
    labels = np.concatenate([old_labels, encoded["labels"].numpy()])
    qwen = np.concatenate([old_encoded["layers"][8].numpy(),
                           encoded["features"].numpy()])
    groups = np.array([f"{case['label']}:{case['pattern_group']}" for case in cases])
    split = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=73)
    fit_local, cal_local = next(split.split(cases, groups=groups))
    fit = np.concatenate([np.arange(len(old)), len(old) + fit_local])
    cal = len(old) + cal_local
    if (len(set(groups[fit_local]) & set(groups[cal_local]))
            or set(labels[cal]) != {0, 1}
            or len(cal) < 500):
        raise ValueError("invalid template-group calibration split")
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3,
                                 max_features=20000, sublinear_tf=True)
    vectorizer.fit([prompts[index] for index in fit])
    sparse = vectorizer.transform(prompts)
    veto = np.array([explicit_abstain_reason(prompts[index]) is not None for index in cal])
    candidates = []
    for scale in (1.0, 4.0):
        features = hstack([sparse, csr_matrix(qwen * scale)], format="csr")
        for c in (.3, 1.0, 3.0, 10.0):
            model = LogisticRegression(C=c, max_iter=1000, class_weight="balanced")
            model.fit(features[fit], labels[fit])
            raw = model.predict_proba(features[cal])[:, 1] >= .5
            score = rates(labels[cal], raw & ~veto)
            candidates.append({"scale": scale, "c": c, **score})
    viable = [row for row in candidates if row["wrench_coverage"] >= .95]
    if viable:
        best = min(viable, key=lambda row: (row["false_wrench"],
                                            -row["balanced_accuracy"], row["c"], row["scale"]))
    else:
        best = max(candidates, key=lambda row: (row["balanced_accuracy"],
                                                -row["false_wrench"], -row["c"], -row["scale"]))
    final_vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5),
                                       min_df=3, max_features=20000,
                                       sublinear_tf=True)
    final_sparse = final_vectorizer.fit_transform(prompts)
    final_features = hstack([final_sparse, csr_matrix(qwen * best["scale"])],
                             format="csr")
    final = LogisticRegression(C=best["c"], max_iter=1000, class_weight="balanced")
    final.fit(final_features, labels)
    names = final_vectorizer.get_feature_names_out().tolist()
    width = len(names)
    weights = final.coef_[0]
    for index in np.linspace(0, len(prompts) - 1, 25, dtype=int):
        expected = float(weights[:width] @ final_sparse[index].toarray()[0])
        actual = char_tfidf_score(prompts[index], final_vectorizer.vocabulary_,
                                  final_vectorizer.idf_.tolist(),
                                  weights[:width].tolist())
        if abs(expected - actual) > 1e-5:
            raise ValueError("runtime lexical scorer disagrees with fit")
    packed = np.concatenate([final_vectorizer.idf_, weights[:width],
                             weights[width:] * best["scale"], final.intercept_]).astype("<f4").tobytes()
    artifact = {"schema": LEXICAL_SCHEMA, "labels": LABELS,
                "feature": LAYER8_FEATURE, "readout_layer": 8,
                "head_type": "char_tfidf_logistic", "width": int(qwen.shape[1]),
                "lexical_grams": names,
                "head_f32le_b64": base64.b64encode(packed).decode("ascii"),
                "head_sha256": hashlib.sha256(packed).hexdigest(),
                "threshold": .5, "max_tokens": 1024, "max_chars": 8192,
                "checkpoint_sha256": encoded["checkpoint_sha256"],
                "inference_profile": PROFILE,
                "policy_sha256": hashlib.sha256(POLICY.encode()).hexdigest(),
                "metadata": {"base_weights_frozen": True,
                             "real_workflow_validated": False,
                             "old_suite_retired_as_training": True,
                             "sources": {str(path): sha256_file(path) for path in
                                         (args.cases, args.features, args.base,
                                          args.contrasts, args.old_features)}}}
    args.output.mkdir(parents=True)
    artifact_path = args.output / "qwen-abstain-head.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True,
                                        allow_nan=False) + "\n", encoding="utf-8")
    if artifact_path.stat().st_size > 1_048_576:
        raise ValueError("artifact exceeds runtime size cap")
    receipt = {"schema": "wrench.system-one-authorized-5k-fit.v1",
               "status": "HEAD_FITTED_NOT_INDEPENDENTLY_EVALUATED",
               "training_rows": len(labels), "calibration_rows": len(cal),
               "group_heldout_training_rows": len(fit),
               "group_heldout_candidates": candidates,
               "selected": best, "lexical_features": width,
               "artifact_sha256": sha256_file(artifact_path),
               "artifact_bytes": artifact_path.stat().st_size,
               "approved_suite_sha256": sha256_file(args.cases),
               "sealed_final_read": False, "replacement_test_read": False,
               "provider_calls": 0, "production_enabled": False}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                                    encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "training_rows",
                                                   "selected", "artifact_bytes")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("phases/system-one-binary-5k-20260922/cases.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("phases/system-one-binary-5k-20260922/manifest.json"))
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--base", type=Path, default=Path("evals/wrench-expanded-v2/calibration.jsonl"))
    parser.add_argument("--contrasts", type=Path, default=Path("phases/system-one-policy-contrasts-v3-20260922/train.jsonl"))
    parser.add_argument("--old-features", type=Path, default=Path("artifacts/system-one-readiness/layer-probe-v3/features.pt"))
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
