"""Validate redacted, labeled real Wrench requests and isolate a future holdout.

This tool is local-only. It never reads the repository's sealed final split,
calls a provider, prints prompt text, or enables the binary gate.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


SCHEMA = "wrench.system-one-real-intake.v1"
LABELS = {"abstain", "not_abstain"}
SENSITIVE = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk-|ghp_|gho_)[A-Za-z0-9_-]{16,}\b|\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{16,}\b", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
)


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def private_path(root: Path, path: Path) -> Path:
    private = (root / "data/private").resolve()
    resolved = (path if path.is_absolute() else root / path).resolve()
    if resolved != private and private not in resolved.parents:
        raise ValueError("real request input and output must stay under data/private")
    return resolved


def parse_rows(raw: bytes) -> tuple[list[dict], dict]:
    rows = []
    seen_ids = set()
    seen_prompts = {}
    groups = defaultdict(Counter)
    duplicate_prompts = 0
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or set(row) - {
            "request_id", "workflow_id", "prompt", "label", "redacted",
            "source", "label_source"}:
            raise ValueError(f"invalid row fields at line {line_number}")
        request_id, workflow_id, prompt = (row.get(key) for key in
                                           ("request_id", "workflow_id", "prompt"))
        if (not isinstance(request_id, str) or not 1 <= len(request_id) <= 128
                or not isinstance(workflow_id, str) or not 1 <= len(workflow_id) <= 128
                or not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 8192
                or row.get("label") not in LABELS or row.get("redacted") is not True
                or row.get("source") != "real_wrench"
                or row.get("label_source") not in {"human_review", "verified_oracle"}):
            raise ValueError(f"invalid real request row at line {line_number}")
        if request_id in seen_ids:
            raise ValueError(f"duplicate request_id at line {line_number}")
        seen_ids.add(request_id)
        if any(pattern.search(prompt) for pattern in SENSITIVE):
            raise ValueError(f"potential sensitive text at line {line_number}; redact before intake")
        norm = normalize(prompt)
        prior = seen_prompts.get(norm)
        if prior is not None:
            if prior != row["label"]:
                raise ValueError(f"conflicting duplicate label at line {line_number}")
            duplicate_prompts += 1
            continue
        seen_prompts[norm] = row["label"]
        groups[workflow_id][row["label"]] += 1
        rows.append({"request_id_hash": sha256(request_id.encode()),
                     "workflow_id_hash": sha256(workflow_id.encode()),
                     "prompt": prompt, "label": row["label"],
                     "label_source": row["label_source"]})
    if len(rows) < 40 or len(groups) < 20 or set(seen_prompts.values()) != LABELS:
        raise ValueError("need at least 40 unique rows, 20 workflows, and both labels")
    return rows, {"unique_rows": len(rows), "workflow_groups": len(groups),
                  "duplicate_prompts_removed": duplicate_prompts,
                  "labels": dict(Counter(row["label"] for row in rows)),
                  "label_sources": dict(Counter(row["label_source"] for row in rows))}


def reject_frozen_suite_overlap(root: Path, rows: list[dict]) -> None:
    """Keep the authored, consumed diagnostic suite out of the real corpus."""
    suite = root / "phases/system-one-binary-5k-20260922/cases.jsonl"
    if not suite.is_file():
        raise ValueError("frozen diagnostic suite is missing; cannot check prompt overlap")
    intake_prompts = {normalize(row["prompt"]) for row in rows}
    with suite.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            prompt = json.loads(line)["prompt"]
            if normalize(prompt) in intake_prompts:
                raise ValueError(f"real intake overlaps frozen diagnostic suite at case {line_number}")


def partition(rows: list[dict]) -> dict[str, list[dict]]:
    splits = {"fit": [], "calibration": [], "sealed": []}
    for row in rows:
        bucket = int(row["workflow_id_hash"][:8], 16) % 100
        split = "fit" if bucket < 70 else "calibration" if bucket < 85 else "sealed"
        splits[split].append(row)
    group_sets = {name: {row["workflow_id_hash"] for row in subset}
                  for name, subset in splits.items()}
    if any(not group_sets[name] or {row["label"] for row in subset} != LABELS
           for name, subset in splits.items()):
        raise ValueError("workflow split lacks groups or one binary label; collect more diverse requests")
    if any(group_sets[a] & group_sets[b] for a, b in
           (("fit", "calibration"), ("fit", "sealed"), ("calibration", "sealed"))):
        raise ValueError("workflow leakage across splits")
    return splits


def run(root: Path, input_path: Path, output_path: Path) -> dict:
    source = private_path(root, input_path)
    output = private_path(root, output_path)
    if not source.is_file() or output.exists() or output == source:
        raise ValueError("input missing or output already exists")
    with source.open("rb") as stream:
        raw = stream.read(50_000_001)
    if len(raw) > 50_000_000:
        raise ValueError("real request input exceeds 50 MB")
    rows, counts = parse_rows(raw)
    reject_frozen_suite_overlap(root, rows)
    splits = partition(rows)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": SCHEMA, "status": "REDACTED_LOCAL_INTAKE_ONLY",
                "source_sha256": sha256(raw), "source_bytes": len(raw),
                "counts": counts, "splits": {}, "cross_split_prompt_overlap": 0,
                "cross_split_workflow_overlap": 0, "frozen_suite_prompt_overlap": 0,
                "human_label_quality_proven": False,
                "real_workflow_proven": False, "production_enabled": False,
                "sealed_split_rule": "Do not train, tune, inspect labels, or select candidates using sealed.jsonl"}
    for name, subset in splits.items():
        data = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                       for row in subset).encode("utf-8")
        (output / f"{name}.jsonl").write_bytes(data)
        manifest["splits"][name] = {"rows": len(subset),
                                    "workflow_groups": len({row["workflow_id_hash"] for row in subset}),
                                    "labels": dict(Counter(row["label"] for row in subset)),
                                    "sha256": sha256(data)}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    result = run(repo, args.input, args.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "splits": result["splits"]}, indent=2))
