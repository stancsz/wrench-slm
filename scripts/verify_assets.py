"""Verify immutable release inputs and small evidence files without model downloads."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads((ROOT / "releases/v21/files.json").read_text(encoding="utf-8"))
    failures = []
    for entry in catalog["files"]:
        path = (ROOT / entry["path"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            failures.append(entry["path"] + ": missing or unsafe")
            continue
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != entry["sha256"]:
            failures.append(entry["path"] + ": checksum mismatch")
    if failures:
        raise SystemExit("\n".join(failures))
    print("Verified", len(catalog["files"]), "release files")


if __name__ == "__main__":
    main()
