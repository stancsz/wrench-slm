#!/usr/bin/env python3
"""Inventory and reserve Wrench artifact storage under a strict 50 GB ceiling."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


LIMIT_BYTES = 50_000_000_000
SCHEMA = "wrench.storage-reservation.v1"
JOB_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


def data_root() -> Path:
    return Path(os.environ.get("WRENCH_DATA_ROOT", r"C:\wrench-slm-data"))


def managed_cache_roots() -> list[Path]:
    candidates = [
        Path.home() / ".cache" / "huggingface",
        Path.home() / ".cache" / "torch",
    ]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.extend((Path(local) / "huggingface", Path(local) / "torch"))
    for name in (
        "HF_HOME",
        "TORCH_HOME",
        "TRANSFORMERS_CACHE",
        "MODELSCOPE_CACHE",
        "OLLAMA_MODELS",
        "TORCH_EXTENSIONS_DIR",
    ):
        value = os.environ.get(name)
        if value:
            candidates.append(Path(value))
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        candidates.extend((Path(xdg_cache) / "huggingface", Path(xdg_cache) / "torch"))
    return candidates


def discover_worktrees(repo: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    return [Path(line[9:]) for line in result.stdout.splitlines() if line.startswith("worktree ")]


def normalized(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def inventory_roots(repo: Path, storage: Path, extras: list[Path]) -> list[Path]:
    candidates = [repo, storage, *discover_worktrees(repo), *managed_cache_roots(), *extras]
    unique: dict[str, Path] = {}
    for candidate in candidates:
        path = normalized(candidate)
        unique.setdefault(os.path.normcase(str(path)), path)

    ordered = sorted(unique.values(), key=lambda item: (len(item.parts), str(item).casefold()))
    roots: list[Path] = []
    for candidate in ordered:
        if any(candidate == root or root in candidate.parents for root in roots):
            continue
        roots.append(candidate)
    return roots


def directory_bytes(root: Path) -> tuple[int, list[str]]:
    if not root.exists():
        return 0, []
    if root.is_file():
        try:
            return root.stat().st_size, []
        except OSError as exc:
            return 0, [f"cannot inspect {root}: {type(exc).__name__}"]

    total = 0
    errors: list[str] = []
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError as exc:
                        errors.append(f"cannot inspect {entry.path}: {type(exc).__name__}")
        except OSError as exc:
            errors.append(f"cannot scan {current}: {type(exc).__name__}")
    return total, errors


def reservation_dir(storage: Path) -> Path:
    return storage / ".budget" / "reservations"


@contextmanager
def registry_lock(storage: Path) -> Iterator[None]:
    lock_path = storage / ".budget" / "reservations.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_reservations(storage: Path) -> tuple[dict[str, dict[str, object]], list[str]]:
    directory = reservation_dir(storage)
    reservations: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    if not directory.exists():
        return reservations, errors
    for path in directory.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if (
                not isinstance(data, dict)
                or data.get("schema") != SCHEMA
                or not isinstance(data.get("job_id"), str)
                or not isinstance(data.get("reserve_bytes"), int)
                or data["reserve_bytes"] < 0
            ):
                raise ValueError("invalid reservation fields")
            reservations[data["job_id"]] = data
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"invalid reservation {path.name}: {type(exc).__name__}")
    return reservations, errors


def current_usage(roots: list[Path]) -> tuple[int, dict[str, int], list[str]]:
    total = 0
    by_root: dict[str, int] = {}
    errors: list[str] = []
    for root in roots:
        size, scan_errors = directory_bytes(root)
        total += size
        by_root[str(root)] = size
        errors.extend(scan_errors)
    return total, by_root, errors


def status(args: argparse.Namespace) -> int:
    try:
        roots = inventory_roots(args.repo_root, args.storage_root, args.include_root)
    except (OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "BLOCKED_SCAN", "error": type(exc).__name__}))
        return 3
    used, by_root, errors = current_usage(roots)
    reservations, reservation_errors = load_reservations(args.storage_root)
    errors.extend(reservation_errors)
    reserved = sum(int(item["reserve_bytes"]) for item in reservations.values())
    projected = used + reserved + args.reserve_bytes
    report = {
        "schema": "wrench.storage-budget-report.v1",
        "status": "BLOCKED_SCAN" if errors else ("BLOCKED_LIMIT" if projected >= LIMIT_BYTES else "WITHIN_LIMIT"),
        "limit_bytes": LIMIT_BYTES,
        "actual_bytes": used,
        "active_reservations_bytes": reserved,
        "requested_reserve_bytes": args.reserve_bytes,
        "projected_bytes": projected,
        "headroom_bytes": max(0, LIMIT_BYTES - 1 - projected),
        "roots": by_root,
        "reservations": sorted(reservations),
        "errors": errors[:100],
        "suppressed_error_count": max(0, len(errors) - 100),
    }
    print(json.dumps(report, indent=2))
    if errors:
        return 3
    return 2 if projected >= LIMIT_BYTES else 0


def reserve(args: argparse.Namespace) -> int:
    if not JOB_ID_RE.fullmatch(args.job_id):
        print("job id must contain only letters, digits, period, underscore, or hyphen", file=sys.stderr)
        return 2
    if args.reserve_bytes <= 0:
        print("reservation must be a positive peak additional byte count", file=sys.stderr)
        return 2
    storage = args.storage_root
    with registry_lock(storage):
        try:
            roots = inventory_roots(args.repo_root, storage, args.include_root)
        except (OSError, subprocess.SubprocessError) as exc:
            print(json.dumps({"status": "BLOCKED_SCAN", "error": type(exc).__name__}))
            return 3
        used, _, errors = current_usage(roots)
        reservations, reservation_errors = load_reservations(storage)
        errors.extend(reservation_errors)
        if errors:
            print(json.dumps({"status": "BLOCKED_SCAN", "errors": errors[:100]}, indent=2))
            return 3
        if args.job_id in reservations:
            print(json.dumps({"status": "BLOCKED_DUPLICATE_JOB_ID", "job_id": args.job_id}))
            return 2
        reserved = sum(int(item["reserve_bytes"]) for item in reservations.values())
        projected = used + reserved + args.reserve_bytes
        if projected >= LIMIT_BYTES:
            print(json.dumps({
                "status": "BLOCKED_LIMIT",
                "limit_bytes": LIMIT_BYTES,
                "actual_bytes": used,
                "active_reservations_bytes": reserved,
                "requested_reserve_bytes": args.reserve_bytes,
                "projected_bytes": projected,
            }, indent=2))
            return 2

        directory = reservation_dir(storage)
        directory.mkdir(parents=True, exist_ok=True)
        reservation = {
            "schema": SCHEMA,
            "job_id": args.job_id,
            "reserve_bytes": args.reserve_bytes,
            "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(args.repo_root),
            "storage_root": str(storage),
            "included_roots": [str(root) for root in roots],
            "limit_bytes": LIMIT_BYTES,
        }
        destination = directory / f"{args.job_id}.json"
        fd, temp_name = tempfile.mkstemp(prefix=f"{args.job_id}.", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(reservation, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, destination)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        print(json.dumps({"status": "RESERVED", **reservation}, indent=2))
    return 0


def release(args: argparse.Namespace) -> int:
    if not JOB_ID_RE.fullmatch(args.job_id):
        print("invalid job id", file=sys.stderr)
        return 2
    with registry_lock(args.storage_root):
        path = reservation_dir(args.storage_root) / f"{args.job_id}.json"
        if not path.is_file():
            print(json.dumps({"status": "NOT_FOUND", "job_id": args.job_id}))
            return 2
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "BLOCKED_INVALID_RESERVATION", "error": type(exc).__name__}))
            return 3
        if not isinstance(data, dict) or data.get("schema") != SCHEMA or data.get("job_id") != args.job_id:
            print(json.dumps({"status": "BLOCKED_INVALID_RESERVATION"}))
            return 3
        path.unlink()
    print(json.dumps({"status": "RELEASED", "job_id": args.job_id}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce the strict Wrench 50 GB artifact budget.")
    parser.add_argument("command", choices=("status", "reserve", "release"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--storage-root", type=Path, default=data_root())
    parser.add_argument("--include-root", type=Path, action="append", default=[])
    parser.add_argument("--job-id")
    parser.add_argument("--reserve-bytes", type=int, default=0)
    args = parser.parse_args()

    args.repo_root = normalized(args.repo_root)
    args.storage_root = normalized(args.storage_root)
    args.include_root = [normalized(path) for path in args.include_root]

    if args.command == "status":
        if args.reserve_bytes < 0:
            parser.error("--reserve-bytes cannot be negative")
        return status(args)
    if not args.job_id:
        parser.error("--job-id is required for reserve and release")
    if args.command == "reserve":
        return reserve(args)
    if args.reserve_bytes:
        parser.error("--reserve-bytes is only valid with reserve or status")
    return release(args)


if __name__ == "__main__":
    raise SystemExit(main())
