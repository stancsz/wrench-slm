"""Restore checksummed release bundles without overwriting local changes."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore(archive, root, prefixes):
    root = Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix="wrench-assets-") as temporary:
        stage = Path(temporary)
        files = []
        seen = set()
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle.getmembers():
                name = PurePosixPath(member.name)
                if (not member.isfile() or name.is_absolute() or ".." in name.parts
                        or "\\" in member.name or ":" in member.name
                        or not any(member.name.startswith(prefix + "/") for prefix in prefixes)
                        or member.name in seen):
                    raise ValueError(f"Unsafe or duplicate archive member: {member.name}")
                seen.add(member.name)
                destination = (root / member.name).resolve()
                if not destination.is_relative_to(root):
                    raise ValueError("Archive destination escapes repository")
                staged = stage / member.name
                staged.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, staged.open("wb") as output:
                    shutil.copyfileobj(source, output)
                files.append((staged, destination))
        # Check every conflict before installing any file.
        for source, destination in files:
            if destination.exists() and (not destination.is_file() or digest(destination) != digest(source)):
                raise FileExistsError(f"Local file differs; refusing to overwrite: {destination}")
        for source, destination in files:
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", help="Bundle name from releases/v21/assets.json")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    catalog = json.loads((ROOT / "releases/v21/assets.json").read_text(encoding="utf-8"))
    if args.list:
        for asset in catalog["bundles"]:
            print(asset["name"], asset["bytes"], asset["purpose"])
        return
    asset = next((entry for entry in catalog["bundles"] if entry["name"] == args.asset), None)
    if asset is None:
        parser.error("Choose an asset shown by --list")
    from huggingface_hub import hf_hub_download
    archive = hf_hub_download(
        repo_id=catalog["repo_id"], repo_type="dataset", revision=catalog["revision"],
        filename=asset["file"], local_dir=ROOT / "artifacts/downloads",
    )
    if digest(archive) != asset["sha256"]:
        raise ValueError("Downloaded asset checksum mismatch")
    print("Verified and restored", restore(archive, ROOT, asset["prefixes"]), "files")


if __name__ == "__main__":
    main()
