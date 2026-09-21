#!/usr/bin/env python3
"""Fail-closed verifier for a Hugging Face package preflight receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "wrench.huggingface-cross-host-receipt.v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _error(reason: str) -> dict[str, Any]:
    return {"status": "BLOCKED_HF_PACKAGE_RECEIPT", "reasons": [reason]}


def verify_receipt(
    receipt: dict[str, Any],
    *,
    expected_source_commit: str,
    expected_repo_id: str,
    expected_revision: str,
) -> dict[str, Any]:
    if receipt.get("schema") != SCHEMA:
        return _error("schema_mismatch")
    if receipt.get("status") != "PASS_HF_PACKAGE_PREFLIGHT":
        return _error("preflight_not_passed")
    if not HEX40.fullmatch(expected_source_commit):
        return _error("invalid_expected_source_commit")
    if receipt.get("source_commit") != expected_source_commit:
        return _error("source_commit_mismatch")
    if receipt.get("huggingface_repo_id") != expected_repo_id:
        return _error("huggingface_repo_id_mismatch")
    if receipt.get("huggingface_revision") != expected_revision:
        return _error("huggingface_revision_mismatch")
    if receipt.get("hub_revision_pinned") is not True:
        return _error("hub_revision_not_pinned")
    if not str(receipt.get("host", "")).strip():
        return _error("missing_host")
    if not str(receipt.get("gpu_identity", "")).strip():
        return _error("missing_gpu_identity")

    validation = receipt.get("package_validation")
    if not isinstance(validation, dict) or validation.get("status") != "PASS_STRUCTURAL_PACKAGE":
        return _error("package_validation_not_passed")
    if int(validation.get("file_hash_count", 0) or 0) <= 0:
        return _error("package_hashes_missing")

    smoke = receipt.get("mechanical_smoke")
    if not isinstance(smoke, dict) or smoke.get("status") != "PASS_HF_PACKAGE_MECHANICAL_SMOKE":
        return _error("mechanical_smoke_not_passed")
    if smoke.get("proposal_status") != "accepted":
        return _error("mechanical_smoke_not_accepted")

    return {
        "status": "PASS_HF_PACKAGE_RECEIPT",
        "schema": SCHEMA,
        "host": receipt["host"],
        "source_commit": receipt["source_commit"],
        "huggingface_repo_id": receipt["huggingface_repo_id"],
        "huggingface_revision": receipt["huggingface_revision"],
        "safetensors_shard_count": receipt.get("safetensors_shard_count"),
        "resource_reserve_policy": "host RAM and VRAM each retain at least 10 percent",
        "quality_claim": False,
        "native_attention_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--expected-repo-id", required=True)
    parser.add_argument("--expected-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.receipt.read_bytes()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = None
    if not isinstance(parsed, dict):
        result = _error("receipt_must_be_object")
    else:
        result = verify_receipt(
            parsed,
            expected_source_commit=args.expected_source_commit,
            expected_repo_id=args.expected_repo_id,
            expected_revision=args.expected_revision,
        )
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "host": result.get("host")}))
    return 0 if result["status"] == "PASS_HF_PACKAGE_RECEIPT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
