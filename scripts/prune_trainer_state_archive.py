"""Remove the superseded external optimizer-state archive after a run."""

from __future__ import annotations

import shutil
from pathlib import Path


TARGET = Path(r"D:\wrench-slm-artifacts-archive\2026-09-10\trainer-states")
EXPECTED_PARENT = Path(r"D:\wrench-slm-artifacts-archive\2026-09-10")


def main() -> int:
    target = TARGET.resolve()
    if target.parent != EXPECTED_PARENT.resolve() or target.name != "trainer-states":
        raise SystemExit(f"refusing to remove unexpected path: {target}")
    if not target.exists():
        print("archive_missing=true")
        return 0
    files = sum(1 for item in target.rglob("*") if item.is_file())
    shutil.rmtree(target)
    print(f"removed_files={files}")
    print(f"removed_path={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
