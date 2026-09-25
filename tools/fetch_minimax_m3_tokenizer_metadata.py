"""Fetch only the pinned MiniMax M3 tokenizer/template metadata, never weights."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any


REPOSITORY = "MiniMaxAI/MiniMax-M3"
REVISION = "f0e1c1e04d40177e4673a22097036854f536e9c0"
REPOSITORY_FILE_COUNT = 82
REPOSITORY_WEIGHT_SHARD_COUNT = 59
REPOSITORY_TOTAL_BYTES = 854_200_504_173
SELECTED_FILES: dict[str, tuple[int, str]] = {
    "LICENSE": (3339, "f413dfa3bbb4d3713823106599052624b91434d9"),
    "added_tokens.json": (1660, "43c846ca31dbefd9250f2681d0013f3304c20b55"),
    "chat_template.jinja": (11756, "93022eb9ceec98f50e7a510841850f7f2e952d9d"),
    "config.json": (5254, "6ad82bf04f219470b07fafe8715d7b05936540f1"),
    "merges.txt": (2414077, "ff574e20e38bcb4a57a4cbdb6e2df9f533339435"),
    "special_tokens_map.json": (277, "c55c5c84d7e4bbb2f02cc746ae1b3730cb5ae5d2"),
    "tokenizer.json": (9731500, "9065e14e5a73c490eb304429d903d3d08b977ab4"),
    "tokenizer_config.json": (11288, "44840ad83c3832759b922a5695ed968a5e0ee2ec"),
    "vocab.json": (4705413, "379894132c073256d7f45c67672de5c5a0d7e4c2"),
}


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _get(url: str, *, max_bytes: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "wrench-tokenizer-inventory/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"download_http_{response.status}")
        payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise RuntimeError("download_size_limit_exceeded")
    return payload


def fetch(output_root: Path) -> dict[str, Any]:
    expected_root = Path(r"C:\wrench-slm-data\artifacts\wrench-local-acceptability")
    output_root = output_root.resolve()
    if not output_root.is_relative_to(expected_root.resolve()):
        raise ValueError("output_must_be_under_approved_artifact_root")
    if output_root.exists():
        raise FileExistsError("refusing_to_overwrite_existing_tokenizer_snapshot")

    api_url = f"https://huggingface.co/api/models/{REPOSITORY}/revision/{REVISION}?blobs=true"
    model = json.loads(_get(api_url, max_bytes=8 * 1024 * 1024))
    siblings = model.get("siblings")
    if model.get("sha") != REVISION or type(siblings) is not list or len(siblings) != REPOSITORY_FILE_COUNT:
        raise ValueError("pinned_repository_inventory_mismatch")

    rows: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for sibling in siblings:
        name = sibling.get("rfilename")
        if type(name) is not str or name in by_name:
            raise ValueError("repository_file_identity_invalid")
        lfs = sibling.get("lfs") or {}
        size = lfs.get("size", sibling.get("size"))
        if type(size) is not int or size < 0:
            raise ValueError("repository_file_size_invalid")
        item = {
            "path": name,
            "size_bytes": size,
            "git_blob_sha1": sibling.get("blobId"),
            "lfs_sha256": lfs.get("sha256"),
        }
        rows.append(item)
        by_name[name] = item
        total_bytes += size

    shard_names = [name for name in by_name if name.endswith(".safetensors")]
    if len(shard_names) != REPOSITORY_WEIGHT_SHARD_COUNT or total_bytes != REPOSITORY_TOTAL_BYTES:
        raise ValueError("repository_size_inventory_mismatch")
    for name, (size, blob_sha1) in SELECTED_FILES.items():
        item = by_name.get(name)
        if item is None or item["size_bytes"] != size or item["git_blob_sha1"] != blob_sha1 or item["lfs_sha256"] is not None:
            raise ValueError(f"selected_file_identity_mismatch:{name}")

    inventory = {
        "schema": "wrench.pinned-model-source-inventory.v1",
        "repository": REPOSITORY,
        "revision": REVISION,
        "repository_file_count": len(rows),
        "weight_shard_count": len(shard_names),
        "repository_total_bytes": total_bytes,
        "selected_tokenizer_metadata": sorted(SELECTED_FILES),
        "selected_tokenizer_metadata_bytes": sum(value[0] for value in SELECTED_FILES.values()),
        "model_weights_downloaded": False,
        "files": sorted(rows, key=lambda item: item["path"]),
    }
    output_root.mkdir(parents=True)
    (output_root / "source_inventory.json").write_bytes(_canonical(inventory))
    tokenizer_root = output_root / "tokenizer"
    tokenizer_root.mkdir()
    for name, (expected_size, expected_git_sha1) in SELECTED_FILES.items():
        url = f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}?download=true"
        contents = _get(url, max_bytes=expected_size)
        if len(contents) != expected_size:
            raise ValueError(f"selected_file_size_mismatch:{name}")
        git_blob = b"blob " + str(len(contents)).encode("ascii") + b"\0" + contents
        if hashlib.sha1(git_blob).hexdigest() != expected_git_sha1:
            raise ValueError(f"selected_file_hash_mismatch:{name}")
        temporary = tokenizer_root / (name + ".part")
        destination = tokenizer_root / name
        temporary.write_bytes(contents)
        temporary.replace(destination)

    result = {
        "status": "TOKENIZER_METADATA_READY",
        "repository": REPOSITORY,
        "revision": REVISION,
        "repository_file_count": len(rows),
        "weight_shard_count": len(shard_names),
        "repository_total_bytes": total_bytes,
        "selected_file_count": len(SELECTED_FILES),
        "selected_file_bytes": inventory["selected_tokenizer_metadata_bytes"],
        "model_weights_downloaded": False,
        "source_inventory_sha256": hashlib.sha256(_canonical(inventory)).hexdigest(),
    }
    (output_root / "fetch_receipt.json").write_bytes(_canonical(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(fetch(args.output_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
