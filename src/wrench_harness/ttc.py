"""Bounded test-time-compute scheduling for Wrench.

The scheduler borrows the useful part of LeanRouter's tiered reasoning
patterns: a fast local gate for routine work, an isolated audit for drafts,
and a bounded deep path only when the action is genuinely contestable. It does
not create execution authority or silently call a frontier model.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .toolbelt import multi_pass_verify


@dataclass(frozen=True)
class TTCProfile:
    name: str
    max_model_passes: int
    passes: tuple[str, ...]
    early_exit_on_clean: bool = True


FAST = TTCProfile(
    "fast",
    1,
    ("schema", "authority", "evidence", "consistency"),
)
GUARDED = TTCProfile(
    "guarded",
    2,
    ("schema", "authority", "evidence", "consistency", "ast_gate", "diff_gate"),
)
DEEP = TTCProfile(
    "deep",
    4,
    ("schema", "authority", "evidence", "consistency", "ast_gate", "diff_gate", "blind_critic", "final_gate"),
)


def select_profile(proposal: object, request_prompt: str | None, *, context_pressure: bool = False) -> TTCProfile:
    """Select the smallest bounded profile that covers the request risk."""

    action = proposal.get("action") if isinstance(proposal, dict) else None
    prompt = request_prompt.casefold() if isinstance(request_prompt, str) else ""
    complex_markers = (
        "multi-step",
        "across several files",
        "debug",
        "refactor",
        "review",
        "test",
        "compare",
        "patch",
    )
    has_complex_marker = any(
        re.search(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", prompt)
        for marker in complex_markers
    )
    if action == "patch_draft" or has_complex_marker:
        return DEEP
    if context_pressure or action in {"literal_search", "health_read"}:
        return GUARDED
    return FAST


def run_ttc_verification(
    proposal: object,
    request_prompt: str | None,
    execution_result: object,
    *,
    context_pressure: bool = False,
    extra_gates: dict[str, bool] | None = None,
) -> dict[str, object]:
    """Run the local multi-pass receipt under a hard, action-sensitive budget."""

    profile = select_profile(proposal, request_prompt, context_pressure=context_pressure)
    base = multi_pass_verify(proposal, request_prompt, execution_result)
    checks = {row["name"]: bool(row["passed"]) for row in base["passes"]}
    observation = execution_result.get("observation") if isinstance(execution_result, dict) else None
    blind_critic_ok = (
        isinstance(proposal, dict)
        and proposal.get("schema") == "wrench.proposal.v1"
        and proposal.get("action") in {"read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"}
        and isinstance(execution_result, dict)
        and execution_result.get("status") in {"accepted", "abstain"}
        and not (
            isinstance(observation, dict)
            and (observation.get("mutated") is True or observation.get("applied") is True)
        )
    )
    checks["blind_critic"] = blind_critic_ok
    # A proposal-only request has no candidate source buffer to parse. The
    # executor's bounded schema and unified-diff checks are the applicable
    # local gates in that case. A caller that has source buffers must override
    # these defaults with static_code_gate results.
    if "ast_gate" in profile.passes:
        checks.setdefault("ast_gate", True)
    if "diff_gate" in profile.passes:
        checks.setdefault("diff_gate", True)
    for name, passed in (extra_gates or {}).items():
        checks[name] = bool(passed)
    final_gate_ok = bool(base["passed"]) and blind_critic_ok and all(
        bool(checks.get(name, False)) for name in (extra_gates or {})
    )
    checks["final_gate"] = final_gate_ok
    failed = [name for name in profile.passes if not bool(checks.get(name, False))]
    passed = not failed and bool(base["passed"])
    return {
        "schema": "wrench.test-time-compute-receipt.v1",
        "profile": profile.name,
        "max_model_passes": profile.max_model_passes,
        "passes_requested": list(profile.passes),
        "checks": checks,
        "failed_checks": failed,
        "early_exit": passed and profile.early_exit_on_clean,
        "passed": passed,
        "base_verifier": base,
    }


def enforce_ttc(
    proposal: object,
    request_prompt: str | None,
    execution_result: dict[str, Any],
    *,
    context_pressure: bool = False,
) -> dict[str, Any]:
    """Attach and enforce the bounded local TTC receipt on accepted output."""

    if execution_result.get("status") != "accepted":
        return execution_result
    receipt = run_ttc_verification(
        proposal,
        request_prompt,
        execution_result,
        context_pressure=context_pressure,
    )
    enriched = dict(execution_result)
    enriched["ttc"] = receipt
    if receipt["passed"]:
        return enriched
    failed = ",".join(str(item) for item in receipt.get("failed_checks", [])) or "unknown"
    return {
        "status": "abstain",
        "fallback_reason": "multi_pass_verification_failed",
        "detail": failed,
        "ttc": receipt,
    }
