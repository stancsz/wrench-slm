#!/usr/bin/env python3
"""Assemble and score historical matched three-arm workflow replay receipts.

This tool consumes already captured arm result JSONL files. It does not call
providers, execute tools, or mutate a repository. Authorization remains
pending unless the caller explicitly supplies the approved value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from .evaluate_workflow_arms import ARMS, evaluate_manifest
except ImportError:
    from evaluate_workflow_arms import ARMS, evaluate_manifest


REQUIRED_FIELDS = (
    "final_success",
    "prohibited_accept",
    "unexpected_mutation",
    "stronger_model_tokens",
    "total_tokens",
    "cost_usd",
    "latency_ms",
    "retry_count",
    "provider_requests",
)


def _load_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{path}:{line_number}: result needs a non-empty id")
        if identifier in rows:
            raise ValueError(f"{path}:{line_number}: duplicate id {identifier}")
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            raise ValueError(f"{path}:{line_number}: missing fields {', '.join(missing)}")
        if not isinstance(row.get("family"), str) or not row["family"]:
            raise ValueError(f"{path}:{line_number}: family is required")
        rows[identifier] = row
    if not rows:
        raise ValueError(f"{path}: no replay results")
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _trace_hash(traces: list[dict[str, Any]]) -> str:
    encoded = json.dumps(traces, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def assemble(
    cloud_path: Path,
    rules_path: Path,
    learned_path: Path,
    *,
    authorization: str = "pending_human_approval",
    capture_id: str = "",
    captured_at: str = "",
    reviewer: str = "",
    source_scope: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = {"cloud_only": cloud_path, "rules_plus_identical_fallback": rules_path, "learned_plus_identical_fallback": learned_path}
    loaded = {arm: _load_jsonl(path) for arm, path in paths.items()}
    identifiers = set(loaded["cloud_only"])
    for arm in ARMS[1:]:
        if set(loaded[arm]) != identifiers:
            missing = sorted(identifiers - set(loaded[arm]))
            extra = sorted(set(loaded[arm]) - identifiers)
            raise ValueError(f"matched trace IDs differ for {arm}: missing={missing}, extra={extra}")

    traces = []
    for identifier in sorted(identifiers):
        family = loaded["cloud_only"][identifier]["family"]
        if any(loaded[arm][identifier]["family"] != family for arm in ARMS):
            raise ValueError(f"family differs across arms for {identifier}")
        traces.append(
            {
                "id": identifier,
                "family": family,
                "arms": {
                    arm: {field: loaded[arm][identifier][field] for field in REQUIRED_FIELDS}
                    for arm in ARMS
                },
            }
        )

    provenance = {
        "capture_id": capture_id,
        "captured_at": captured_at,
        "reviewer": reviewer,
        "source_scope": source_scope,
    }
    manifest = {
        "schema": "wrench.workflow-arm-traces.v1",
        "authorization": authorization,
        "provenance": provenance,
        "trace_set_sha256": _trace_hash(traces),
        "input_receipts": {arm: {"path": str(paths[arm].resolve()), "sha256": _sha256(paths[arm])} for arm in ARMS},
        "traces": traces,
    }
    evaluation = evaluate_manifest(manifest)
    evaluation["input_receipts"] = manifest["input_receipts"]
    return manifest, evaluation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cloud", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--learned", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--authorization", default="pending_human_approval")
    parser.add_argument("--capture-id", default="")
    parser.add_argument("--captured-at", default="")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--source-scope", default="")
    args = parser.parse_args()
    manifest, evaluation = assemble(
        args.cloud.resolve(),
        args.rules.resolve(),
        args.learned.resolve(),
        authorization=args.authorization,
        capture_id=args.capture_id,
        captured_at=args.captured_at,
        reviewer=args.reviewer,
        source_scope=args.source_scope,
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "trace-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output_dir / "evaluation.json").write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
    run_manifest = {
        "schema": "wrench.workflow-arm-replay-run.v1",
        "status": evaluation["status"],
        "trace_count": evaluation["trace_count"],
        "authorization": args.authorization,
        "outputs": ["trace-manifest.json", "evaluation.json"],
        "provider_calls_made": False,
        "repository_mutations": False,
    }
    (output_dir / "run-manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": evaluation["status"], "trace_count": evaluation["trace_count"], "output_dir": str(output_dir)}))
    return 0 if evaluation["status"] in {"BLOCKED_TRACE_AUTHORIZATION", "BLOCKED_TRACE_PROVENANCE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
