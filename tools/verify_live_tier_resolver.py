#!/usr/bin/env python3
"""Verify both experimental tier selections against the live catalog and policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import select_experimental_tier


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selections = [select_experimental_tier(preference, args.catalog, args.policy) for preference in ("compact", "larger")]
    receipt = {
        "schema": "wrench.live-tier-resolver-receipt.v1",
        "status": "PASS_LIVE_EXPERIMENTAL_TIER_RESOLUTION",
        "selections": selections,
        "quality_claim": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "tiers": len(selections)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
