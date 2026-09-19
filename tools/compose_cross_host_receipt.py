#!/usr/bin/env python3
"""Compose a hash-verified host receipt from a completed runtime smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


HOSTS = {"rtx-5070-ti", "rtx-5060-ti"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify_artifact_manifest(root: Path, manifest_path: Path) -> str:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    failures: list[str] = []
    for item in manifest.get("files", []):
        relative = Path(str(item["path"]))
        path = root / relative
        if not path.is_file():
            failures.append(f"missing:{relative}")
            continue
        expected_bytes = int(item["bytes"])
        actual_bytes = path.stat().st_size
        if actual_bytes != expected_bytes:
            failures.append(f"bytes:{relative}:{actual_bytes}!={expected_bytes}")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != item["sha256"]:
            failures.append(f"sha256:{relative}")
    if failures:
        raise ValueError("artifact manifest verification failed: " + ", ".join(failures[:8]))
    return hashlib.sha256(manifest_bytes).hexdigest()


def compose_receipt(
    *,
    host: str,
    source_root: Path,
    artifact_root: Path,
    expected_source_commit: str,
    expected_artifact_commit: str,
    runtime_smoke_path: Path,
) -> dict[str, Any]:
    if host not in HOSTS:
        raise ValueError(f"unsupported host: {host}")
    actual_source_commit = git_head(source_root)
    actual_artifact_commit = git_head(artifact_root)
    if actual_source_commit != expected_source_commit:
        raise ValueError(f"source commit mismatch: {actual_source_commit} != {expected_source_commit}")
    if actual_artifact_commit != expected_artifact_commit:
        raise ValueError(f"artifact commit mismatch: {actual_artifact_commit} != {expected_artifact_commit}")
    smoke = json.loads(runtime_smoke_path.read_text(encoding="utf-8"))
    if smoke.get("status") != "PASS_STRUCTURAL_LOAD_AND_FORWARD":
        raise ValueError(f"runtime smoke did not pass: {smoke.get('status')!r}")
    for field in ("load_seconds", "peak_memory_bytes", "gpu_identity", "runtime_identity"):
        if field not in smoke:
            raise ValueError(f"runtime smoke missing {field}")
    manifest_path = artifact_root / "artifact-manifest.json"
    manifest_hash = verify_artifact_manifest(artifact_root, manifest_path)
    return {
        "schema": "wrench.cross-host-receipt.v1",
        "host": host,
        "source_commit": expected_source_commit,
        "artifact_commit": expected_artifact_commit,
        "artifact_hash_verified": True,
        "artifact_manifest_sha256": manifest_hash,
        "runtime_identity": smoke["runtime_identity"],
        "gpu_identity": smoke["gpu_identity"],
        "metrics": {
            "load_seconds": smoke["load_seconds"],
            "peak_memory_bytes": smoke["peak_memory_bytes"],
            "generation_seconds": smoke.get("generation_seconds"),
        },
        "runtime_smoke_status": smoke["status"],
        "quality_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, choices=sorted(HOSTS))
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--artifact-commit", required=True)
    parser.add_argument("--runtime-smoke", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = compose_receipt(
        host=args.host,
        source_root=args.source_root.resolve(),
        artifact_root=args.artifact_root.resolve(),
        expected_source_commit=args.source_commit,
        expected_artifact_commit=args.artifact_commit,
        runtime_smoke_path=args.runtime_smoke.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_CROSS_HOST_RECEIPT", "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
