"""Fetch and verify the pinned Agent Retrieval Bench V2 releases.

All downloaded benchmark data and extraction receipts stay under this phase's
ignored external data directory. The script does not run model inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import psutil
import zstandard
from huggingface_hub import hf_hub_download


PHASE = Path(__file__).resolve().parent
DATA_ROOT = PHASE / "external" / "agent-retrieval-bench" / "data"
DATASET_REPO = "eyuansu71/agent_retrieval_bench"
DATASET_REVISION = "5901e1ee3aff048290db72edf9c63bc498b79ea3"
SOURCE_REVISION = "07014c986f3deadb1548c62b32c0ffbe6a81465d"
RELEASES = (
    "v2_code2test",
    "v2_comment2context",
    "v2_trace2code",
    "v2_edit2ripple",
    "v2_abstention",
    "v2_selective_retrieval_balanced",
    "v2_selective_retrieval_natural",
)
RESERVE_FRACTION = 0.10


def resource_sample() -> dict[str, int | None]:
    memory = psutil.virtual_memory()
    result: dict[str, int | None] = {
        "ram_free_bytes": int(memory.available),
        "ram_total_bytes": int(memory.total),
        "vram_free_bytes": None,
        "vram_total_bytes": None,
    }
    query = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.free,memory.total",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    free_mib, total_mib = (int(part.strip()) for part in query.stdout.splitlines()[0].split(","))
    result["vram_free_bytes"] = free_mib * 1024 * 1024
    result["vram_total_bytes"] = total_mib * 1024 * 1024
    return result


def require_reserve() -> dict[str, int | None]:
    sample = resource_sample()
    for name in ("ram", "vram"):
        free = sample[f"{name}_free_bytes"]
        total = sample[f"{name}_total_bytes"]
        if free is None or total is None or free < total * RESERVE_FRACTION:
            raise RuntimeError(f"10 percent {name.upper()} reserve would be breached: {sample}")
    return sample


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_checksum(path: Path) -> str:
    match = re.search(r"\b[0-9a-fA-F]{64}\b", path.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"no SHA-256 found in checksum file: {path}")
    return match.group(0).lower()


def safe_member_path(root: Path, name: str) -> Path:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts:
        raise ValueError(f"unsafe archive path: {name}")
    relative = Path(*(part for part in member.parts if part not in ("", ".")))
    target = (root / relative).resolve()
    target.relative_to(root.resolve())
    return target


def extract_archive(archive: Path) -> tuple[int, int]:
    files = 0
    written_bytes = 0
    root = DATA_ROOT.resolve()
    reader = zstandard.ZstdDecompressor().stream_reader(archive.open("rb"))
    with reader, tarfile.open(fileobj=reader, mode="r|") as bundle:
        for member in bundle:
            require_reserve()
            target = safe_member_path(root, member.name)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise ValueError(f"unsupported archive member type: {member.name}")

            source = bundle.extractfile(member)
            if source is None:
                raise ValueError(f"archive member has no data: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            size = 0
            if target.exists():
                with source, target.open("rb") as existing:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(block)
                        size += len(block)
                    existing_hash = hashlib.sha256()
                    for block in iter(lambda: existing.read(4 * 1024 * 1024), b""):
                        existing_hash.update(block)
                if size != member.size or digest.hexdigest() != existing_hash.hexdigest():
                    raise FileExistsError(f"existing extracted file differs: {target}")
                continue

            temporary: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb", prefix=target.name + ".", suffix=".partial",
                    dir=target.parent, delete=False,
                ) as output:
                    temporary = Path(output.name)
                    with source:
                        for block in iter(lambda: source.read(1024 * 1024), b""):
                            output.write(block)
                            digest.update(block)
                            size += len(block)
                            if size % (64 * 1024 * 1024) < len(block):
                                require_reserve()
                if size != member.size:
                    raise ValueError(f"size mismatch for archive member: {member.name}")
                temporary.replace(target)
            except Exception:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
                raise
            files += 1
            written_bytes += size
    return files, written_bytes


def fetch_release(release: str) -> dict[str, Any]:
    require_reserve()
    raw_root = DATA_ROOT / "raw"
    filename = f"releases/{release}/agent_retrieval_bench_{release}.tar.zst"
    archive = Path(
        hf_hub_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            filename=filename,
            revision=DATASET_REVISION,
            local_dir=str(raw_root),
        )
    )
    checksum_path = Path(
        hf_hub_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            filename=filename + ".sha256",
            revision=DATASET_REVISION,
            local_dir=str(raw_root),
        )
    )
    expected = expected_checksum(checksum_path)
    actual = sha256_file(archive)
    if actual != expected:
        raise ValueError(f"archive checksum mismatch for {release}: {actual} != {expected}")
    files, extracted_bytes = extract_archive(archive)
    return {
        "release": release,
        "archive": filename,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": actual,
        "files_written": files,
        "extracted_bytes_written": extracted_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", choices=RELEASES, action="append")
    args = parser.parse_args()
    selected = args.release or list(RELEASES)
    receipt: dict[str, Any] = {
        "schema": "wrench.arb-v2-data-setup.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_repo": DATASET_REPO,
        "dataset_revision": DATASET_REVISION,
        "source_revision": SOURCE_REVISION,
        "reserve_fraction": RESERVE_FRACTION,
        "resources_before": require_reserve(),
        "releases": [],
    }
    for release in selected:
        item = fetch_release(release)
        receipt["releases"].append(item)
        print(json.dumps(item, sort_keys=True), flush=True)
    receipt["resources_after"] = require_reserve()
    output = DATA_ROOT / "arb-v2-data-setup-receipt.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"receipt={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
