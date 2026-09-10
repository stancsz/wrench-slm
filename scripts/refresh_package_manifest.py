"""Recompute a staged package checksum manifest after release-document edits."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--status", choices=["TRAINED CANDIDATE", "WEIGHTS READY FOR RELEASE"], required=True)
    args = parser.parse_args()
    package = Path(args.package).resolve()
    if not package.is_relative_to(ROOT / "artifacts/model-release"):
        parser.error("package must be under artifacts/model-release")
    manifest_path = package / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = args.status
    manifest["sha256"] = {
        str(path.relative_to(package)).replace("\\", "/"): digest(path)
        for path in sorted(package.rglob("*"))
        if path.is_file() and path != manifest_path
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "package": str(package),
        "status": manifest["status"],
        "adapter_sha256": manifest["adapter_sha256"],
        "files": len(manifest["sha256"]),
        "manifest_sha256": digest(manifest_path),
    }, indent=2))


if __name__ == "__main__":
    main()
