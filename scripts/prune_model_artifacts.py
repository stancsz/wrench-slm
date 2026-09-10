"""Prune superseded local model artifacts while preserving selected releases."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


WEIGHT_SUFFIXES = {".bin", ".ckpt", ".pt", ".pth", ".safetensors"}


def remove_tree(path: Path, root: Path) -> int:
    if not path.is_relative_to(root):
        raise RuntimeError(f"refusing to remove outside the artifact root: {path}")
    if not path.exists():
        return 0
    count = sum(1 for item in path.rglob("*") if item.is_file()) if path.is_dir() else 1
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-training-run",
        default="pro-training-v13",
        help="Training run directory to preserve, or 'none' to drop all historical run checkpoints.",
    )
    parser.add_argument(
        "--keep-package",
        action="append",
        default=None,
        help="Package directory to preserve. Repeat for multiple package directories; defaults to package-selected-v13.",
    )
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parents[1]
    release_root = (workspace / "artifacts" / "model-release").resolve()
    pilot_root = (workspace / "artifacts" / "usefulness-pilot").resolve()
    if not release_root.is_dir():
        raise SystemExit(f"missing artifact root: {release_root}")

    package_names = args.keep_package if args.keep_package is not None else ["package-selected-v13"]
    keep_roots = {
        (release_root / "base-dependency-v1").resolve(),
        (release_root / "licensing-v1").resolve(),
    }
    keep_roots.update((release_root / name).resolve() for name in package_names)
    if args.keep_training_run != "none":
        keep_roots.add((release_root / args.keep_training_run).resolve())
    removed_files = 0
    removed_trees = []

    for child in release_root.iterdir():
        if child.resolve() in keep_roots:
            continue
        if child.name.startswith("package-"):
            removed_files += remove_tree(child, release_root)
            removed_trees.append(child.name)
            continue
        if child.name.startswith(("pro-training-", "warmstart-diagnostic-")):
            for nested in list(child.iterdir()):
                if nested.is_dir() and (nested.name == "checkpoint" or nested.name.startswith("step-")):
                    removed_files += remove_tree(nested, release_root)

    for path in release_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in WEIGHT_SUFFIXES:
            continue
        if any(path.is_relative_to(keep_root) for keep_root in keep_roots):
            continue
        path.unlink()
        removed_files += 1

    if pilot_root.is_dir():
        for nested in pilot_root.rglob("checkpoint"):
            if nested.is_dir():
                removed_files += remove_tree(nested, pilot_root)

    print(f"removed_files={removed_files}")
    print("removed_package_trees=" + ",".join(sorted(removed_trees)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
