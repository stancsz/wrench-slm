"""Content-free accounting for final OpenCode requests sent to SubRoute.

This module defines a bounded receipt consumer for a future observation point
at OpenCode's final HTTP transport. It is not wired to OpenCode or SubRoute.
The tests exercise synthetic fixtures only and say nothing about live traffic,
provider tokenization, billed cost, or task success. Raw prompt/request content
is parsed in memory and discarded; receipts retain bounded sizes, identities,
and cryptographic digests only. Digests are stable and linkable, so receipts
are content-free but not anonymous.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from typing import Literal
from urllib.parse import urlsplit


SCHEMA_VERSION = "wrench.opencode-request-capture.v1"
SUPPORTED_OPENCODE_VERSION = "2.0.12"
ROUTE_IDENTITY = "http://127.0.0.1:4000/v1/chat/completions"
MAX_REQUEST_BODY_BYTES = 1_048_576
MAX_TOP_LEVEL_FIELDS = 64
MAX_MESSAGES = 256
MAX_TOOLS = 128
MAX_PAIRED_EPISODES = 10_000
MAX_PAIRED_REQUESTS = 2_048
MAX_AGGREGATE_RECEIPT_METADATA_BYTES = 32 * 1_048_576
MAX_ID_CHARS = 128
MAX_MODEL_ALIAS_CHARS = 256
_ALLOWED_ROLES = frozenset({"system", "developer", "user", "assistant", "tool"})
_ALLOWED_ARMS = frozenset({"baseline", "wrench"})
_SAFE_FIELD_NAMES = frozenset({
    "model", "messages", "tools", "tool_choice", "parallel_tool_calls",
    "stream", "stream_options", "max_tokens", "max_completion_tokens",
    "temperature", "top_p", "n", "stop", "frequency_penalty",
    "presence_penalty", "logit_bias", "logprobs", "top_logprobs",
    "response_format", "seed", "user", "service_tier", "metadata",
    "store", "modalities", "audio", "reasoning_effort", "verbosity",
    "prediction", "web_search_options", "include", "prompt_cache_key",
})
_JSON_WS = frozenset(" \t\r\n")


class CaptureError(ValueError):
    """Raised when a request or paired receipt violates the bounded contract."""


@dataclass(frozen=True)
class RequestFieldDigest:
    """Digest and exact byte length of one top-level JSON value's raw bytes."""

    name: str
    raw_value_bytes: int
    sha256: str


@dataclass(frozen=True)
class OpenCodeRequestCapture:
    """Metadata for one exact request body, with no retained request content."""

    schema_version: str
    opencode_version: str
    route_identity: str
    pair_id: str
    arm: Literal["baseline", "wrench"]
    request_id: str
    attempt_index: int
    request_sha256: str
    body_bytes: int
    model_alias: str
    message_count: int
    role_counts: tuple[tuple[str, int], ...]
    tool_schema_count: int
    fields: tuple[RequestFieldDigest, ...]
    envelope_bytes: int
    input_tokens: None = None
    input_token_status: str = "unavailable_tokenizer_and_chat_framing_unverified"
    _integrity_sha256: str = field(default="", repr=False, compare=True)


@dataclass(frozen=True)
class RequestArmEpisode:
    """Complete capture state for one arm of one paired task episode."""

    pair_id: str
    arm: Literal["baseline", "wrench"]
    captures: tuple[OpenCodeRequestCapture, ...]
    capture_complete: bool


@dataclass(frozen=True)
class PairedRequestAccounting:
    """Transport-byte totals only; task and provider outcomes remain unknown."""

    pair_count: int
    baseline_request_count: int
    wrench_request_count: int
    baseline_zero_request_episodes: int
    wrench_zero_request_episodes: int
    baseline_body_bytes: int
    wrench_body_bytes: int
    retained_receipt_metadata_bytes: int
    body_byte_reduction_fraction: float | None
    body_byte_reduction_is_token_reduction: bool
    input_token_reduction_fraction: None
    frontier_success_retention: None
    all_in_cost_reduction_fraction: None
    task_success_rates: None
    opencode_version: str
    route_identity: str
    observed_model_aliases: tuple[str, ...]


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> object:
    raise ValueError("non_finite_json_number")


def _check_identifier(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not 1 <= len(value) <= MAX_ID_CHARS
        or not all(ch.isascii() and (ch.isalnum() or ch in "._:-") for ch in value)
    ):
        raise CaptureError(f"{field_name}_invalid")
    return value


def _validate_route(method: object, url: object) -> None:
    if type(method) is not str or method != "POST" or type(url) is not str or len(url) > 512:
        raise CaptureError("route_unsupported")
    try:
        parsed = urlsplit(url)
        valid = (
            parsed.scheme == "http"
            and parsed.hostname in {"127.0.0.1", "localhost"}
            and parsed.port == 4000
            and parsed.path == "/v1/chat/completions"
            and not parsed.query
            and not parsed.fragment
            and parsed.username is None
            and parsed.password is None
        )
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise CaptureError("route_unsupported")


def _skip_ws(text: str, index: int) -> int:
    while index < len(text) and text[index] in _JSON_WS:
        index += 1
    return index


def _raw_top_level_values(text: str, body: bytes) -> dict[str, bytes]:
    """Return byte-exact JSON value slices for the top-level object fields."""
    decoder = json.JSONDecoder(
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
    )
    index = _skip_ws(text, 0)
    if index >= len(text) or text[index] != "{":
        raise CaptureError("request_object_required")
    index += 1
    values: dict[str, bytes] = {}
    while True:
        index = _skip_ws(text, index)
        if index >= len(text):
            raise CaptureError("request_json_invalid")
        if text[index] == "}":
            index += 1
            break
        if len(values) >= MAX_TOP_LEVEL_FIELDS:
            raise CaptureError("too_many_top_level_fields")
        try:
            key, key_end = decoder.raw_decode(text, index)
        except (ValueError, json.JSONDecodeError, RecursionError):
            raise CaptureError("request_json_invalid") from None
        if type(key) is not str or key in values:
            raise CaptureError("duplicate_or_invalid_json_key")
        index = _skip_ws(text, key_end)
        if index >= len(text) or text[index] != ":":
            raise CaptureError("request_json_invalid")
        value_start = _skip_ws(text, index + 1)
        try:
            _value, value_end = decoder.raw_decode(text, value_start)
        except (ValueError, json.JSONDecodeError, RecursionError):
            raise CaptureError("request_json_invalid") from None
        try:
            start_byte = len(text[:value_start].encode("utf-8"))
            end_byte = len(text[:value_end].encode("utf-8"))
        except UnicodeEncodeError:
            raise CaptureError("request_utf8_invalid") from None
        values[key] = body[start_byte:end_byte]
        index = _skip_ws(text, value_end)
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            index += 1
            break
        raise CaptureError("request_json_invalid")
    if _skip_ws(text, index) != len(text):
        raise CaptureError("request_json_invalid")
    return values


def _safe_field_name(name: str) -> str:
    if name in _SAFE_FIELD_NAMES:
        return name
    try:
        key_digest = hashlib.sha256(name.encode("utf-8", errors="strict")).hexdigest()
    except UnicodeEncodeError:
        raise CaptureError("json_key_invalid") from None
    return f"unknown_sha256_{key_digest}"


def _capture_integrity_payload(capture: OpenCodeRequestCapture) -> bytes:
    payload = {
        "schema_version": capture.schema_version,
        "opencode_version": capture.opencode_version,
        "route_identity": capture.route_identity,
        "pair_id": capture.pair_id,
        "arm": capture.arm,
        "request_id": capture.request_id,
        "attempt_index": capture.attempt_index,
        "request_sha256": capture.request_sha256,
        "body_bytes": capture.body_bytes,
        "model_alias": capture.model_alias,
        "message_count": capture.message_count,
        "role_counts": capture.role_counts,
        "tool_schema_count": capture.tool_schema_count,
        "fields": [
            {"name": item.name, "raw_value_bytes": item.raw_value_bytes, "sha256": item.sha256}
            for item in capture.fields
        ],
        "envelope_bytes": capture.envelope_bytes,
        "input_tokens": capture.input_tokens,
        "input_token_status": capture.input_token_status,
    }
    return json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _seal_capture(capture: OpenCodeRequestCapture) -> OpenCodeRequestCapture:
    digest = hashlib.sha256(_capture_integrity_payload(capture)).hexdigest()
    return replace(capture, _integrity_sha256=digest)


def _validate_capture(capture: object) -> OpenCodeRequestCapture:
    if type(capture) is not OpenCodeRequestCapture:
        raise CaptureError("capture_type_invalid")
    if (
        capture.schema_version != SCHEMA_VERSION
        or capture.opencode_version != SUPPORTED_OPENCODE_VERSION
        or capture.route_identity != ROUTE_IDENTITY
        or type(capture.arm) is not str
        or capture.arm not in _ALLOWED_ARMS
        or type(capture.body_bytes) is not int
        or not 0 < capture.body_bytes <= MAX_REQUEST_BODY_BYTES
        or type(capture.input_tokens) is not type(None)
        or capture.input_token_status != "unavailable_tokenizer_and_chat_framing_unverified"
        or not isinstance(capture.fields, tuple)
        or type(capture.request_sha256) is not str
        or len(capture.request_sha256) != 64
    ):
        raise CaptureError("capture_contract_invalid")
    _check_identifier(capture.pair_id, "pair_id")
    _check_identifier(capture.request_id, "request_id")
    if type(capture.attempt_index) is not int or not 0 <= capture.attempt_index <= 10_000:
        raise CaptureError("attempt_index_invalid")
    expected = hashlib.sha256(_capture_integrity_payload(capture)).hexdigest()
    if capture._integrity_sha256 != expected:
        raise CaptureError("capture_integrity_mismatch")
    return capture


def capture_opencode_request(
    *,
    method: str,
    url: str,
    body: bytes,
    opencode_version: str,
    pair_id: str,
    arm: Literal["baseline", "wrench"],
    request_id: str,
    attempt_index: int,
) -> OpenCodeRequestCapture:
    """Summarize one bounded final request without retaining raw content.

    The caller must supply bytes observed at the final local HTTP transport.
    This function itself performs no I/O, networking, logging, or persistence.
    """
    _validate_route(method, url)
    if opencode_version != SUPPORTED_OPENCODE_VERSION:
        raise CaptureError("opencode_version_unsupported")
    pair_id = _check_identifier(pair_id, "pair_id")
    request_id = _check_identifier(request_id, "request_id")
    if type(arm) is not str or arm not in _ALLOWED_ARMS:
        raise CaptureError("arm_invalid")
    if type(attempt_index) is not int or not 0 <= attempt_index <= 10_000:
        raise CaptureError("attempt_index_invalid")
    if type(body) is not bytes or not 0 < len(body) <= MAX_REQUEST_BODY_BYTES:
        raise CaptureError("request_body_size_invalid")
    try:
        text = body.decode("utf-8", errors="strict")
        decoded = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
        raise CaptureError("request_json_invalid") from None
    if type(decoded) is not dict:
        raise CaptureError("request_object_required")
    model_alias = decoded.get("model")
    messages = decoded.get("messages")
    tools = decoded.get("tools", [])
    if (
        type(model_alias) is not str
        or not 1 <= len(model_alias) <= MAX_MODEL_ALIAS_CHARS
        or type(messages) is not list
        or not 1 <= len(messages) <= MAX_MESSAGES
        or type(tools) is not list
        or len(tools) > MAX_TOOLS
    ):
        raise CaptureError("request_shape_unsupported")
    role_counts: dict[str, int] = {}
    for message in messages:
        if (
            type(message) is not dict
            or type(message.get("role")) is not str
            or message.get("role") not in _ALLOWED_ROLES
        ):
            raise CaptureError("message_shape_unsupported")
        role = message["role"]
        role_counts[role] = role_counts.get(role, 0) + 1

    raw_fields = _raw_top_level_values(text, body)
    fields = tuple(
        RequestFieldDigest(
            name=_safe_field_name(name),
            raw_value_bytes=len(value_bytes),
            sha256=hashlib.sha256(value_bytes).hexdigest(),
        )
        for name, value_bytes in sorted(raw_fields.items())
    )
    value_bytes_total = sum(item.raw_value_bytes for item in fields)
    if value_bytes_total > len(body):
        raise CaptureError("request_component_accounting_invalid")
    capture = OpenCodeRequestCapture(
        schema_version=SCHEMA_VERSION,
        opencode_version=SUPPORTED_OPENCODE_VERSION,
        route_identity=ROUTE_IDENTITY,
        pair_id=pair_id,
        arm=arm,
        request_id=request_id,
        attempt_index=attempt_index,
        request_sha256=hashlib.sha256(body).hexdigest(),
        body_bytes=len(body),
        model_alias=model_alias,
        message_count=len(messages),
        role_counts=tuple(sorted(role_counts.items())),
        tool_schema_count=len(tools),
        fields=fields,
        envelope_bytes=len(body) - value_bytes_total,
    )
    return _seal_capture(capture)


def aggregate_paired_request_bytes(
    episodes: tuple[RequestArmEpisode, ...],
) -> PairedRequestAccounting:
    """Validate complete baseline/Wrench pairs and aggregate request body bytes."""
    if type(episodes) is not tuple or not episodes:
        raise CaptureError("paired_episodes_required")
    if len(episodes) > MAX_PAIRED_EPISODES:
        raise CaptureError("paired_episode_limit_exceeded")
    grouped: dict[str, dict[str, RequestArmEpisode]] = {}
    request_ids: set[str] = set()
    aliases: set[str] = set()
    request_count = 0
    receipt_metadata_bytes = 0
    for episode in episodes:
        if (
            type(episode) is not RequestArmEpisode
            or type(episode.arm) is not str
            or episode.arm not in _ALLOWED_ARMS
        ):
            raise CaptureError("episode_invalid")
        pair_id = _check_identifier(episode.pair_id, "pair_id")
        if type(episode.capture_complete) is not bool or not episode.capture_complete:
            raise CaptureError("capture_incomplete")
        if type(episode.captures) is not tuple:
            raise CaptureError("episode_captures_invalid")
        arms = grouped.setdefault(pair_id, {})
        if episode.arm in arms:
            raise CaptureError("duplicate_pair_arm")
        arms[episode.arm] = episode
        attempt_indices: list[int] = []
        for raw_capture in episode.captures:
            request_count += 1
            if request_count > MAX_PAIRED_REQUESTS:
                raise CaptureError("paired_request_limit_exceeded")
            capture = _validate_capture(raw_capture)
            if capture.pair_id != pair_id or capture.arm != episode.arm:
                raise CaptureError("capture_episode_mismatch")
            if capture.request_id in request_ids:
                raise CaptureError("duplicate_request_id")
            request_ids.add(capture.request_id)
            aliases.add(capture.model_alias)
            attempt_indices.append(capture.attempt_index)
            receipt_metadata_bytes += len(_capture_integrity_payload(capture))
            if receipt_metadata_bytes > MAX_AGGREGATE_RECEIPT_METADATA_BYTES:
                raise CaptureError("aggregate_receipt_metadata_limit_exceeded")
        if sorted(attempt_indices) != list(range(len(attempt_indices))):
            raise CaptureError("request_attempt_indices_not_contiguous")
    if any(set(arms) != _ALLOWED_ARMS for arms in grouped.values()):
        raise CaptureError("paired_arm_missing")
    if not request_ids:
        raise CaptureError("no_observed_requests")
    if len(aliases) != 1:
        raise CaptureError("model_alias_mixed_or_missing")

    baseline_bytes = 0
    wrench_bytes = 0
    baseline_count = 0
    wrench_count = 0
    baseline_zero = 0
    wrench_zero = 0
    for arms in grouped.values():
        baseline = arms["baseline"].captures
        wrench = arms["wrench"].captures
        if not baseline:
            baseline_zero += 1
        if not wrench:
            wrench_zero += 1
        pair_signatures = {
            (capture.opencode_version, capture.route_identity, capture.model_alias)
            for arm in (baseline, wrench)
            for capture in arm
        }
        if len(pair_signatures) != 1:
            raise CaptureError("paired_request_identity_mismatch")
        baseline_count += len(baseline)
        wrench_count += len(wrench)
        baseline_bytes += sum(item.body_bytes for item in baseline)
        wrench_bytes += sum(item.body_bytes for item in wrench)

    reduction = (
        (baseline_bytes - wrench_bytes) / baseline_bytes if baseline_bytes > 0 else None
    )
    return PairedRequestAccounting(
        pair_count=len(grouped),
        baseline_request_count=baseline_count,
        wrench_request_count=wrench_count,
        baseline_zero_request_episodes=baseline_zero,
        wrench_zero_request_episodes=wrench_zero,
        baseline_body_bytes=baseline_bytes,
        wrench_body_bytes=wrench_bytes,
        retained_receipt_metadata_bytes=receipt_metadata_bytes,
        body_byte_reduction_fraction=reduction,
        body_byte_reduction_is_token_reduction=False,
        input_token_reduction_fraction=None,
        frontier_success_retention=None,
        all_in_cost_reduction_fraction=None,
        task_success_rates=None,
        opencode_version=SUPPORTED_OPENCODE_VERSION,
        route_identity=ROUTE_IDENTITY,
        observed_model_aliases=tuple(sorted(aliases)),
    )
