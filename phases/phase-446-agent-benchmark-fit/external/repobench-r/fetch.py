from __future__ import annotations

import hashlib
import json
from pathlib import Path

from huggingface_hub import hf_hub_download


REVISION = "b631bd4ce1215cd604c78eb095babebcba6e22de"
FILES = {
    "java_cff/test_easy/0000.parquet": "52ccb4ecc489bc65dfd46ec3614ec765edc37c714562799628634d43be937ee6",
    "java_cff/test_hard/0000.parquet": "2876fe5274940fac36f83eb7bdff9f7d31dffb954ea01ca2b14d4ca4e42738b9",
    "java_cff/test_hard/0001.parquet": "34d96c4d5f0ea637e3d84309e20f2f00954a23c64724ac740a1f77def32137d8",
    "java_cfr/test_easy/0000.parquet": "0591901f01aff6c94666248560de9d56144e5602f276ba76b3da384648197473",
    "java_cfr/test_hard/0000.parquet": "b8c197e5445750753fc8b36f632c1858842d9722b31a81cde31b23ee63fcf51d",
    "python_cff/test_easy/0000.parquet": "3d4355754a5e7e623f02250e7b36a58a4c1c8588c0cafc111328ee0d474597db",
    "python_cff/test_hard/0000.parquet": "2ff17e8143927e939c042c78a3dc5bcea516d697218490ae0626986474027fd9",
    "python_cfr/test_easy/0000.parquet": "2806c025fd1a778b033d36183f059b2426bdc2f0b89504fb16a6b2ff2067ecde",
    "python_cfr/test_hard/0000.parquet": "294922b28435e1d01fbc4e08aa3063174e4d2e581336c699d31a6342916fc3a1",
}


def main() -> None:
    data_root = Path(__file__).resolve().parent / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    receipts = []
    for filename, expected_hash in FILES.items():
        path = Path(
            hf_hub_download(
                repo_id="tianyang/repobench-r",
                repo_type="dataset",
                filename=filename,
                revision=REVISION,
                local_dir=data_root,
            )
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_hash:
            raise SystemExit(f"SHA-256 mismatch for {filename}: {digest}")
        receipts.append({"path": filename, "sha256": digest, "bytes": path.stat().st_size})
    print(
        json.dumps(
            {
                "dataset": "tianyang/repobench-r",
                "revision": REVISION,
                "scope": "test_only",
                "files": receipts,
                "total_bytes": sum(item["bytes"] for item in receipts),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
