"""Fail-closed offline admission checks for bounded OpenRouter data capture."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

APPROVAL_SCHEMA = "wrench.minimax-data-job-approval.v1"
CHILD_SCHEMA = "wrench.provider-budget-child-receipt.v1"
APPROVED_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
APPROVED_MODEL = "minimax/minimax-m3"
APPROVED_PROVIDER = "minimax"
DATA_ROOT = Path(r"C:\wrench-slm-data").resolve()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_jsonl_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))


def _money(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"{name} must be a finite nonnegative decimal")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a finite nonnegative decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{name} must be a finite nonnegative decimal")
    return result


def _approval(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        approval = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("human approval is not valid JSON") from exc
    if not isinstance(approval, dict) or approval.get("schema") != APPROVAL_SCHEMA:
        raise ValueError("unexpected human approval schema")
    pilot = approval.get("pilot")
    if (
        approval.get("status") != "APPROVED_BOUNDED_CORPUS_INFERENCE_BLOCKED_ON_AUTHENTICATION"
        or approval.get("approved_by") != "human"
        or _money(approval.get("maximum_total_cost_usd"), "approval cap") != Decimal("100.0")
        or approval.get("provider") != "minimax via OpenRouter"
        or approval.get("model") != APPROVED_MODEL
        or approval.get("requested_upstream_provider") != APPROVED_PROVIDER
        or approval.get("fallbacks") is not False
        or not isinstance(pilot, dict)
        or pilot.get("maximum_requests") != 1
        or pilot.get("maximum_output_tokens") != 128
        or pilot.get("automatic_retries") != 0
        or pilot.get("retain_hidden_reasoning") is not False
    ):
        raise ValueError("human approval does not authorize this bounded pilot configuration")
    if set(pilot.get("retain_only", [])) != {
        "normalized structured proposal", "response model identifier",
        "provider usage and cost", "response content hash",
    }:
        raise ValueError("approval retention list is not the exact approved normalized-only set")
    return approval, sha256(raw)


def _receipt_task_hash(receipt: dict[str, Any]) -> str:
    values = {key: value for key, value in receipt.items() if key != "task_hash"}
    return sha256(_canonical_json(values))


def admit(
    approval_path: Path,
    child_receipt_path: Path,
    cases_path: Path,
    *,
    endpoint: str,
    model: str,
    max_tokens: int,
    workers: int,
    prior_spend_usd: str,
    prior_charge_status: str,
    reconciliation_reference: str,
    remaining_cap_usd: str,
    output_path: Path,
) -> dict[str, Any]:
    """Validate all spend, task binding, route, and token bounds before dispatch."""
    approval, approval_hash = _approval(approval_path)
    try:
        receipt = json.loads(child_receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("child admission receipt is missing or invalid JSON") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != CHILD_SCHEMA:
        raise ValueError("unexpected child admission receipt schema")
    cases_hash = canonical_jsonl_sha256(cases_path)
    expected = {
        "approval_sha256": approval_hash,
        "cases_canonical_sha256": cases_hash,
        "endpoint": APPROVED_ENDPOINT,
        "model": APPROVED_MODEL,
        "provider": APPROVED_PROVIDER,
        "allow_fallbacks": False,
        "workers": 1,
        "maximum_requests": 1,
        "maximum_output_tokens": 128,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"child receipt {key} does not match the approved task")
    if endpoint != APPROVED_ENDPOINT or model != APPROVED_MODEL:
        raise ValueError("endpoint and model must exactly match the approved route")
    if workers != 1 or max_tokens != 128:
        raise ValueError("pilot request count, workers, and output ceiling are fixed at 1 / 1 / 128")
    if receipt.get("task_hash") != _receipt_task_hash(receipt):
        raise ValueError("child receipt task hash is invalid")
    input_tokens = receipt.get("maximum_input_tokens")
    output_tokens = receipt.get("maximum_output_tokens")
    request_count = receipt.get("maximum_requests")
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (input_tokens, output_tokens, request_count)):
        raise ValueError("child receipt token and request ceilings must be positive integers")
    if output_tokens > 128 or request_count != 1:
        raise ValueError("child receipt exceeds the approved output or request ceiling")
    pricing = receipt.get("immutable_maximum_rates_usd_per_million_tokens")
    if not isinstance(pricing, dict) or pricing.get("model") != APPROVED_MODEL:
        raise ValueError("child receipt must include immutable model-specific maximum rates")
    if not isinstance(pricing.get("source_reference"), str) or not pricing["source_reference"].strip():
        raise ValueError("child receipt maximum rates require an immutable source reference")
    if not isinstance(pricing.get("source_sha256"), str) or len(pricing["source_sha256"]) != 64:
        raise ValueError("child receipt maximum rates require a source SHA-256")
    source_path_value = pricing.get("source_path")
    if not isinstance(source_path_value, str) or not source_path_value.strip():
        raise ValueError("child receipt maximum rates require a local source_path")
    source_path = Path(source_path_value).resolve()
    if DATA_ROOT != source_path and DATA_ROOT not in source_path.parents:
        raise ValueError("pricing source_path must be under C:\\wrench-slm-data")
    try:
        source_raw = source_path.read_bytes()
        source_data = json.loads(source_raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("local immutable pricing source is missing or invalid JSON") from exc
    if sha256(source_raw) != pricing["source_sha256"]:
        raise ValueError("local pricing source SHA-256 does not match the child receipt")
    if not isinstance(source_data, dict) or source_data.get("model") != APPROVED_MODEL:
        raise ValueError("local pricing source model does not match the approved model")
    input_rate = _money(pricing.get("input"), "maximum input rate")
    output_rate = _money(pricing.get("output"), "maximum output rate")
    if _money(source_data.get("input"), "source input rate") != input_rate or _money(source_data.get("output"), "source output rate") != output_rate:
        raise ValueError("local pricing source rates do not match the child receipt")
    if input_rate <= 0 or output_rate <= 0:
        raise ValueError("both immutable maximum rates must be positive")
    reserve_per_request = _money(receipt.get("maximum_request_reserve_usd"), "request reserve")
    cumulative_reserve = _money(receipt.get("cumulative_reserve_usd"), "cumulative reserve")
    computed_request = (Decimal(input_tokens) * input_rate + Decimal(output_tokens) * output_rate) / Decimal(1_000_000)
    computed_total = computed_request * request_count
    if reserve_per_request < computed_request or cumulative_reserve < computed_total:
        raise ValueError("receipt reserve is below the maximum implied by its token ceilings and rates")
    if cumulative_reserve < reserve_per_request * request_count:
        raise ValueError("cumulative reserve does not cover all request reserves")

    if prior_charge_status not in {"RECONCILED_CHARGED", "RECONCILED_NOT_CHARGED"}:
        raise ValueError("prior charge status must be reconciled; UNKNOWN is never treated as zero")
    if not reconciliation_reference.strip():
        raise ValueError("a prior-charge reconciliation reference is required")
    prior = _money(prior_spend_usd, "prior spend")
    remaining = _money(remaining_cap_usd, "remaining cap")
    cap = _money(approval["maximum_total_cost_usd"], "approval cap")
    if prior + remaining != cap:
        raise ValueError("caller-supplied prior spend and remaining cap must exactly reconcile to the human cap")
    if cumulative_reserve > remaining:
        raise ValueError("request reserve exceeds the reconciled remaining cap")
    resolved_output = output_path.resolve()
    if receipt.get("output_path") != str(resolved_output):
        raise ValueError("child receipt output_path does not match the CLI output path")
    allowed_roots = [(DATA_ROOT / "artifacts").resolve(), (DATA_ROOT / "datasets").resolve()]
    if not any(resolved_output == root or root in resolved_output.parents for root in allowed_roots):
        raise ValueError("output path must be under C:\\wrench-slm-data\\artifacts or datasets")
    return {
        "approval_sha256": approval_hash,
        "cases_canonical_sha256": cases_hash,
        "maximum_requests": request_count,
        "maximum_input_tokens": input_tokens,
        "maximum_output_tokens": output_tokens,
        "maximum_request_reserve_usd": str(reserve_per_request),
        "cumulative_reserve_usd": str(cumulative_reserve),
        "prior_spend_usd": str(prior),
        "prior_charge_status": prior_charge_status,
        "reconciliation_reference": reconciliation_reference,
        "remaining_cap_usd": str(remaining),
        "maximum_input_rate_usd_per_million_tokens": str(input_rate),
        "maximum_output_rate_usd_per_million_tokens": str(output_rate),
    }


def debit_attempt(reserve_usd: str, actual_cost_usd: Any | None) -> str:
    """Return charge to account for; absent/unparseable usage consumes full reserve."""
    reserve = _money(reserve_usd, "request reserve")
    try:
        actual = _money(actual_cost_usd, "actual provider cost")
    except ValueError:
        return str(reserve)
    if actual > reserve:
        raise ValueError("reported actual cost exceeds the admitted request reserve")
    return str(actual)


def conservative_input_size(messages: list[dict[str, Any]]) -> int:
    """Conservative tokenizer-free upper bound: UTF-8 content bytes + framing."""
    total = 128
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("messages must be objects")
        content = message.get("content", "")
        if not isinstance(content, str):
            raise ValueError("message content must be text")
        total += len(str(message.get("role", "")).encode("utf-8")) + len(content.encode("utf-8")) + 32
    return total
