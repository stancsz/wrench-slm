#!/usr/bin/env python3
"""Run a real Wrench worker generation after a monster-context first-layer gate.

This is a development probe. It deliberately disables the mechanical shortcut
so the Transformers checkpoint must generate after the package-local reducer
compacts the raw message. It does not use the sealed final split.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from wrench_harness.worker import WrenchWorker  # noqa: E402
from tools.probe_native_handoff_prefill import _build_payload  # noqa: E402


_SYSTEM = (
    "You are Wrench, a narrow developer-tool proposal generator. Output exactly "
    "one valid JSON object and nothing else: no markdown, no code fence, no prose. "
    "Always include schema wrench.proposal.v1 and exactly one allowed action. "
    "Use read_file={schema,action:read_file,path,max_bytes}."
)
_ADMISSION_ESTIMATE_SAFETY_MARGIN = 4_096


def _payload(target_tokens: int) -> str:
    content = _build_payload(target_tokens)
    prefix, _, _ = content.rpartition("CURRENT INTENT:")
    return prefix + (
        "CURRENT INTENT: Prepare a bounded read proposal for "
        "phases/phase-49-release-gate-audit/README.md with a 131072 byte ceiling."
    )


def run(args: argparse.Namespace) -> dict[str, object]:
    payload = _payload(max(1, args.payload_tokens - _ADMISSION_ESTIMATE_SAFETY_MARGIN))
    worker = WrenchWorker.from_pretrained(
        args.model,
        allowed_root=args.allowed_root,
        load_model=True,
    )
    started = time.perf_counter()
    result = worker.propose(
        [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": payload},
        ],
        max_tokens=args.max_new_tokens,
        use_mechanical_route=False,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    prefill = result.get("dynamic_prefill")
    prefill = prefill if isinstance(prefill, dict) else {}
    expected_proposal = {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "phases/phase-49-release-gate-audit/README.md",
        "max_bytes": 131072,
    }
    observed_proposal = None
    raw_model_output = result.get("raw_model_output")
    if isinstance(raw_model_output, str):
        try:
            parsed = json.loads(raw_model_output)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            observed_proposal = parsed
    receipt: dict[str, object] = {
        "schema": "wrench.real-worker-long-context-probe.v1",
        "status": (
            "PASS_REAL_WORKER_LONG_CONTEXT"
            if result.get("status") == "accepted"
            else "REAL_WORKER_GENERATION_GAP"
        ),
        "model": str(args.model.resolve()),
        "payload_target_tokens": args.payload_tokens,
        "admission_estimate_safety_margin_tokens": _ADMISSION_ESTIMATE_SAFETY_MARGIN,
        "max_new_tokens": args.max_new_tokens,
        "mechanical_shortcut": False,
        "status_observed": result.get("status"),
        "exact_target_match": observed_proposal == expected_proposal,
        "backend": result.get("backend"),
        "model_device": result.get("model_device"),
        "model_calls": result.get("model_calls"),
        "fallback_reason": result.get("fallback_reason"),
        "elapsed_ms": elapsed_ms,
        "raw_token_count": prefill.get("raw_token_count"),
        "model_prefill_token_count": prefill.get("model_prefill_token_count"),
        "context_gate_latency_ms": prefill.get("context_gate_latency_ms"),
        "working_context_budget_tokens": prefill.get("working_context_budget_tokens"),
        "model_prefill_budget": prefill.get("model_prefill_budget"),
        "raw_payload_sha256": prefill.get("raw_payload_sha256"),
        "prepared_payload_sha256": prefill.get("prepared_payload_sha256"),
        "exact_expected_proposal": expected_proposal,
        "observed_proposal": observed_proposal,
        "quality_claim": False,
        "notes": [
            "Development-only real model generation after package-local first-layer compaction.",
            "This does not prove dense-native attention, family-disjoint quality, or release readiness.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in (
        "status", "status_observed", "model_device", "model_calls", "elapsed_ms",
        "raw_token_count", "model_prefill_token_count", "context_gate_latency_ms",
    )}, ensure_ascii=False))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, default=Path("."))
    parser.add_argument("--payload-tokens", type=int, default=2_000_000)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.payload_tokens < 1:
        raise ValueError("payload-tokens must be positive")
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
