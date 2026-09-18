#!/usr/bin/env python3
"""Build a safety-focused calibration set without changing the source splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--boundary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=10)
    args = parser.parse_args()
    base = rows(args.base)
    boundary = [row for row in rows(args.boundary) if row.get("family") == "boundary_abstention"]
    if not base or len(boundary) < 8 or args.repeat < 1:
        raise SystemExit("expected a non-empty base and at least eight boundary rows")
    augmented = base + boundary * args.repeat
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in augmented), encoding="utf-8")
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    print(json.dumps({"base": len(base), "boundary": len(boundary), "repeat": args.repeat, "total": len(augmented), "sha256": digest}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
