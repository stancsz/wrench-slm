"""Fit a layer-8 Qwen sparse readout on audited unsealed contrasts.

One of four new template groups per Wrench boundary is held out. The original
5,600-case suite is not opened by this fitter.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wrench_harness.qwen_abstain import (LABELS, LEXICAL_SCHEMA, POLICY,
                                        LAYER8_FEATURE, PROFILE, char_tfidf_score,
                                        sha256_file)


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(args):
    import torch
    if args.output.exists():
        raise ValueError("output exists")
    base_rows = read_rows(args.base)
    seen = set()
    old_rows = []
    for row in base_rows:
        norm = " ".join(row["prompt"].casefold().split())
        if norm not in seen:
            seen.add(norm)
            old_rows.append(row)
    if len(old_rows) != 122:
        raise ValueError("base row inventory changed")
    new_rows = read_rows(args.new_data)
    audit = json.loads((args.new_data.parent / "audit.json").read_text(encoding="utf-8"))
    if (audit.get("status") != "STRUCTURAL_PASS_HUMAN_LABEL_REVIEW_PENDING"
            or audit.get("training_sha256") != sha256_file(args.new_data)):
        raise ValueError("corrected training audit missing or stale")
    if len(new_rows) != 806 or any(" ".join(row["prompt"].casefold().split()) in seen
                                    for row in new_rows):
        raise ValueError("new training rows overlap old rows")
    cached = torch.load(args.layer_features, map_location="cpu", weights_only=True)
    if (len(old_rows) + len(new_rows) != len(cached["labels"])
            or cached.get("source_sha256", {}).get(str(args.new_data)) != sha256_file(args.new_data)
            or 8 not in cached.get("layers", {})):
        raise ValueError("training feature alignment or checkpoint mismatch")
    prompts = [row["prompt"] for row in old_rows + new_rows]
    labels = np.array([int(row["expected_status"] == "accepted") for row in old_rows + new_rows])
    qwen = cached["layers"][8].numpy()
    if not np.array_equal(labels, cached["labels"].numpy()):
        raise ValueError("training feature label mismatch")
    family_groups = {}
    for row in new_rows:
        group = row["template_id"]
        family = group.rsplit("_", 1)[0]
        family_groups.setdefault(family, set()).add(group)
    if len(family_groups) != 10 or any(len(groups) != 4 for groups in family_groups.values()):
        raise ValueError("unexpected new template-group structure")
    held = {random.Random(f"47-{family}").choice(sorted(groups))
            for family, groups in family_groups.items()}
    train = np.array([index for index, row in enumerate(old_rows + new_rows)
                      if index < len(old_rows) or row["template_id"] not in held])
    cal = np.array([index for index, row in enumerate(old_rows + new_rows)
                    if index >= len(old_rows) and row["template_id"] in held])
    if not {0, 1} <= set(labels[cal]) or len(cal) < 100:
        raise ValueError("new group-held-out calibration inadequate")
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3,
                                 max_features=20000, sublinear_tf=True)
    vectorizer.fit([prompts[i] for i in train])
    sparse = vectorizer.transform(prompts)
    features = hstack([sparse, csr_matrix(qwen * 4)], format="csr")
    classifier = LogisticRegression(C=10, max_iter=1000, class_weight="balanced")
    classifier.fit(features[train], labels[train])
    probabilities = classifier.predict_proba(features[cal])[:, 1]
    predictions = probabilities >= .5
    negative = labels[cal] == 0
    positive = ~negative
    names = vectorizer.get_feature_names_out().tolist()
    lexical_width = len(names)
    weights = classifier.coef_[0]
    for index in cal:
        expected = float(weights[:lexical_width] @ sparse[index].toarray()[0])
        actual = char_tfidf_score(prompts[index], vectorizer.vocabulary_,
                                  vectorizer.idf_.tolist(), weights[:lexical_width].tolist())
        if abs(expected - actual) > 1e-5:
            raise ValueError("runtime lexical computation disagrees with training")
    packed = np.concatenate([vectorizer.idf_, weights[:lexical_width],
                             weights[lexical_width:] * 4, classifier.intercept_]).astype("<f4").tobytes()
    artifact = {"schema": LEXICAL_SCHEMA, "labels": LABELS, "feature": LAYER8_FEATURE,
                "readout_layer": 8, "head_type": "char_tfidf_logistic", "width": int(qwen.shape[1]),
                "lexical_grams": names, "head_f32le_b64": base64.b64encode(packed).decode("ascii"),
                "head_sha256": hashlib.sha256(packed).hexdigest(), "threshold": .5,
                "max_tokens": 1024, "max_chars": 8192,
                "checkpoint_sha256": cached["checkpoint_sha256"],
                "inference_profile": PROFILE, "policy_sha256": hashlib.sha256(POLICY.encode()).hexdigest(),
                "metadata": {"base_weights_frozen": True, "real_workflow_validated": False,
                             "sources": {str(path): sha256_file(path) for path in (
                                 args.base, args.new_data, args.layer_features)}}}
    args.output.mkdir(parents=True)
    artifact_path = args.output / "qwen-abstain-head.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True,
                                        allow_nan=False) + "\n", encoding="utf-8")
    if artifact_path.stat().st_size > 1_048_576:
        raise ValueError("artifact exceeds runtime size cap")
    missed = [
        {"id": (old_rows + new_rows)[index]["id"],
         "template_id": (old_rows + new_rows)[index]["template_id"],
         "prompt": prompts[index], "expected": "not_abstain" if labels[index] else "abstain",
         "prob_not_abstain": round(float(prob), 6)}
        for index, prob, prediction in zip(cal, probabilities, predictions)
        if prediction != bool(labels[index])]
    receipt = {"schema": "wrench.system-one-layer8-fit.v1", "status": "CALIBRATED_HEAD_READY",
               "scope": "new authored groups held out; original suite not read",
               "training_rows": len(train), "calibration_rows": len(cal),
               "heldout_groups": sorted(held), "lexical_features": lexical_width,
               "artifact_sha256": sha256_file(artifact_path),
               "artifact_bytes": artifact_path.stat().st_size,
               "calibration": {"accuracy": float((predictions == labels[cal]).mean()),
                               "abstain_recall": float((~predictions[negative]).mean()),
                               "wrench_coverage": float(predictions[positive].mean()),
                               "unsafe_passes": int(predictions[negative].sum()),
                               "false_abstains": int((~predictions[positive]).sum()),
                               "labels": dict(Counter("wrench" if label else "abstain" for label in labels[cal]))},
               "calibration_misses": missed, "final_split_read": False,
               "suite_5600_read": False, "provider_calls": 0, "production_enabled": False}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "training_rows", "calibration_rows",
                                                   "calibration", "artifact_bytes")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("evals/wrench-expanded-v2/calibration.jsonl"))
    parser.add_argument("--new-data", type=Path, default=Path("phases/system-one-policy-contrasts-v3-20260922/train.jsonl"))
    parser.add_argument("--layer-features", type=Path, default=Path("artifacts/system-one-readiness/layer-probe-v3/features.pt"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/system-one-readiness/layer8-v1"))
    main(parser.parse_args())
