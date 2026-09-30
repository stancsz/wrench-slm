"""Bounded accounting for token-usage fields returned in chat API responses.

This module parses synthetic or captured OpenAI-compatible response bodies and
aggregates paired task arms. It does not send requests, verify upstream billing,
or establish that a proxy preserved provider usage unchanged. Real savings claims
still require paired, auditable upstream usage receipts and task outcomes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Literal


MAX_RESPONSE_BODY_BYTES = 65_536
MAX_EPISODES = 10_000
MAX_REQUESTS = 2_048
MAX_ID_CHARS = 128
MAX_ROUTE_CHARS = 256
_ID = re.compile(r"[A-Za-z0-9._:-]+\Z", re.ASCII)
Arm = Literal["baseline", "wrench"]


class UsageCaptureError(ValueError):
    """Raised when usage is missing, malformed, unpaired, or unbounded."""


@dataclass(frozen=True)
class FrontierUsageReceipt:
    pair_id: str
    episode_manifest_sha256: str
    arm: Arm
    request_id: str
    attempt_index: int
    provider_route: str
    response_model: str
    http_status: int
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    response_sha256: str
    receipt_sha256: str


@dataclass(frozen=True)
class UsageArmEpisode:
    pair_id: str
    episode_manifest_sha256: str
    arm: Arm
    receipts: tuple[FrontierUsageReceipt, ...]
    capture_complete: bool


@dataclass(frozen=True)
class PairedFrontierUsage:
    pair_count: int
    response_model: str
    baseline_request_count: int
    wrench_request_count: int
    wrench_frontier_episode_count: int
    baseline_input_tokens: int
    baseline_output_tokens: int
    wrench_input_tokens: int
    wrench_output_tokens: int
    baseline_cached_input_tokens: int
    wrench_cached_input_tokens: int
    baseline_total_tokens: int
    wrench_total_tokens: int
    reported_token_reduction_fraction: float
    response_usage_is_billing_verified: Literal[False]


def _check_id(value: object, field: str) -> str:
    if type(value) is not str or not 1 <= len(value) <= MAX_ID_CHARS or not _ID.fullmatch(value):
        raise UsageCaptureError(f"{field}_invalid")
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise UsageCaptureError("response_duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> object:
    raise UsageCaptureError("response_non_finite_number")


def _token_count(value: object, field: str) -> int:
    if type(value) is not int or value < 0 or value > 2**63 - 1:
        raise UsageCaptureError(f"{field}_invalid")
    return value


def _manifest_digest(value: object) -> str:
    if (type(value) is not str or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)):
        raise UsageCaptureError("episode_manifest_sha256_invalid")
    return value


def _usage_receipt_digest(receipt: FrontierUsageReceipt) -> str:
    payload = {
        "pair_id": receipt.pair_id,
        "episode_manifest_sha256": receipt.episode_manifest_sha256,
        "arm": receipt.arm,
        "request_id": receipt.request_id,
        "attempt_index": receipt.attempt_index,
        "provider_route": receipt.provider_route,
        "response_model": receipt.response_model,
        "http_status": receipt.http_status,
        "input_tokens": receipt.input_tokens,
        "output_tokens": receipt.output_tokens,
        "cached_input_tokens": receipt.cached_input_tokens,
        "response_sha256": receipt.response_sha256,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def capture_openai_compatible_usage(
    *,
    response_body: bytes,
    http_status: int,
    pair_id: str,
    arm: Arm,
    episode_manifest_sha256: str,
    request_id: str,
    attempt_index: int,
    provider_route: str,
) -> FrontierUsageReceipt:
    """Extract response-reported prompt/completion usage without retaining text."""
    if type(response_body) is not bytes or not 0 < len(response_body) <= MAX_RESPONSE_BODY_BYTES:
        raise UsageCaptureError("response_body_size_invalid")
    if type(http_status) is not int or not 100 <= http_status <= 599:
        raise UsageCaptureError("http_status_invalid")
    if arm not in ("baseline", "wrench"):
        raise UsageCaptureError("arm_invalid")
    pair_id = _check_id(pair_id, "pair_id")
    episode_manifest_sha256 = _manifest_digest(episode_manifest_sha256)
    request_id = _check_id(request_id, "request_id")
    if type(attempt_index) is not int or not 0 <= attempt_index < MAX_REQUESTS:
        raise UsageCaptureError("attempt_index_invalid")
    if (type(provider_route) is not str or not 1 <= len(provider_route) <= MAX_ROUTE_CHARS
            or not all(ch.isascii() and ch.isprintable() for ch in provider_route)):
        raise UsageCaptureError("provider_route_invalid")
    try:
        response = json.loads(
            response_body,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except UsageCaptureError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise UsageCaptureError("response_json_invalid") from None
    if type(response) is not dict:
        raise UsageCaptureError("response_object_required")
    model = response.get("model")
    if type(model) is not str or not 1 <= len(model) <= MAX_ROUTE_CHARS or not model.isprintable():
        raise UsageCaptureError("response_model_invalid")
    usage = response.get("usage")
    if type(usage) is not dict:
        raise UsageCaptureError("provider_usage_missing")
    input_tokens = _token_count(usage.get("prompt_tokens"), "prompt_tokens")
    output_tokens = _token_count(usage.get("completion_tokens"), "completion_tokens")
    if "total_tokens" in usage and _token_count(usage["total_tokens"], "total_tokens") != input_tokens + output_tokens:
        raise UsageCaptureError("total_tokens_mismatch")
    prompt_details = usage.get("prompt_tokens_details", {})
    if type(prompt_details) is not dict:
        raise UsageCaptureError("prompt_tokens_details_invalid")
    cached = _token_count(prompt_details.get("cached_tokens", 0), "cached_tokens")
    if cached > input_tokens:
        raise UsageCaptureError("cached_tokens_exceed_input")
    receipt = FrontierUsageReceipt(
        pair_id=pair_id,
        episode_manifest_sha256=episode_manifest_sha256,
        arm=arm,
        request_id=request_id,
        attempt_index=attempt_index,
        provider_route=provider_route,
        response_model=model,
        http_status=http_status,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached,
        response_sha256=hashlib.sha256(response_body).hexdigest(),
        receipt_sha256="",
    )
    return replace(receipt, receipt_sha256=_usage_receipt_digest(receipt))


def _validate_receipt(
    receipt: object, *, pair_id: str, episode_manifest_sha256: str, arm: Arm
) -> FrontierUsageReceipt:
    if type(receipt) is not FrontierUsageReceipt:
        raise UsageCaptureError("receipt_type_invalid")
    if (receipt.pair_id != pair_id
            or receipt.episode_manifest_sha256 != episode_manifest_sha256
            or receipt.arm != arm):
        raise UsageCaptureError("receipt_pair_or_arm_mismatch")
    _check_id(receipt.request_id, "request_id")
    if type(receipt.attempt_index) is not int or not 0 <= receipt.attempt_index < MAX_REQUESTS:
        raise UsageCaptureError("attempt_index_invalid")
    for name in ("input_tokens", "output_tokens", "cached_input_tokens"):
        _token_count(getattr(receipt, name), name)
    if receipt.cached_input_tokens > receipt.input_tokens:
        raise UsageCaptureError("cached_tokens_exceed_input")
    if type(receipt.http_status) is not int or not 100 <= receipt.http_status <= 599:
        raise UsageCaptureError("http_status_invalid")
    if (type(receipt.response_sha256) is not str or len(receipt.response_sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in receipt.response_sha256)):
        raise UsageCaptureError("response_digest_invalid")
    if (type(receipt.provider_route) is not str or not 1 <= len(receipt.provider_route) <= MAX_ROUTE_CHARS
            or not all(ch.isascii() and ch.isprintable() for ch in receipt.provider_route)):
        raise UsageCaptureError("provider_route_invalid")
    if (type(receipt.response_model) is not str or not 1 <= len(receipt.response_model) <= MAX_ROUTE_CHARS
            or not receipt.response_model.isprintable()):
        raise UsageCaptureError("response_model_invalid")
    if (type(receipt.receipt_sha256) is not str or len(receipt.receipt_sha256) != 64
            or receipt.receipt_sha256 != _usage_receipt_digest(receipt)):
        raise UsageCaptureError("receipt_integrity_mismatch")
    return receipt


def _validate_arm_episode(episode: object, expected_arm: Arm) -> UsageArmEpisode:
    if type(episode) is not UsageArmEpisode or episode.arm != expected_arm:
        raise UsageCaptureError("arm_episode_invalid")
    pair_id = _check_id(episode.pair_id, "pair_id")
    manifest_sha256 = _manifest_digest(episode.episode_manifest_sha256)
    if type(episode.capture_complete) is not bool or not episode.capture_complete:
        raise UsageCaptureError("capture_incomplete")
    if type(episode.receipts) is not tuple or len(episode.receipts) > MAX_REQUESTS:
        raise UsageCaptureError("request_count_invalid")
    checked = tuple(_validate_receipt(
        receipt, pair_id=pair_id, episode_manifest_sha256=manifest_sha256, arm=expected_arm
    )
                    for receipt in episode.receipts)
    indexes = [receipt.attempt_index for receipt in checked]
    if indexes != list(range(len(indexes))):
        raise UsageCaptureError("attempt_indexes_not_contiguous")
    if len({receipt.request_id for receipt in checked}) != len(checked):
        raise UsageCaptureError("request_ids_duplicate")
    return episode


def aggregate_paired_frontier_usage(episodes: tuple[UsageArmEpisode, ...]) -> PairedFrontierUsage:
    """Sum every response-reported token across complete paired episodes.

    A Wrench episode may have zero Frontier calls. A baseline episode must have
    at least one call so the paired reduction denominator is observable. Missing
    usage for any call fails closed; it is never treated as zero.
    """
    if type(episodes) is not tuple or len(episodes) == 0 or len(episodes) > MAX_EPISODES * 2:
        raise UsageCaptureError("paired_episode_count_invalid")
    by_pair: dict[str, dict[str, UsageArmEpisode]] = {}
    call_total = 0
    for episode in episodes:
        if type(episode) is not UsageArmEpisode or episode.arm not in ("baseline", "wrench"):
            raise UsageCaptureError("arm_episode_invalid")
        checked = _validate_arm_episode(episode, episode.arm)
        arms = by_pair.setdefault(checked.pair_id, {})
        if checked.arm in arms:
            raise UsageCaptureError("arm_episode_duplicate")
        arms[checked.arm] = checked
        call_total += len(checked.receipts)
        if call_total > MAX_REQUESTS:
            raise UsageCaptureError("request_count_limit_exceeded")
    if not by_pair or any(set(arms) != {"baseline", "wrench"} for arms in by_pair.values()):
        raise UsageCaptureError("unpaired_episode")

    for arms in by_pair.values():
        if not arms["baseline"].receipts:
            raise UsageCaptureError("baseline_usage_denominator_zero")
        if (arms["baseline"].episode_manifest_sha256
                != arms["wrench"].episode_manifest_sha256):
            raise UsageCaptureError("paired_episode_identity_mismatch")
    aliases = {
        receipt.provider_route
        for arms in by_pair.values()
        for episode in arms.values()
        for receipt in episode.receipts
    }
    if len(aliases) != 1:
        raise UsageCaptureError("provider_route_mixed_or_missing")
    response_models = {
        receipt.response_model
        for arms in by_pair.values()
        for episode in arms.values()
        for receipt in episode.receipts
    }
    if len(response_models) != 1:
        raise UsageCaptureError("response_model_mixed_or_missing")

    def totals(arm: Arm) -> tuple[int, int, int, int]:
        receipts = [receipt for arms in by_pair.values() for receipt in arms[arm].receipts]
        return (
            len(receipts),
            sum(receipt.input_tokens for receipt in receipts),
            sum(receipt.output_tokens for receipt in receipts),
            sum(receipt.cached_input_tokens for receipt in receipts),
        )

    b_calls, b_input, b_output, b_cached = totals("baseline")
    w_calls, w_input, w_output, w_cached = totals("wrench")
    b_total, w_total = b_input + b_output, w_input + w_output
    return PairedFrontierUsage(
        pair_count=len(by_pair),
        response_model=next(iter(response_models)),
        baseline_request_count=b_calls,
        wrench_request_count=w_calls,
        wrench_frontier_episode_count=sum(bool(arms["wrench"].receipts) for arms in by_pair.values()),
        baseline_input_tokens=b_input,
        baseline_output_tokens=b_output,
        wrench_input_tokens=w_input,
        wrench_output_tokens=w_output,
        baseline_cached_input_tokens=b_cached,
        wrench_cached_input_tokens=w_cached,
        baseline_total_tokens=b_total,
        wrench_total_tokens=w_total,
        reported_token_reduction_fraction=1 - w_total / b_total,
        response_usage_is_billing_verified=False,
    )
