"""Verify a local Wrench gateway checkpoint against its pinned file manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


BLOCK_BYTES = 8 * 1024 * 1024
EXPECTED_MODEL_DIR = Path(r"C:\wrench-slm-data\weights\Qwen3.5-0.8B")
APPROVED_WEIGHTS_ROOT = Path(r"C:\wrench-slm-data\weights")
APPROVED_INVENTORY_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-model-research")
DEFAULT_CANDIDATE = Path("docs/northstar/model-candidate.json")


def _hashes(path: Path, size: int) -> tuple[str, str]:
    sha256 = hashlib.sha256()
    git_blob = hashlib.sha1()
    git_blob.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK_BYTES), b""):
            sha256.update(block)
            git_blob.update(block)
    return sha256.hexdigest(), git_blob.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=EXPECTED_MODEL_DIR)
    parser.add_argument("--candidate-manifest", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    model_dir = args.model_dir.resolve(strict=True)
    if not model_dir.is_relative_to(APPROVED_WEIGHTS_ROOT.resolve()):
        raise SystemExit(f"model directory outside approved weights root: {model_dir}")
    candidate = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    model_id = candidate.get("model_id")
    revision = candidate.get("revision")
    if not isinstance(model_id, str) or not model_id.startswith("Qwen/"):
        raise SystemExit("candidate manifest model ID must be a pinned Qwen repository")
    if not isinstance(revision, str) or len(revision) != 40 or any(ch not in "0123456789abcdef" for ch in revision):
        raise SystemExit("candidate manifest revision must be a full lowercase commit SHA")
    if model_dir.name != model_id.rsplit("/", 1)[-1]:
        raise SystemExit("model directory name does not match pinned model ID")

    expected = {item["path"]: item for item in candidate["files"]}
    # Hugging Face's local-dir downloader keeps its own small, revision-bound
    # metadata under .cache/huggingface. It is not a model input file and is
    # deliberately excluded from the upstream snapshot file-set comparison.
    actual_paths = [
        path for path in model_dir.rglob("*")
        if path.is_file()
        and path.relative_to(model_dir).parts[:2] != (".cache", "huggingface")
    ]
    actual_rel = {path.relative_to(model_dir).as_posix(): path for path in actual_paths}
    if set(actual_rel) != set(expected):
        missing = sorted(set(expected) - set(actual_rel))
        extra = sorted(set(actual_rel) - set(expected))
        raise SystemExit(f"snapshot file set mismatch; missing={missing}; extra={extra}")

    files: list[dict[str, Any]] = []
    for relative_path in sorted(expected):
        path = actual_rel[relative_path]
        spec = expected[relative_path]
        size = path.stat().st_size
        if size != spec["size_bytes"]:
            raise SystemExit(f"size mismatch: {relative_path}")
        sha256, git_blob = _hashes(path, size)
        upstream_sha256 = spec.get("upstream_sha256")
        if upstream_sha256:
            if sha256 != upstream_sha256:
                raise SystemExit(f"upstream content SHA-256 mismatch: {relative_path}")
            # Hub Git blob IDs for large LFS objects identify the pointer blob,
            # not the raw weight bytes. Verify LFS contents with upstream SHA-256.
            git_blob_check = "lfs_pointer_id_not_recomputed"
        else:
            if git_blob != spec["git_blob_id"]:
                raise SystemExit(f"pinned Git blob mismatch: {relative_path}")
            git_blob_check = "verified"
        files.append({
            "path": relative_path,
            "size_bytes": size,
            "sha256": sha256,
            "git_blob_id": spec["git_blob_id"],
            "content_identity_check": git_blob_check,
        })

    total_bytes = sum(item["size_bytes"] for item in files)
    if total_bytes != candidate["repository_bytes"]:
        raise SystemExit("total snapshot byte count mismatch")

    manifest = {
        "schema": "wrench.gateway.model-inventory.v1",
        "status": "VERIFIED_LOCAL_SNAPSHOT",
        "model_id": model_id,
        "revision": revision,
        "model_dir": str(model_dir),
        "inventory_source": str(args.candidate_manifest.resolve()),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "files": files,
    }
    output = args.output.resolve()
    if not output.is_relative_to(APPROVED_INVENTORY_ROOT.resolve()):
        raise SystemExit(f"inventory output outside approved artifact root: {output}")
    if output.exists():
        raise SystemExit(f"refusing to overwrite inventory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_bytes(manifest)
    with output.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({
        "status": manifest["status"],
        "model_id": model_id,
        "revision": revision,
        "file_count": manifest["file_count"],
        "total_bytes": total_bytes,
        "inventory_path": str(output),
        "inventory_sha256": hashlib.sha256(payload).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
