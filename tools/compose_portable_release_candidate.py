#!/usr/bin/env python3
"""Compose a hash-bound release-candidate receipt without uploading anything."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def run(args: argparse.Namespace) -> dict[str, Any]:
    package = args.package_dir.resolve()
    package_metadata = _load(package / "wrench-package.json")
    validation = _load(args.validation.resolve())
    client = _load(args.client.resolve())
    ollama = _load(args.ollama.resolve())
    if validation.get("status") != "PASS_STRUCTURAL_PACKAGE":
        raise ValueError("package validation is not passing")
    if client.get("status") != "PASS_LOCAL_PORTABLE_CLIENT_ACCEPTANCE":
        raise ValueError("client acceptance is not passing")
    if ollama.get("status") != "PASS_OLLAMA_SHAPED_MODEL_LOCAL_4M":
        raise ValueError("Ollama-shaped acceptance is not passing")

    files = validation.get("file_hashes")
    if not isinstance(files, dict) or not files:
        raise ValueError("validation has no file hashes")
    manifest_bytes = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    source_root = args.source_root.resolve()
    source_commit = _git(source_root, "rev-parse", "HEAD")
    dirty = bool(_git(source_root, "status", "--porcelain"))
    parameter_count = int(package_metadata.get("verified_total_parameters", 0))
    ceiling = int(package_metadata.get("hard_parameter_ceiling", 0))
    context = package_metadata.get("context")
    runtime = package_metadata.get("runtime")
    publication = package_metadata.get("publication")
    receipt: dict[str, Any] = {
        "schema": "wrench.portable-release-candidate.v1",
        "status": "NEEDS_CLEAN_SOURCE_SNAPSHOT" if dirty else "PASS_RELEASE_CANDIDATE_MANIFEST",
        "publication_performed": False,
        "package_dir": str(package),
        "package_candidate_identity": package_metadata.get("candidate_identity"),
        "package_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "package_file_count": len(files),
        "package_bytes": sum(int(item.get("bytes", 0)) for item in files.values() if isinstance(item, dict)),
        "parameter_count": parameter_count,
        "parameter_ceiling": ceiling,
        "under_parameter_ceiling": 0 < parameter_count < ceiling,
        "context": context,
        "runtime": runtime,
        "publication_target": publication,
        "source": {
            "root": str(source_root),
            "commit": source_commit,
            "dirty": dirty,
            "dirty_policy": "must be clean before publication or independent cross-host promotion",
        },
        "evidence": {
            "package_validation": str(args.validation.resolve()),
            "portable_clients": str(args.client.resolve()),
            "ollama_portable": str(args.ollama.resolve()),
        },
        "claims_not_authorized": [
            "HF upload or publication",
            "independent RTX 5060 Ti current-source verification",
            "learned MiniMax parity",
            "dense-native 4M decoder quality",
            "production readiness",
        ],
    }
    receipt["all_local_checks_pass"] = (
        receipt["under_parameter_ceiling"]
        and not validation.get("errors")
        and client.get("checks", {}).get("all_clients_exited_zero") is True
        and ollama.get("all_checks_pass") is True
    )
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--client", type=Path, required=True)
    parser.add_argument("--ollama", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args)
    print(json.dumps({"status": receipt["status"], "all_local_checks_pass": receipt["all_local_checks_pass"], "package_manifest_sha256": receipt["package_manifest_sha256"]}))
    return 0 if receipt["all_local_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
