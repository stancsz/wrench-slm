#!/usr/bin/env python3
"""Compose a source-pinned receipt for an HF package preflight."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path


def _read_json(path: Path) -> dict:
    """Read JSON receipts emitted by both PowerShell and Python writers."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def compose_receipt(
    *,
    host: str,
    source_root: Path,
    source_commit: str,
    repo_id: str,
    revision: str,
    package_root: Path,
    validation_path: Path,
    smoke_path: Path,
    resource_snapshot_path: Path,
    gpu_identity: str,
    job_id: str | None = None,
    claim_nonce: str | None = None,
    host_name: str | None = None,
) -> dict:
    actual = git_head(source_root)
    if actual != source_commit:
        raise ValueError(f"source commit mismatch: {actual} != {source_commit}")
    validation = _read_json(validation_path)
    if validation.get("status") != "PASS_STRUCTURAL_PACKAGE":
        raise ValueError(f"package validation did not pass: {validation.get('status')!r}")
    smoke = _read_json(smoke_path)
    if smoke.get("status") != "PASS_HF_PACKAGE_MECHANICAL_SMOKE":
        raise ValueError(f"package smoke did not pass: {smoke.get('status')!r}")
    if not gpu_identity.strip():
        raise ValueError("GPU identity is empty")
    if bool(job_id) != bool(claim_nonce):
        raise ValueError("job_id and claim_nonce must be supplied together")
    resource_snapshot = _read_json(resource_snapshot_path)
    if resource_snapshot.get("status") != "PASS_HOST_RESOURCE_RESERVE":
        raise ValueError(f"host resource reserve did not pass: {resource_snapshot.get('status')!r}")
    for sample_name in ("before_download", "after_download"):
        sample = resource_snapshot.get(sample_name)
        if not isinstance(sample, dict) or float(sample.get("ram_free_fraction", 0)) < 0.10:
            raise ValueError(f"RAM reserve below 10 percent: {sample_name}")
        for gpu in sample.get("gpus", []):
            if float(gpu.get("free_fraction", 0)) < 0.10:
                raise ValueError(f"VRAM reserve below 10 percent: {sample_name}")
    shards = sorted(package_root.glob("*.safetensors"))
    if not shards:
        raise ValueError("downloaded package has no Safetensors shards")
    receipt = {
        "schema": "wrench.huggingface-cross-host-receipt.v1",
        "status": "PASS_HF_PACKAGE_PREFLIGHT",
        "host": host,
        "host_name": (host_name or platform.node()).strip(),
        "source_commit": source_commit,
        "huggingface_repo_id": repo_id,
        "huggingface_revision": revision,
        "hub_revision_pinned": True,
        "package_root": str(package_root.resolve()),
        "safetensors_shard_count": len(shards),
        "gpu_identity": gpu_identity.strip(),
        "resource_reserve": resource_snapshot,
        "runtime_identity": smoke.get("runtime_identity", {}),
        "package_validation": {
            "status": validation["status"],
            "config_max_position_embeddings": validation.get("config_max_position_embeddings"),
            "file_hash_count": len(validation.get("file_hashes", {})),
        },
        "mechanical_smoke": {
            "status": smoke["status"],
            "proposal_status": smoke.get("proposal_status"),
        },
        "quality_claim": False,
        "native_attention_claim": False,
    }
    if job_id is not None and claim_nonce is not None:
        receipt["job_id"] = job_id
        receipt["claim_nonce"] = claim_nonce
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--huggingface-repo-id", required=True)
    parser.add_argument("--huggingface-revision", required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--smoke", type=Path, required=True)
    parser.add_argument("--resource-snapshot", type=Path, required=True)
    parser.add_argument("--gpu-identity", required=True)
    parser.add_argument("--job-id")
    parser.add_argument("--claim-nonce")
    parser.add_argument("--host-name")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = compose_receipt(
        host=args.host,
        source_root=args.source_root.resolve(),
        source_commit=args.source_commit,
        repo_id=args.huggingface_repo_id,
        revision=args.huggingface_revision,
        package_root=args.package_root.resolve(),
        validation_path=args.validation.resolve(),
        smoke_path=args.smoke.resolve(),
        resource_snapshot_path=args.resource_snapshot.resolve(),
        gpu_identity=args.gpu_identity,
        job_id=args.job_id,
        claim_nonce=args.claim_nonce,
        host_name=args.host_name,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "host": receipt["host"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
