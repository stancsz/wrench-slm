"""Retain the best bounded set of native NanoWrench checkpoint snapshots."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


LOSS_RE = re.compile(r"_loss_([0-9]+(?:\.[0-9]+)?)\.pt$")


def checkpoint_loss(path: Path) -> float:
    match = LOSS_RE.search(path.name)
    return float(match.group(1)) if match else float("inf")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="models/checkpoints")
    parser.add_argument("--keep-best", type=int, default=3)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace = Path(__file__).resolve().parents[1]
    if not root.is_relative_to(workspace):
        raise SystemExit(f"refusing to prune outside the workspace: {root}")
    if not root.is_dir():
        raise SystemExit(f"checkpoint directory does not exist: {root}")
    if args.keep_best < 1:
        raise SystemExit("--keep-best must be at least 1")

    files = list(root.glob("*.pt"))
    ranked = sorted(files, key=lambda path: (checkpoint_loss(path), -path.stat().st_mtime))
    keep = ranked[: args.keep_best]
    keep_names = {path.name for path in keep}
    removed = []
    for path in ranked[args.keep_best :]:
        path.unlink()
        removed.append(path.name)

    remaining = list(root.glob("*.pt"))
    total_bytes = sum(path.stat().st_size for path in remaining)
    print(f"removed={len(removed)}")
    print(f"remaining={len(remaining)}")
    print(f"remaining_bytes={total_bytes}")
    print(f"remaining_gib={total_bytes / (1024 ** 3):.3f}")
    print("kept=" + ",".join(sorted(keep_names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
