#!/usr/bin/env python3
"""Capture bounded synthetic teacher traces through the existing SubRoute.

The caller cannot create approval. It requires a current, hash-bound human
approval file, reserves the maximum possible request cost in a durable ledger
before dispatch, sends one request at a time with retries and fallbacks off,
and retains an ambiguous reservation until authoritative reconciliation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tools.capture_minimax_teacher_traces import _normalize
from tools.provider_budget_guard import canonical_jsonl_sha256
from tools.subroute_budget_guard import (
    BudgetError,
    BudgetLedger,
    SUBROUTE_ENDPOINT,
    SubRouteApproval,
    load_approval,
)


CONTROL_METADATA_KEY = "wrench_openrouter_provider_controls"
RESPONSE_LIMIT_BYTES = 1_048_576
REQUEST_TIMEOUT_SECONDS = 60
SUBROUTE_KEY_ENV_NAMES = ("WRENCH_SUBROUTE_API_KEY", "GATEWAY_MASTER_KEY")


def _json_no_duplicates(raw: bytes, *, name: str) -> Any:
    def object_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BudgetError(f"{name}_duplicate_json_key")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=object_hook)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BudgetError(f"{name}_invalid_json") from exc


def _load_cases(path: Path, approval: SubRouteApproval) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != approval.cases_sha256:
        raise BudgetError("case_file_hash_mismatch")
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        row = _json_no_duplicates(line, name=f"case_line_{line_number}")
        if not isinstance(row, dict) or row.get("synthetic") is not True:
            raise BudgetError("only_explicit_synthetic_cases_are_allowed")
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id.strip() or case_id in ids:
            raise BudgetError("case_id_missing_or_duplicate")
        if str(row.get("split", "")).casefold() in {"heldout", "final", "test", "sealed"}:
            raise BudgetError("sealed_or_test_case_refused")
        messages = row.get("messages")
        if messages is None:
            system = row.get("system")
            prompt = row.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise BudgetError("case_prompt_missing")
            if not isinstance(system, str) or not system.strip():
                raise BudgetError("case_system_message_missing")
            messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        if not isinstance(messages, list) or not messages:
            raise BudgetError("case_messages_invalid")
        for message in messages:
            if (
                not isinstance(message, dict)
                or not isinstance(message.get("role"), str)
                or not isinstance(message.get("content"), str)
            ):
                raise BudgetError("case_message_invalid")
        row["messages"] = messages
        ids.add(case_id)
        rows.append(row)
    if len(rows) != approval.maximum_requests:
        raise BudgetError("case_count_does_not_match_approved_request_count")
    return rows


def _build_request(row: dict[str, Any], approval: SubRouteApproval) -> tuple[bytes, int]:
    controls = {
        "only": [approval.expected_provider],
        "allow_fallbacks": False,
        "max_price": {
            "prompt": float(approval.maximum_input_rate_usd_per_million_tokens),
            "completion": float(approval.maximum_output_rate_usd_per_million_tokens),
        },
    }
    body = {
        "model": approval.model_alias,
        "messages": row["messages"],
        "temperature": 0,
        "max_tokens": approval.maximum_output_tokens,
        "stream": False,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "usage": {"include": True},
        "provider": controls,
        "metadata": {CONTROL_METADATA_KEY: controls},
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > approval.maximum_request_body_bytes:
        raise BudgetError("request_body_exceeds_approved_byte_ceiling")
    conservative_input_bound = len(encoded) + 4096
    if conservative_input_bound > approval.maximum_input_tokens:
        raise BudgetError("request_exceeds_approved_input_token_bound")
    return encoded, conservative_input_bound


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def _api_key_from_environment() -> str:
    for name in SUBROUTE_KEY_ENV_NAMES:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    raise BudgetError("subroute_auth_credential_unavailable")


def _send_once(request_body: bytes, *, api_key: str) -> tuple[dict[str, Any], str, float]:
    if not isinstance(api_key, str) or not api_key.strip():
        raise BudgetError("subroute_auth_credential_unavailable")
    request = urllib.request.Request(
        SUBROUTE_ENDPOINT,
        data=request_body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    started = time.perf_counter()
    with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        body = response.read(RESPONSE_LIMIT_BYTES + 1)
        generation_id = response.headers.get("X-Generation-Id", "")
    latency_ms = (time.perf_counter() - started) * 1000
    if len(body) > RESPONSE_LIMIT_BYTES:
        raise BudgetError("response_body_exceeds_fixed_limit")
    value = _json_no_duplicates(body, name="provider_response")
    if not isinstance(value, dict):
        raise BudgetError("provider_response_shape_invalid")
    return value, generation_id, latency_ms


def _selected_endpoint(response: dict[str, Any], approval: SubRouteApproval) -> dict[str, Any]:
    metadata = response.get("openrouter_metadata")
    endpoints = metadata.get("endpoints") if isinstance(metadata, dict) else None
    available = endpoints.get("available") if isinstance(endpoints, dict) else None
    if not isinstance(available, list):
        raise BudgetError("openrouter_endpoint_metadata_missing")
    selected = [item for item in available if isinstance(item, dict) and item.get("selected") is True]
    if len(selected) != 1:
        raise BudgetError("openrouter_selected_endpoint_ambiguous")
    endpoint = selected[0]
    provider = endpoint.get("provider")
    model = endpoint.get("model")
    if not isinstance(provider, str) or provider.casefold() != approval.expected_provider:
        raise BudgetError("upstream_provider_mismatch")
    if model != approval.expected_upstream_model:
        raise BudgetError("upstream_model_mismatch")
    return {"provider": provider, "model": model, "selected": True}


def _validated_usage(response: dict[str, Any]) -> tuple[dict[str, Any], int, int, int, str]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise BudgetError("provider_usage_missing")
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    if any(type(value) is not int or value < 0 for value in (prompt, completion, total)):
        raise BudgetError("provider_usage_tokens_invalid")
    if total != prompt + completion:
        raise BudgetError("provider_usage_total_mismatch")
    cost = usage.get("cost")
    if isinstance(cost, bool) or not isinstance(cost, (str, int, float)):
        raise BudgetError("provider_billed_cost_missing")
    try:
        decimal_cost = Decimal(str(cost))
    except InvalidOperation as exc:
        raise BudgetError("provider_billed_cost_invalid") from exc
    if not decimal_cost.is_finite() or decimal_cost < 0:
        raise BudgetError("provider_billed_cost_invalid")
    # Persist only billing fields; gateways may add arbitrary fields to usage.
    safe_usage = {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cost": str(decimal_cost),
    }
    return safe_usage, prompt, completion, total, str(decimal_cost)


def _make_result(
    row: dict[str, Any],
    response: dict[str, Any],
    generation_id: str,
    endpoint: dict[str, Any],
    usage: dict[str, Any],
    latency_ms: float,
) -> dict[str, Any]:
    choice_list = response.get("choices")
    content = None
    if isinstance(choice_list, list) and choice_list and isinstance(choice_list[0], dict):
        message = choice_list[0].get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            content = message["content"]
    normalized = _normalize(content) if isinstance(content, str) else None
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest() if isinstance(content, str) else None
    response_model = endpoint["model"]
    return {
        "id": row["id"],
        "normalized_proposal": normalized,
        "response_model": response_model,
        "raw_model_output": None,
        "transport_failure": False,
        "provider": endpoint["provider"],
        "generation_id": generation_id,
        "gateway_response_model": response.get("model"),
        "openrouter_endpoint": endpoint,
        "usage": usage,
        "latency_ms": round(latency_ms, 3),
        "response_content_sha256": content_sha256,
    }


def _write_receipt_exclusive(path: Path, payload: dict[str, Any], data_root: Path) -> None:
    path = Path(os.path.abspath(path))
    root = Path(os.path.abspath(data_root))
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise BudgetError("receipt_outside_approved_storage_root") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise BudgetError("receipt_already_exists")
    temporary = path.with_name(path.name + ".tmp")
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def capture(
    approval_path: Path,
    cases_path: Path,
    *,
    data_root: Path | None = None,
    repo_root: Path | None = None,
    transport=None,
) -> dict[str, Any]:
    data_root = data_root or Path(r"C:\wrench-slm-data")
    repo_root = repo_root or Path(__file__).resolve().parents[1]
    approval = load_approval(approval_path, cases_path, data_root=data_root, repo_root=repo_root)
    cases = _load_cases(cases_path, approval)
    api_key = _api_key_from_environment() if transport is None else None
    ledger = BudgetLedger(approval, storage_root=data_root)
    if approval.receipt_path.exists():
        raise BudgetError("receipt_already_exists")
    send = transport or (lambda body: _send_once(body, api_key=api_key or ""))

    for row in cases:
        settled = ledger.settled_cases()
        if row["id"] in settled:
            continue
        request_body, _input_bound = _build_request(row, approval)
        request_sha256 = hashlib.sha256(request_body).hexdigest()
        request_id, _reserve = ledger.reserve(row["id"], request_sha256)
        try:
            ledger.mark_dispatched(request_id)
            response, generation_id, latency_ms = send(request_body)
            if not isinstance(generation_id, str) or not generation_id.strip():
                raise BudgetError("openrouter_generation_id_missing")
            endpoint = _selected_endpoint(response, approval)
            usage, prompt_tokens, completion_tokens, total_tokens, cost = _validated_usage(response)
            result = _make_result(row, response, generation_id, endpoint, usage, latency_ms)
            ledger.settle(
                request_id,
                provider_name=endpoint["provider"],
                response_model=endpoint["model"],
                generation_id=generation_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                actual_cost_usd=cost,
                usage=usage,
                safe_result=result,
            )
        except Exception as exc:
            try:
                ledger.mark_unknown(request_id, "provider_result_unverified")
            except BudgetError:
                pass
            raise BudgetError("provider_result_unverified_full_reserve_retained") from exc

    settled = ledger.settled_cases()
    if set(settled) != {row["id"] for row in cases}:
        raise BudgetError("capture_incomplete_no_aggregate_receipt_written")
    results = [settled[row["id"]]["receipt"] for row in cases]
    models = {item.get("response_model") for item in results}
    if models != {approval.expected_upstream_model}:
        raise BudgetError("settled_model_identity_not_uniform")
    summary = ledger.summary()
    payload = {
        "schema": "wrench.mechanical-worker-teacher-traces.v1",
        "status": "CAPTURED_SUBROUTE_BOUNDED_SYNTHETIC",
        "authorization": approval.approval_id,
        "teacher": {
            "endpoint": approval.endpoint,
            "requested_model_alias": approval.model_alias,
            "response_model": approval.expected_upstream_model,
            "provider": approval.expected_provider,
            "identity_status": "openrouter_selected_endpoint_and_generation_receipt_verified",
        },
        "input_path": str(approval.cases_path),
        "input_sha256": canonical_jsonl_sha256(approval.cases_path),
        "approval_sha256": approval.approval_sha256,
        "budget_ledger": summary,
        "results": results,
    }
    _write_receipt_exclusive(approval.receipt_path, payload, data_root)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    args = parser.parse_args()
    result = capture(args.approval, args.cases)
    print(json.dumps({"status": result["status"], "requests": len(result["results"]), "receipt": result["teacher"]["response_model"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
