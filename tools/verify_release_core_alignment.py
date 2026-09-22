#!/usr/bin/env python3
"""Verify that a materialized package's executable core matches repository HEAD."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


PAIRS = (
    ("src/wrench_harness/server.py", "wrench_runtime/server.py"),
    ("src/wrench_harness/worker.py", "wrench_runtime/worker.py"),
    ("src/wrench_harness/prefill.py", "wrench_runtime/prefill.py"),
    ("src/wrench_harness/mechanical.py", "wrench_runtime/mechanical.py"),
    ("src/wrench_harness/core.py", "wrench_runtime/core.py"),
    ("src/wrench_harness/toolbelt.py", "wrench_runtime/toolbelt.py"),
    ("wrench_server.py", "wrench_server.py"),
    ("wrench_worker.py", "wrench_worker.py"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    data = path.read_bytes()
    # A Windows checkout may materialize tracked Python files with CRLF while
    # the uploaded portable package contains LF.  Line endings are not runtime
    # identity, so normalize only the executable text files being compared.
    if path.suffix.lower() == ".py":
        data = data.replace(b"\r\n", b"\n")
    digest.update(data)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def run(args: argparse.Namespace) -> dict[str, Any]:
    source = args.source_root.resolve()
    package = args.package_dir.resolve()
    rows: list[dict[str, Any]] = []
    for source_rel, package_rel in PAIRS:
        source_path = source / source_rel
        package_path = package / package_rel
        if not source_path.is_file() or not package_path.is_file():
            rows.append({"source": source_rel, "package": package_rel, "match": False, "error": "missing"})
            continue
        source_sha = _sha256(source_path)
        package_sha = _sha256(package_path)
        rows.append({"source": source_rel, "package": package_rel, "match": source_sha == package_sha, "source_sha256": source_sha, "package_sha256": package_sha})
    tracked_core_status = _git(source, "status", "--short", "--", *[pair[0] for pair in PAIRS])
    core_manifest = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt: dict[str, Any] = {
        "schema": "wrench.release-core-alignment.v1",
        "status": "PASS_CORE_RUNTIME_ALIGNED_WITH_HEAD" if all(row.get("match") for row in rows) and not tracked_core_status else "FAIL_CORE_RUNTIME_ALIGNMENT",
        "source_root": str(source),
        "source_head": _git(source, "rev-parse", "HEAD"),
        "package_dir": str(package),
        "pairs": rows,
        "core_manifest_sha256": hashlib.sha256(core_manifest).hexdigest(),
        "hash_normalization": "Python runtime files normalize CRLF to LF before SHA-256 comparison",
        "tracked_core_status": tracked_core_status,
        "publication_policy": "unrelated README and phase dirt remains a clean-snapshot concern; no upload performed",
        "claims_not_authorized": [
            "HF upload",
            "independent RTX 5060 Ti verification",
            "learned MiniMax parity",
            "production readiness",
        ],
    }
    receipt["all_pairs_match"] = all(row.get("match") for row in rows)
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args)
    print(json.dumps({"status": receipt["status"], "all_pairs_match": receipt["all_pairs_match"], "core_manifest_sha256": receipt["core_manifest_sha256"]}))
    return 0 if receipt["all_pairs_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
