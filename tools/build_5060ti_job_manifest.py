#!/usr/bin/env python3
"""Build a self-contained, nonce-bound 5060 Ti verification job manifest.

The tool only creates a pending manifest. It does not upload, execute, or
claim a remote job. A worker or queue adapter must validate the manifest and
produce the attested receipt before any hardware claim is allowed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any


QUEUE_CONTRACT = "jobs/pending -> jobs/running -> jobs/completed or jobs/failed"
REMOTE_SOURCE_ROOT = r"C:\Users\stanc\github\wrench-slm"
REMOTE_MODEL_ROOT = r"D:\models\wrench-5060ti-cache"
REMOTE_RECEIPT_ROOT = r"D:\models\wrench-5060ti-receipts"
HF_REPO_ID = "stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview"


def canonical_sha256(path: Path) -> str:
    """Hash JSONL content with CRLF normalized to LF for cross-host parity."""

    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def build_manifest(
    *,
    source_commit: str,
    hf_revision: str,
    job_id: str | None = None,
    target_host: str = "DESKTOP-KET1SKP",
    cases_path: Path | None = None,
    workload: str = "wrench_hf_package_preflight",
) -> dict[str, Any]:
    if len(source_commit) != 40 or any(char not in "0123456789abcdef" for char in source_commit.lower()):
        raise ValueError("source_commit must be a 40-character hexadecimal commit")
    if len(hf_revision) != 40 or any(char not in "0123456789abcdef" for char in hf_revision.lower()):
        raise ValueError("hf_revision must be a 40-character hexadecimal revision")
    if not target_host:
        raise ValueError("target_host is required")
    resolved_job_id = job_id or f"wrench-5060ti-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:10]}"
    if any(char in resolved_job_id for char in "\\/:"):
        raise ValueError("job_id must be a safe path component")
    nonce = uuid.uuid4().hex
    cases = None
    if cases_path is not None:
        cases = {
            "path": str(cases_path),
            "canonical_sha256": canonical_sha256(cases_path),
        }
    workload_scripts = {
        "wrench_hf_package_preflight": "run_5060ti_hf_preflight.ps1",
        "wrench_current_package_verification": "run_5060ti_current_package_verification.ps1",
    }
    if workload not in workload_scripts:
        raise ValueError(f"unsupported workload: {workload}")
    command = (
        "powershell -NoProfile -ExecutionPolicy Bypass -File "
        f"{REMOTE_SOURCE_ROOT}\\tools\\{workload_scripts[workload]} "
        f"-SourceRoot {REMOTE_SOURCE_ROOT} "
        f"-ExpectedSourceCommit {source_commit} "
        f"-HuggingFaceRepoId {HF_REPO_ID} "
        f"-HuggingFaceRevision {hf_revision} "
        f"-ModelRoot {REMOTE_MODEL_ROOT} "
        f"-ReceiptRoot {REMOTE_RECEIPT_ROOT}\\{resolved_job_id} "
        f"-JobId {resolved_job_id} -ClaimNonce {nonce}"
    )
    return {
        "schema": "wrench.worker-job.v1",
        "job_id": resolved_job_id,
        "claim_nonce": nonce,
        "state": "pending",
        "queue_contract": QUEUE_CONTRACT,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target": {
            "host_name": target_host,
            "required_gpu_identity": "NVIDIA GeForce RTX 5060 Ti",
            "source_root": REMOTE_SOURCE_ROOT,
            "source_commit": source_commit,
            "huggingface_repo_id": HF_REPO_ID,
            "huggingface_revision": hf_revision,
        },
        "inputs": {
            "cases": cases,
            "artifact_is_pinned": True,
            "raw_teacher_trace_upload": False,
        },
        "execution": {
            "workload": workload,
            "script": f"tools/{workload_scripts[workload]}",
            "command": command,
            "timeout_seconds": 1800,
            "retry_limit": 1,
            "allowed_mutation": "none",
        },
        "resource_requirements": {
            "minimum_host_ram_free_fraction": 0.1,
            "minimum_host_vram_free_fraction": 0.1,
            "sample_before_and_after": True,
            "abort_if_reserve_breached": True,
        },
        "boundaries": {
            "provider_spending": False,
            "credential_access": False,
            "arbitrary_shell": False,
            "production_routing": False,
            "mutation_authority": False,
            "parity_claim_without_attestation": False,
        },
        "required_receipt": {
            "schema": "wrench.hf-cross-host-receipt.v1",
            "must_echo": ["job_id", "claim_nonce"],
            "must_report": [
                "worker_identity",
                "host_name",
                "gpu_identity",
                "source_commit",
                "huggingface_repo_id",
                "huggingface_revision",
                "package_hashes",
                "resource_snapshot_before",
                "resource_snapshot_after",
                "command",
                "exit_code",
                "validation_receipt_path",
                "smoke_receipt_path",
                "failure_details",
            ],
            "independent_5060_claim_requires": [
                "host_name == DESKTOP-KET1SKP",
                "gpu_identity contains RTX 5060 Ti",
                "claim_nonce echo",
                "source_commit exact match",
                "huggingface_revision exact match",
                "both resource reserves >= 0.10",
                "exit_code == 0",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--huggingface-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--job-id")
    parser.add_argument("--target-host", default="DESKTOP-KET1SKP")
    parser.add_argument("--cases", type=Path)
    parser.add_argument(
        "--workload",
        choices=("wrench_hf_package_preflight", "wrench_current_package_verification"),
        default="wrench_hf_package_preflight",
    )
    args = parser.parse_args()
    if args.cases is not None and not args.cases.is_file():
        raise SystemExit(f"cases file does not exist: {args.cases}")
    manifest = build_manifest(
        source_commit=args.source_commit,
        hf_revision=args.huggingface_revision,
        job_id=args.job_id,
        target_host=args.target_host,
        cases_path=args.cases,
        workload=args.workload,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_MANIFEST_BUILT", "job_id": manifest["job_id"], "claim_nonce": manifest["claim_nonce"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
