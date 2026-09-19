"""Validate a host-labeled Wrench cross-host verification receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "wrench.cross-host-receipt.v1"
HOSTS = {"rtx-5070-ti", "rtx-5060-ti"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _error(reason: str) -> dict[str, Any]:
    return {"status": "BLOCKED_CROSS_HOST_RECEIPT", "reasons": [reason]}


def verify_receipt(
    receipt: dict[str, Any],
    *,
    expected_source_commit: str,
    expected_artifact_commit: str,
) -> dict[str, Any]:
    """Return a pass or fail-closed receipt without making quality claims."""

    if receipt.get("schema") != SCHEMA:
        return _error("schema_mismatch")
    if receipt.get("host") not in HOSTS:
        return _error("unsupported_host")
    if not HEX40.fullmatch(expected_source_commit):
        return _error("invalid_expected_source_commit")
    if not HEX40.fullmatch(expected_artifact_commit):
        return _error("invalid_expected_artifact_commit")
    if receipt.get("source_commit") != expected_source_commit:
        return _error("source_commit_mismatch")
    if receipt.get("artifact_commit") != expected_artifact_commit:
        return _error("artifact_commit_mismatch")
    if receipt.get("artifact_hash_verified") is not True:
        return _error("artifact_hash_not_verified")
    if not HEX64.fullmatch(str(receipt.get("artifact_manifest_sha256", ""))):
        return _error("invalid_artifact_manifest_sha256")
    for field in ("runtime_identity", "gpu_identity"):
        value = receipt.get(field)
        if isinstance(value, str):
            valid = bool(value.strip())
        elif isinstance(value, dict):
            valid = bool(value)
        else:
            valid = False
        if not valid:
            return _error(f"missing_{field}")

    metrics = receipt.get("metrics")
    if not isinstance(metrics, dict):
        return _error("missing_metrics")
    for field in ("load_seconds", "peak_memory_bytes"):
        value = metrics.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            return _error(f"invalid_metric:{field}")

    result = {
        "status": "PASS_CROSS_HOST_RECEIPT",
        "schema": SCHEMA,
        "host": receipt["host"],
        "source_commit": receipt["source_commit"],
        "artifact_commit": receipt["artifact_commit"],
        "artifact_manifest_sha256": receipt["artifact_manifest_sha256"],
        "runtime_identity": receipt["runtime_identity"],
        "gpu_identity": receipt["gpu_identity"],
        "metrics": metrics,
        "latency_scope": "host_specific_not_cross_host_comparable",
    }
    return result


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--expected-artifact-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.receipt.read_bytes()
    receipt = json.loads(raw.decode("utf-8"))
    if not isinstance(receipt, dict):
        result = _error("receipt_must_be_object")
    else:
        result = verify_receipt(
            receipt,
            expected_source_commit=args.expected_source_commit,
            expected_artifact_commit=args.expected_artifact_commit,
        )
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "host": result.get("host")}))
    return 0 if result["status"] == "PASS_CROSS_HOST_RECEIPT" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
