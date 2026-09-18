#!/usr/bin/env python3
"""Exercise Wrench routing controls across a persisted state boundary."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import CancellationToken, ProposalRouter, RouterConfig, load_router_state, save_router_state


def run(output: Path) -> dict[str, object]:
    events: list[dict[str, object]] = []
    config = RouterConfig(max_attempts=3, failure_threshold=1)
    router = ProposalRouter(config, event_sink=events.append)
    failed = router.run(lambda: {"status": "abstain", "fallback_reason": "synthetic_failure"})

    with tempfile.TemporaryDirectory(prefix="wrench-router-recovery-") as temporary:
        state_path = Path(temporary) / "router-state.json"
        saved = save_router_state(router, state_path)
        restored = load_router_state(config, state_path)
        blocked_after_restore = restored.run(lambda: {"status": "accepted"})
        reset_ok = restored.reset(config.config_hash)
        accepted_after_reset = restored.run(lambda: {"status": "accepted"})
        wrong_hash_rejected = False
        try:
            load_router_state(RouterConfig(max_attempts=3, failure_threshold=2), state_path)
        except ValueError:
            wrong_hash_rejected = True

    cancellation_events: list[dict[str, object]] = []
    cancellation_router = ProposalRouter(RouterConfig(max_attempts=1), event_sink=cancellation_events.append)
    token = CancellationToken()

    def cancel_during_attempt() -> dict[str, str]:
        token.cancel()
        return {"status": "accepted"}

    cancelled = cancellation_router.run(cancel_during_attempt, token)
    receipt: dict[str, object] = {
        "schema": "wrench.router-control-receipt.v1",
        "status": "PASS_BOUNDED_LOCAL_CONTROL_RECEIPT",
        "checks": {
            "circuit_opened": failed.get("circuit_opened") is True,
            "state_saved": saved.get("schema") == "wrench.router-state.v1",
            "restart_restored_disabled_state": blocked_after_restore.get("fallback_reason") == "router_disabled",
            "hash_mismatch_rejected": wrong_hash_rejected,
            "hash_bound_reset": reset_ok and accepted_after_reset.get("status") == "accepted",
            "cooperative_cancellation": cancelled.get("fallback_reason") == "cancelled",
        },
        "events": [event.get("event") for event in events],
        "cancellation_events": [event.get("event") for event in cancellation_events],
        "scope": "local no-mutation control evidence; external alert delivery not exercised",
        "quality_claim": False,
    }
    receipt["all_checks_pass"] = all(receipt["checks"].values())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.output)
    print(json.dumps({"all_checks_pass": receipt["all_checks_pass"], "output": str(args.output)}))
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
