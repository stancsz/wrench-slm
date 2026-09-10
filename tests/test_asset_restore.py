import io
from pathlib import Path
import tarfile

import pytest

from scripts.fetch_assets import restore


def archive(tmp_path, members):
    path = tmp_path / "bundle.tar.gz"
    with tarfile.open(path, "w:gz") as bundle:
        for name, content in members:
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            bundle.addfile(entry, io.BytesIO(content))
    return path


def test_restore_preserves_existing_and_is_repeatable(tmp_path):
    bundle = archive(tmp_path, [("artifacts/example/a", b"original")])
    root = tmp_path / "repo"
    assert restore(bundle, root, ["artifacts/example"]) == 1
    assert restore(bundle, root, ["artifacts/example"]) == 1
    assert (root / "artifacts/example/a").read_bytes() == b"original"


def test_conflict_does_not_partially_install(tmp_path):
    root = tmp_path / "repo"
    existing = root / "artifacts/example/b"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"user change")
    bundle = archive(tmp_path, [("artifacts/example/a", b"new"), ("artifacts/example/b", b"old")])
    with pytest.raises(FileExistsError):
        restore(bundle, root, ["artifacts/example"])
    assert not (existing.parent / "a").exists()
    assert existing.read_bytes() == b"user change"


@pytest.mark.parametrize("name", ["../escape", "/absolute", "artifacts/example/../../escape", "other/file", "C:/escape"])
def test_reject_unsafe_paths(tmp_path, name):
    bundle = archive(tmp_path, [(name, b"bad")])
    with pytest.raises(ValueError):
        restore(bundle, tmp_path / "repo", ["artifacts/example"])
