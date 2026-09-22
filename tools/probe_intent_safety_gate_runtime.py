#!/usr/bin/env python3
"""Run one real Transformers worker request with the optional safety gate."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness.worker import WrenchWorker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ["WRENCH_INTENT_SAFETY_GATE"] = "1"
    os.environ["WRENCH_INTENT_SAFETY_GATE_ARTIFACT"] = str(args.sidecar.resolve())
    worker = WrenchWorker.from_pretrained(
        args.model,
        allowed_root=args.allowed_root,
        load_model=True,
    )
    result = worker.propose(
        [
            {
                "role": "system",
                "content": "Output exactly one valid wrench proposal JSON object and no prose.",
            },
            {
                "role": "user",
                "content": "Read README.md with a 4096 byte ceiling.",
            },
        ],
        max_tokens=128,
        use_mechanical_route=False,
    )
    gate = result.get("intent_safety_gate")
    receipt = {
        "schema": "wrench.intent-safety-gate-runtime-probe.v1",
        "status": "PASS_INTENT_SAFETY_GATE_RUNTIME"
        if isinstance(gate, dict)
        and gate.get("schema") == "wrench.intent-safety-gate.v1"
        and gate.get("authority") == "abstain_only"
        else "FAIL_INTENT_SAFETY_GATE_RUNTIME",
        "model": str(args.model.resolve()),
        "sidecar": str(args.sidecar.resolve()),
        "worker_result": result,
        "production_enabled": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "worker_status": result.get("status"), "gate": gate}))
    return 0 if receipt["status"] == "PASS_INTENT_SAFETY_GATE_RUNTIME" else 1


if __name__ == "__main__":
    raise SystemExit(main())
