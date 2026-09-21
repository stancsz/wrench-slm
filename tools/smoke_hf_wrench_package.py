#!/usr/bin/env python3
"""Run a bounded no-mutation smoke through a downloaded HF package."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path


def run_smoke(model_dir: Path) -> dict:
    model_dir = model_dir.resolve()
    sys.path.insert(0, str(model_dir))
    from wrench_worker import WrenchWorker

    worker = WrenchWorker.from_pretrained(model_dir, allowed_root=model_dir, load_model=False)
    result = worker.propose(
        [{"role": "user", "content": "Read generation_config.json with a 512 byte limit."}],
        use_mechanical_route=True,
    )
    status = result.get("status") if isinstance(result, dict) else None
    return {
        "schema": "wrench.huggingface-package-mechanical-smoke.v1",
        "model_dir": str(model_dir),
        "proposal_status": status,
        "result": result,
        "runtime_identity": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "status": "PASS_HF_PACKAGE_MECHANICAL_SMOKE"
        if status == "accepted"
        else "FAIL_HF_PACKAGE_MECHANICAL_SMOKE",
        "quality_claim": False,
        "native_attention_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_smoke(args.model_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "proposal_status": receipt["proposal_status"]}))
    return 0 if receipt["status"] == "PASS_HF_PACKAGE_MECHANICAL_SMOKE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
