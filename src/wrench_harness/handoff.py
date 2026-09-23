"""Bounded frontier handoff receipts for the hybrid Wrench worker.

The local worker owns the expensive raw-payload inspection.  When it cannot
finish safely, this module packages the selected working context and the
failure evidence for a stronger model.  The raw request stays hash-bound, but
the monster payload is never copied into the handoff packet.
"""

from __future__ import annotations

import json
from typing import Any

from .mechanical import active_intent_suffix
from .prefill import _estimate_token_count, ordered_payload_sha256


_DEFAULT_CONTEXT_BUDGET = 64_000
_MAX_CONTEXT_BUDGET = 64_000
_DEFAULT_PACKET_BYTES = 1_000_000


def _clip_text(value: str, token_budget: int) -> str:
    """Clip by the same conservative estimate used by the reducer.

    Keep both edges because the beginning often contains a file or tool name,
    while the end usually contains the latest failure or current intent.
    """

    if not isinstance(value, str):
        return ""
    if token_budget < 1 or _estimate_token_count(value) <= token_budget:
        return value
    char_budget = max(64, token_budget * 4)
    while char_budget > 64:
        head = max(32, char_budget // 3)
        tail = max(32, char_budget - head)
        candidate = value[:head] + "\n<wrench:handoff-clip>\n" + value[-tail:]
        if _estimate_token_count(candidate) <= token_budget:
            return candidate
        char_budget = max(64, int(char_budget * 0.8))
    return value[:64]


def _message_content(message: Any) -> str:
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content if isinstance(content, str) else ""


def _compact_messages(
    messages: list[dict[str, str]],
    *,
    token_budget: int,
) -> tuple[list[dict[str, str]], int]:
    """Keep policy and newest intent, then fill the remainder from the tail."""

    if token_budget < 1:
        return [], 0
    selected: list[dict[str, str]] = []
    used = 0
    selected_ids: set[int] = set()

    def add(message: dict[str, str], budget: int) -> None:
        nonlocal used
        if id(message) in selected_ids or used >= token_budget:
            return
        content = _message_content(message)
        if not content:
            return
        remaining = min(budget, token_budget - used)
        clipped = _clip_text(content, remaining)
        cost = _estimate_token_count(clipped)
        if cost > token_budget - used:
            clipped = _clip_text(clipped, max(1, token_budget - used))
            cost = _estimate_token_count(clipped)
        selected.append({"role": str(message.get("role", "user")), "content": clipped})
        selected_ids.add(id(message))
        used += cost

    policy = [
        message
        for message in messages
        if isinstance(message, dict) and message.get("role") in {"system", "developer"}
    ]
    for message in policy:
        add(message, min(8_000, token_budget - used))

    user_messages = [
        message
        for message in messages
        if isinstance(message, dict) and message.get("role") == "user"
    ]
    if user_messages:
        add(user_messages[-1], min(24_000, token_budget - used))

    for message in reversed(messages):
        if isinstance(message, dict):
            add(message, token_budget - used)

    return selected, used


def _receipt_subset(receipt: dict[str, Any] | None) -> dict[str, Any]:
    """Keep evidence metadata, never a full lookup table or raw payload."""

    if not isinstance(receipt, dict):
        return {}
    allowed = {
        "schema",
        "mode",
        "pipeline",
        "raw_token_count",
        "raw_token_count_estimate",
        "model_prefill_token_count",
        "compression_ratio",
        "model_prefill_budget",
        "hot_token_budget",
        "reference_index_budget",
        "current_intent_source_index",
        "hot_message_count",
        "reference_card_count",
        "evidence_window_count",
        "lookup_table_ids",
        "map_stage",
        "reduce_stage",
        "context_gate",
        "context_gate_latency_ms",
        "source_payload_sha256",
        "prepared_payload_sha256",
        "payload_hash_mode",
        "split_current_message",
        "suffix_chars",
        "adaptive_selection",
        "native_input_claim",
        "error",
    }
    return {key: receipt[key] for key in allowed if key in receipt}


def build_advisor_handoff(
    messages: list[dict[str, str]],
    *,
    result: dict[str, Any],
    working_messages: list[dict[str, str]] | None = None,
    prefill_receipt: dict[str, Any] | None = None,
    max_context_tokens: int = _DEFAULT_CONTEXT_BUDGET,
    max_packet_bytes: int = _DEFAULT_PACKET_BYTES,
) -> dict[str, Any]:
    """Build a bounded, read-only packet for a stronger model.

    This function is intentionally pure. It does not invoke a model, perform
    I/O, or grant mutation authority. A caller may make at most two frontier
    passes, feeding each result back through Wrench's verifier.
    """

    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list")
    if not isinstance(result, dict):
        raise ValueError("result must be an object")
    if not isinstance(max_context_tokens, int) or not 1 <= max_context_tokens <= _MAX_CONTEXT_BUDGET:
        raise ValueError("max_context_tokens must be between 1 and 64000")
    if not isinstance(max_packet_bytes, int) or max_packet_bytes < 16_384:
        raise ValueError("max_packet_bytes must be at least 16384")

    user_messages = [
        message
        for message in messages
        if isinstance(message, dict) and message.get("role") == "user" and _message_content(message)
    ]
    latest_raw = _message_content(user_messages[-1]) if user_messages else ""
    latest_intent = active_intent_suffix(latest_raw, suffix_chars=16_000)
    selected, selected_tokens = _compact_messages(
        working_messages if isinstance(working_messages, list) else messages,
        token_budget=max_context_tokens,
    )
    raw_hash = None
    for key in ("source_payload_sha256", "raw_payload_sha256"):
        if isinstance(prefill_receipt, dict) and isinstance(prefill_receipt.get(key), str):
            raw_hash = prefill_receipt[key]
            break
    if raw_hash is None and isinstance(result.get("context_gate"), dict):
        raw_hash = result["context_gate"].get("raw_payload_sha256")
    if raw_hash is None:
        raw_hash = ordered_payload_sha256(messages)

    packet: dict[str, Any] = {
        "schema": "wrench.advisor-handoff.v1",
        "handoff_required": True,
        "authority": "proposal_only_no_mutation",
        "reason": str(result.get("fallback_reason", "wrench_abstain")),
        "latest_intent": _clip_text(latest_intent, min(16_000, max_context_tokens)),
        "working_context": selected,
        "working_context_token_estimate": selected_tokens,
        "context_budget_tokens": max_context_tokens,
        "raw_payload_sha256": raw_hash,
        "raw_payload_hash_bound": bool(raw_hash),
        "wrench_attempt": {
            "status": result.get("status"),
            "fallback_reason": result.get("fallback_reason"),
            "raw_model_output": _clip_text(str(result.get("raw_model_output", "")), 2_000),
            "model_calls": result.get("model_calls", 0),
            "repair_pass_count": result.get("repair_pass_count", 0),
            "intent_safety_gate": result.get("intent_safety_gate"),
        },
        "prefill": _receipt_subset(prefill_receipt),
        "frontier_policy": {
            "max_frontier_calls": 2,
            "retry_shape": "one_review_then_one_repair",
            "return_each_result_to_wrench_verifier": True,
            "frontier_must_not_execute_tools": True,
            "preserve_raw_payload_out_of_band": True,
        },
    }
    encoded = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > max_packet_bytes:
        # Reduce only the context. Metadata and the latest intent stay intact.
        excess_ratio = max_packet_bytes / max(len(encoded), 1)
        reduced_budget = max(1, int(selected_tokens * excess_ratio * 0.9))
        packet["working_context"], selected_tokens = _compact_messages(
            working_messages if isinstance(working_messages, list) else messages,
            token_budget=min(max_context_tokens, reduced_budget),
        )
        packet["working_context_token_estimate"] = selected_tokens
        encoded = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > max_packet_bytes:
        raise ValueError("advisor_handoff_packet_budget_exceeded")
    packet["packet_bytes"] = len(encoded)
    return packet
