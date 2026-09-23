"""Small model-local OpenAI-compatible server for the portable Wrench package.

The server is part of the downloaded model directory. It accepts the complete
raw request before the worker chooses a mechanical fast path or stages a
bounded model prefill. It is intentionally narrow and never executes tools.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import ipaddress
import json
import math
import multiprocessing
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib import request as urllib_request

from .core import execute_model_output
from .handoff import build_advisor_handoff
from .mechanical import active_intent_suffix
from .patching import add_bounded_repair_instruction
from .prefill import _estimate_token_count, ordered_payload_sha256
from .router import CancellationToken, ProposalRouter
from .ttc import enforce_ttc
from .worker import WrenchWorker, _dynamic_prefill_messages


MAX_INPUT_CONTEXT_TOKENS = 4_000_000
MAX_FINAL_ANSWER_CHARS = 16_384
TEST_ROUTER_TERMINATE_GRACE_SECONDS = 0.25
READ_ONLY_TOOL_NAME_MARKERS = {
    "read",
    "read_file",
    "readfile",
    "read_lines",
    "readlines",
    "literal_search",
    "search",
    "grep",
    "ripgrep",
}


def _test_router_child_entrypoint(
    invoke: Callable[[], dict[str, Any]],
    connection: Any,
) -> None:
    """Run only an explicitly injected deterministic test callback in a child."""

    try:
        result = invoke()
        if not isinstance(result, dict):
            raise TypeError("test proposal callback must return a dictionary")
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        connection.send(("result", encoded))
    except BaseException as exc:  # noqa: BLE001
        try:
            connection.send(("error", type(exc).__name__))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


def _terminate_test_router_process(process: Any) -> bool:
    """Terminate, then kill and join a test callback process within fixed bounds."""

    if not process.is_alive():
        process.join(timeout=0)
        return True
    process.terminate()
    process.join(timeout=TEST_ROUTER_TERMINATE_GRACE_SECONDS)
    if process.is_alive():
        process.kill()
        process.join(timeout=TEST_ROUTER_TERMINATE_GRACE_SECONDS)
    return not process.is_alive()


def _estimated_tokens(value: str) -> int:
    return _estimate_token_count(value)


def _request_token_estimate(messages: list[dict[str, Any]]) -> tuple[int, int, str | None]:
    raw_chars = 0
    raw_tokens = 0
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            raw_chars += len(content)
            raw_tokens += _estimated_tokens(content)
    payload_sha256 = None
    if all(
        isinstance(message, dict)
        and isinstance(message.get("role"), str)
        and isinstance(message.get("content"), str)
        for message in messages
    ):
        payload_sha256 = ordered_payload_sha256(messages)  # type: ignore[arg-type]
    return raw_chars, raw_tokens, payload_sha256


def _request_tool_names(request: dict[str, Any]) -> list[str]:
    names: list[str] = []
    tools = request.get("tools")
    if not isinstance(tools, list):
        return names
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function")
        candidate = function.get("name") if isinstance(function, dict) else tool.get("name")
        if isinstance(candidate, str) and candidate:
            names.append(candidate)
    return names


def _request_tool_specs(request: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    tools = request.get("tools")
    if not isinstance(tools, list):
        return specs
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function")
        if isinstance(function, dict) and isinstance(function.get("name"), str):
            specs.append(function)
        elif isinstance(tool.get("name"), str):
            specs.append(tool)
    return specs


def _proposal_from_result(result: dict[str, Any]) -> dict[str, Any] | None:
    raw = result.get("raw_model_output")
    if not isinstance(raw, str):
        return None
    try:
        proposal = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return proposal if isinstance(proposal, dict) else None


def _build_read_tool_call(request: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    """Translate a verified read-only proposal into a client-native tool call.

    This bridge is intentionally conservative. It only exposes read/search
    actions and only when the client supplied a matching tool definition. No
    edit, write, shell, git mutation, or arbitrary function is synthesized.
    """

    proposal = _proposal_from_result(result)
    if result.get("status") != "accepted" or proposal is None:
        return None
    action = proposal.get("action")
    if action not in {"read_file", "read_lines", "literal_search"}:
        return None
    specs = _request_tool_specs(request)
    preferred = {
        "read_file": {"read", "read_file", "readfile"},
        "read_lines": {"read", "read_lines", "readfile"},
        "literal_search": {"grep", "search", "literal_search", "ripgrep"},
    }[action]
    selected: dict[str, Any] | None = None
    for spec in specs:
        name = str(spec.get("name", ""))
        lowered = name.casefold()
        if lowered in preferred and not any(marker in lowered for marker in ("write", "edit", "bash", "shell")):
            selected = spec
            break
    if selected is None:
        return None
    name = str(selected["name"])
    parameters = selected.get("parameters")
    if not isinstance(parameters, dict):
        parameters = selected.get("input_schema")
    properties = parameters.get("properties", {}) if isinstance(parameters, dict) else {}
    if not isinstance(properties, dict):
        properties = {}

    def field(candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in properties:
                return candidate
        return candidates[0] if candidates else None

    arguments: dict[str, Any] = {}
    if action in {"read_file", "read_lines"}:
        path_field = field(("filePath", "file_path", "path"))
        if path_field is None:
            return None
        arguments[path_field] = proposal.get("path")
        if action == "read_lines":
            start = int(proposal.get("start", 1))
            end = int(proposal.get("end", start))
            offset_field = field(("offset", "start", "line_start"))
            limit_field = field(("limit", "lines", "line_limit"))
            if offset_field in properties:
                arguments[offset_field] = max(0, start - 1)
            if limit_field in properties:
                arguments[limit_field] = max(1, end - start + 1)
        elif "max_bytes" in properties:
            arguments["max_bytes"] = proposal.get("max_bytes")
        elif "limit" in properties:
            # OpenCode/Claude read tools usually bound lines, not bytes. Keep
            # the bridge conservative and visibly bounded rather than hiding
            # the semantic conversion.
            arguments["limit"] = 1
    else:
        pattern_field = field(("pattern", "literal", "query"))
        path_field = field(("path", "filePath", "file_path"))
        if pattern_field is None or path_field is None:
            return None
        arguments[pattern_field] = proposal.get("literal")
        arguments[path_field] = proposal.get("root", ".")
    return {
        "id": f"wrench-call-{uuid.uuid4().hex}",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False, separators=(",", ":"))},
    }


def _cost_accounting_receipt(
    result: dict[str, Any],
    *,
    raw_tokens: int,
    completion_tokens: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    """Expose token-flow facts without pretending they are dollar costs."""

    model_calls = result.get("model_calls", 0)
    model_calls = model_calls if isinstance(model_calls, int) and model_calls >= 0 else 0
    frontier_usage = result.get("frontier_usage")
    has_frontier_usage = isinstance(frontier_usage, dict)
    dynamic_prefill = result.get("dynamic_prefill")
    model_prompt_tokens = 0
    if model_calls and not has_frontier_usage:
        if isinstance(dynamic_prefill, dict):
            native_prompt = dynamic_prefill.get("native_backend_prompt_tokens")
            staged_prompt = dynamic_prefill.get("model_prefill_token_count")
            if isinstance(native_prompt, int) and native_prompt >= 0:
                model_prompt_tokens = native_prompt
            elif isinstance(staged_prompt, int) and staged_prompt >= 0:
                model_prompt_tokens = staged_prompt
        if model_prompt_tokens == 0:
            model_prompt_tokens = raw_tokens
    model_completion_tokens = completion_tokens if model_calls and not has_frontier_usage else 0
    frontier_tokens = 0
    frontier_prompt_tokens = 0
    frontier_completion_tokens = 0
    frontier_cost = None
    if isinstance(frontier_usage, dict):
        prompt = frontier_usage.get("prompt_tokens")
        if isinstance(prompt, int) and prompt >= 0:
            frontier_prompt_tokens = prompt
        completion = frontier_usage.get("completion_tokens")
        if isinstance(completion, int) and completion >= 0:
            frontier_completion_tokens = completion
        total = frontier_usage.get("total_tokens")
        if isinstance(total, int) and total >= 0:
            frontier_tokens = total
        cost = frontier_usage.get("cost")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            frontier_cost = float(cost)
    receipt = {
        "schema": "wrench.cost-accounting-receipt.v1",
        "raw_input_tokens": raw_tokens,
        "model_prompt_tokens": model_prompt_tokens,
        "model_completion_tokens": model_completion_tokens,
        "local_model_tokens": model_prompt_tokens + model_completion_tokens,
        "input_tokens_not_sent_to_model": max(0, raw_tokens - model_prompt_tokens),
        "model_calls": model_calls,
        "local_model_calls": 0 if has_frontier_usage else model_calls,
        "repair_passes": result.get("repair_pass_count", 0),
        "frontier_tokens": frontier_tokens,
        "frontier_prompt_tokens": frontier_prompt_tokens,
        "frontier_completion_tokens": frontier_completion_tokens,
        "frontier_cost_usd": frontier_cost,
        "total_workflow_tokens": (
            model_prompt_tokens + model_completion_tokens + frontier_tokens
        ),
        "mechanical_fast_path": bool(result.get("mechanical_fast_path", False)),
        "total_local_elapsed_ms": round(elapsed_ms, 3),
        "usd_cost": None,
        "usd_cost_status": "not_priced_local_runtime",
    }
    if isinstance(frontier_usage, dict):
        receipt["frontier_usage"] = frontier_usage
    return receipt


def _completion_response(
    result: dict[str, Any],
    *,
    model_name: str,
    raw_chars: int,
    raw_tokens: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    content = result.get("raw_model_output")
    if not isinstance(content, str):
        content = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    completion_tokens = _estimated_tokens(content)
    response: dict[str, Any] = {
        "id": f"wrench-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": (
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [result["tool_call"]],
                    }
                    if isinstance(result.get("tool_call"), dict)
                    else {"role": "assistant", "content": content}
                ),
                "finish_reason": "tool_calls" if isinstance(result.get("tool_call"), dict) else "stop",
            }
        ],
        "usage": {
            "prompt_tokens": raw_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": raw_tokens + completion_tokens,
        },
        "wrench": {
            "raw_input_chars": raw_chars,
            "raw_input_tokens_estimate": raw_tokens,
            "elapsed_ms": round(elapsed_ms, 3),
            "status": result.get("status"),
            "backend": result.get("backend"),
            "mechanical_fast_path": result.get("mechanical_fast_path", False),
            "model_calls": result.get("model_calls", 0),
            "repair_pass_count": result.get("repair_pass_count", 0),
            "context_gate": result.get("context_gate"),
            "dynamic_prefill": result.get("dynamic_prefill"),
            "fallback_reason": result.get("fallback_reason"),
            "advisor_handoff": result.get("advisor_handoff"),
            "upstream_attempts": result.get("upstream_attempts"),
            "frontier_usage": result.get("frontier_usage"),
            "frontier_round": result.get("frontier_round"),
            "final_answer": result.get("final_answer", False),
            "tool_result_sha256": result.get("tool_result_sha256"),
            "ttc": result.get("ttc"),
            "cost_accounting": _cost_accounting_receipt(
                result,
                raw_tokens=raw_tokens,
                completion_tokens=completion_tokens,
                elapsed_ms=elapsed_ms,
            ),
        },
    }
    test_router_status = result.get("test_only_router_status")
    if isinstance(test_router_status, dict):
        response["wrench"]["test_only_proposal_router"] = test_router_status
    return response


def _completion_stream_chunks(response: dict[str, Any]) -> list[str]:
    """Encode one completed response as OpenAI-compatible SSE chunks."""

    choice = response["choices"][0]
    message = choice.get("message", {})
    content = message.get("content", "")
    identifier = response.get("id")
    model = response.get("model")
    created = response.get("created")
    if isinstance(message.get("tool_calls"), list) and message["tool_calls"]:
        tool_call = message["tool_calls"][0]
        function = tool_call.get("function", {})
        chunks = [
            {
                "id": identifier,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            },
            {
                "id": identifier,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": tool_call.get("id"),
                                    "type": "function",
                                    "function": {
                                        "name": function.get("name"),
                                        "arguments": function.get("arguments", ""),
                                    },
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": identifier,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
                "usage": response.get("usage"),
                "wrench": response.get("wrench"),
            },
        ]
        return [f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n" for chunk in chunks] + ["data: [DONE]\n\n"]
    chunks = [
        {
            "id": identifier,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
        },
        {
            "id": identifier,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
        },
        {
            "id": identifier,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": choice.get("finish_reason", "stop")}],
            "usage": response.get("usage"),
            "wrench": response.get("wrench"),
        },
    ]
    return [f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n" for chunk in chunks] + ["data: [DONE]\n\n"]


def _anthropic_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif block.get("type") == "tool_result":
                parts.append(_tool_result_text(block.get("content")))
        return "\n".join(part for part in parts if part)
    return _tool_result_text(content)


def _normalize_anthropic_messages(request: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize Claude Messages input to the internal bounded message shape."""

    messages: list[dict[str, Any]] = []
    system = request.get("system")
    system_text = _anthropic_text(system)
    if system_text:
        messages.append({"role": "system", "content": system_text})
    raw_messages = request.get("messages")
    if not isinstance(raw_messages, list):
        raise ValueError("messages must be a list")
    for message in raw_messages:
        if not isinstance(message, dict) or not isinstance(message.get("role"), str):
            raise ValueError("messages must contain role-bearing objects")
        role = message["role"]
        content = message.get("content")
        if isinstance(content, list) and any(
            isinstance(block, dict) and block.get("type") == "tool_result"
            for block in content
        ):
            normalized: dict[str, Any] = {
                "role": "tool",
                "content": _anthropic_text(content),
            }
            tool_results = [
                block for block in content if isinstance(block, dict) and block.get("type") == "tool_result"
            ]
            if tool_results and isinstance(tool_results[0].get("tool_use_id"), str):
                normalized["tool_call_id"] = tool_results[0]["tool_use_id"]
            messages.append(normalized)
        elif role == "tool":
            messages.append({"role": "tool", "content": _anthropic_text(content)})
        elif role in {"user", "assistant", "system"}:
            normalized = {"role": role, "content": _anthropic_text(content)}
            if role == "assistant" and isinstance(content, list):
                tool_calls = []
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    name = block.get("name")
                    call_id = block.get("id")
                    if isinstance(name, str) and isinstance(call_id, str):
                        tool_calls.append(
                            {
                                "id": call_id,
                                "function": {"name": name},
                            }
                        )
                if tool_calls:
                    normalized["tool_calls"] = tool_calls
            messages.append(normalized)
        else:
            raise ValueError(f"unsupported message role: {role}")
    return messages


def _anthropic_tool_use(result: dict[str, Any]) -> dict[str, Any] | None:
    tool_call = result.get("tool_call")
    if not isinstance(tool_call, dict):
        return None
    function = tool_call.get("function")
    if not isinstance(function, dict) or not isinstance(function.get("name"), str):
        return None
    arguments: dict[str, Any]
    try:
        parsed = json.loads(str(function.get("arguments", "{}")))
        arguments = parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        arguments = {}
    return {
        "type": "tool_use",
        "id": str(tool_call.get("id") or f"wrench-tool-{uuid.uuid4().hex}"),
        "name": function["name"],
        "input": arguments,
    }


def _anthropic_response(
    result: dict[str, Any],
    *,
    model_name: str,
    raw_chars: int,
    raw_tokens: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    content = result.get("raw_model_output")
    if not isinstance(content, str):
        content = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    tool_use = _anthropic_tool_use(result)
    blocks = [tool_use] if tool_use is not None else [{"type": "text", "text": content}]
    completion_tokens = _estimated_tokens(content)
    return {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "role": "assistant",
        "model": model_name,
        "content": blocks,
        "stop_reason": "tool_use" if tool_use is not None else "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": raw_tokens, "output_tokens": completion_tokens},
        "wrench": {
            "raw_input_chars": raw_chars,
            "raw_input_tokens_estimate": raw_tokens,
            "elapsed_ms": round(elapsed_ms, 3),
            "status": result.get("status"),
            "backend": result.get("backend"),
            "mechanical_fast_path": result.get("mechanical_fast_path", False),
            "model_calls": result.get("model_calls", 0),
            "repair_pass_count": result.get("repair_pass_count", 0),
            "context_gate": result.get("context_gate"),
            "advisor_handoff": result.get("advisor_handoff"),
            "upstream_attempts": result.get("upstream_attempts"),
            "frontier_usage": result.get("frontier_usage"),
            "frontier_round": result.get("frontier_round"),
            "final_answer": result.get("final_answer", False),
            "tool_result_sha256": result.get("tool_result_sha256"),
            "cost_accounting": _cost_accounting_receipt(
                result,
                raw_tokens=raw_tokens,
                completion_tokens=completion_tokens,
                elapsed_ms=elapsed_ms,
            ),
        },
    }


def _anthropic_stream_chunks(response: dict[str, Any]) -> list[str]:
    """Encode a complete Anthropic Messages response as valid SSE events."""

    block = response["content"][0]
    usage = response.get("usage", {})
    message = {
        "id": response["id"],
        "type": "message",
        "role": "assistant",
        "model": response["model"],
        "content": [],
        "stop_reason": None,
        "stop_sequence": None,
        "usage": {"input_tokens": usage.get("input_tokens", 0), "output_tokens": 0},
        "wrench": response.get("wrench"),
    }
    events: list[dict[str, Any]] = [
        {"event": "message_start", "data": {"type": "message_start", "message": message}},
        {
            "event": "content_block_start",
            "data": {"type": "content_block_start", "index": 0, "content_block": (
                {"type": "text", "text": ""}
                if block.get("type") == "text"
                else {"type": "tool_use", "id": block["id"], "name": block["name"], "input": {}}
            )},
        },
    ]
    if block.get("type") == "text":
        events.append(
            {
                "event": "content_block_delta",
                "data": {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": block.get("text", "")},
                },
            }
        )
    else:
        events.append(
            {
                "event": "content_block_delta",
                "data": {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {
                        "type": "input_json_delta",
                        "partial_json": json.dumps(block.get("input", {}), ensure_ascii=False),
                    },
                },
            }
        )
    events.extend(
        [
            {"event": "content_block_stop", "data": {"type": "content_block_stop", "index": 0}},
            {
                "event": "message_delta",
                "data": {
                    "type": "message_delta",
                    "delta": {
                        "stop_reason": response.get("stop_reason"),
                        "stop_sequence": None,
                    },
                    "usage": {"output_tokens": usage.get("output_tokens", 0)},
                },
            },
            {"event": "message_stop", "data": {"type": "message_stop"}},
        ]
    )
    return [
        f"event: {item['event']}\ndata: {json.dumps(item['data'], ensure_ascii=False)}\n\n"
        for item in events
    ]


def _ollama_response(
    result: dict[str, Any],
    *,
    model_name: str,
    raw_chars: int,
    raw_tokens: int,
    elapsed_ms: float,
    chat: bool,
    declared_context_tokens: int | None,
) -> dict[str, Any]:
    """Return the small Ollama-compatible response shape used by local clients.

    This is an API compatibility layer inside the package. It does not claim
    that the stock Ollama binary can load Wrench's hybrid checkpoint.
    """

    content = result.get("raw_model_output")
    if not isinstance(content, str):
        content = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    completion_tokens = _estimated_tokens(content)
    wrench = {
        "raw_input_chars": raw_chars,
        "raw_input_tokens_estimate": raw_tokens,
        "elapsed_ms": round(elapsed_ms, 3),
        "status": result.get("status"),
        "backend": result.get("backend"),
        "mechanical_fast_path": result.get("mechanical_fast_path", False),
        "model_calls": result.get("model_calls", 0),
        "repair_pass_count": result.get("repair_pass_count", 0),
        "context_gate": result.get("context_gate"),
        "dynamic_prefill": result.get("dynamic_prefill"),
        "fallback_reason": result.get("fallback_reason"),
        "advisor_handoff": result.get("advisor_handoff"),
        "upstream_attempts": result.get("upstream_attempts"),
        "frontier_usage": result.get("frontier_usage"),
        "frontier_round": result.get("frontier_round"),
        "final_answer": result.get("final_answer", False),
        "tool_result_sha256": result.get("tool_result_sha256"),
        "ttc": result.get("ttc"),
        "declared_context_tokens": declared_context_tokens,
        "cost_accounting": _cost_accounting_receipt(
            result,
            raw_tokens=raw_tokens,
            completion_tokens=completion_tokens,
            elapsed_ms=elapsed_ms,
        ),
    }
    response: dict[str, Any] = {
        "model": model_name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": raw_tokens,
        "eval_count": completion_tokens,
        "wrench": wrench,
    }
    if chat:
        response["message"] = {"role": "assistant", "content": content}
    else:
        response["response"] = content
    return response


def _upstream_payload(
    request: dict[str, Any],
    *,
    path: str,
    messages_override: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Translate package-local Ollama-shaped requests to OpenAI chat input."""

    if messages_override is not None:
        messages = messages_override
    elif path == "/api/generate":
        prompt = request.get("prompt")
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")
        messages: list[dict[str, Any]] = []
        system = request.get("system")
        if isinstance(system, str) and system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
    else:
        messages = request.get("messages")
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
    options = request.get("options")
    max_tokens = request.get("max_tokens", 256)
    if isinstance(options, dict) and isinstance(options.get("num_predict"), int):
        max_tokens = options["num_predict"]
    return {
        "model": str(request.get("model") or "wrench-4b"),
        "messages": messages,
        "max_tokens": max_tokens,
        # The package owns the Ollama-shaped response, so the native backend
        # must return one complete candidate for local verification.
        "stream": False,
    }


def _forward_upstream(
    upstream_url: str,
    request: dict[str, Any],
    *,
    path: str,
    timeout_seconds: float,
    messages_override: list[dict[str, str]] | None = None,
    response_metadata: dict[str, Any] | None = None,
) -> str:
    """Ask the native backend for text, without giving it execution authority."""

    body = json.dumps(
        _upstream_payload(request, path=path, messages_override=messages_override),
        ensure_ascii=False,
    ).encode("utf-8")
    upstream_request = urllib_request.Request(
        upstream_url,
        data=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        method="POST",
    )
    with urllib_request.urlopen(upstream_request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if response_metadata is not None and isinstance(payload, dict):
        usage = payload.get("usage")
        if isinstance(usage, dict):
            response_metadata["usage"] = usage
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
        if isinstance(choices[0].get("text"), str):
            return choices[0]["text"]
    raise ValueError("native_backend_response_missing_text")


_UPSTREAM_RETRYABLE_REASONS = {
    "model_output_not_text",
    "model_output_invalid_json",
    "model_output_not_object",
}


def _frontier_usage_receipt(usages: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate only bounded numeric usage fields from upstream attempts."""

    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    cost = 0.0
    cost_seen = False
    for usage in usages:
        if not isinstance(usage, dict):
            continue
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        total = usage.get("total_tokens")
        if isinstance(prompt, int) and not isinstance(prompt, bool):
            prompt_tokens += prompt
        if isinstance(completion, int) and not isinstance(completion, bool):
            completion_tokens += completion
        if isinstance(total, int) and not isinstance(total, bool):
            total_tokens += total
        elif isinstance(prompt, int) and isinstance(completion, int):
            total_tokens += prompt + completion
        value = usage.get("cost")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            cost += float(value)
            cost_seen = True
    receipt: dict[str, Any] = {
        "schema": "wrench.frontier-usage-receipt.v1",
        "attempt_count": len(usages),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    if cost_seen:
        receipt["cost"] = round(cost, 10)
    return receipt


def _latest_user_prompt(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user" and isinstance(message.get("content"), str):
            return message["content"]
    return ""


def _bounded_verification_prompt(messages: list[dict[str, Any]]) -> str:
    """Keep verifier work proportional to active intent, not raw history.

    The raw payload is already hash-bound in the prefill receipt. Older
    material is reference-only, so semantic guards and TTC should inspect the
    same bounded current-intent suffix used by the mechanical router. Passing
    a 4M string into repeated ``lower()`` calls here would turn a fast staged
    handoff into a multi-second CPU scan.
    """

    prompt = _latest_user_prompt(messages)
    try:
        suffix_chars = int(os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS", "16000"))
    except ValueError:
        suffix_chars = 16_000
    return active_intent_suffix(prompt, suffix_chars=max(1, suffix_chars))


def _tool_result_text(content: Any) -> str:
    """Extract a bounded, displayable result from a client tool message."""

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, dict) and isinstance(block.get("content"), str):
                parts.append(block["content"])
        return "\n".join(parts)
    if content is None:
        return ""
    return json.dumps(content, ensure_ascii=False, separators=(",", ":"))


def _bounded_tool_result(content: Any) -> str:
    """Render one client result exactly as it is exposed to the final answer."""

    raw = _tool_result_text(content)
    bounded = raw[:MAX_FINAL_ANSWER_CHARS]
    if not bounded:
        bounded = "(client tool returned no displayable content)"
    if len(raw) > len(bounded):
        bounded += "\n[tool result truncated by Wrench]"
    return bounded


def _read_only_tool_call_id(call: Any) -> str | None:
    if not isinstance(call, dict):
        return None
    function = call.get("function")
    name = function.get("name") if isinstance(function, dict) else call.get("name")
    if not isinstance(name, str) or name.casefold() not in READ_ONLY_TOOL_NAME_MARKERS:
        return None
    call_id = call.get("id")
    return call_id if isinstance(call_id, str) and call_id else None


def _read_only_tool_call_ids(messages: list[dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        calls = message.get("tool_calls")
        if isinstance(calls, list):
            for call in calls:
                call_id = _read_only_tool_call_id(call)
                if call_id is not None:
                    ids.add(call_id)
    return ids


def _tool_result_call_id(message: dict[str, Any]) -> str | None:
    call_id = message.get("tool_call_id")
    if isinstance(call_id, str) and call_id:
        return call_id
    content = message.get("content")
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            candidate = block.get("tool_use_id")
            if isinstance(candidate, str) and candidate:
                return candidate
    return None


def _latest_verified_tool_result(messages: list[dict[str, Any]]) -> dict[str, str] | None:
    """Return the latest read-only result only when it matches Wrench's call."""

    if not messages:
        return None
    allowed_call_ids = _read_only_tool_call_ids(messages)
    for candidate in reversed(messages):
        if not isinstance(candidate, dict):
            continue
        if candidate.get("role") == "user":
            return None
        content = candidate.get("content")
        is_tool_message = candidate.get("role") == "tool"
        if isinstance(content, list):
            is_tool_message = is_tool_message or any(
                isinstance(block, dict) and block.get("type") == "tool_result"
                for block in content
            )
        if not is_tool_message:
            continue
        call_id = _tool_result_call_id(candidate)
        if call_id is None or call_id not in allowed_call_ids:
            return None
        bounded = _bounded_tool_result(content)
        return {
            "text": bounded,
            "sha256": hashlib.sha256(bounded.encode("utf-8")).hexdigest(),
            "call_id": call_id,
        }
    return None


def _add_bounded_final_answer_instruction(
    messages: list[dict[str, Any]],
    *,
    tool_result_sha256: str,
) -> list[dict[str, Any]]:
    """Tell the upstream that this request is the one bounded final round."""

    instruction = (
        "<wrench:final-answer schema=wrench.final-answer.v1>\n"
        "A read-only Wrench tool call was verified and executed. Return exactly one JSON object, "
        "with only schema, answer, and tool_result_sha256 fields. The schema must be "
        "wrench.final-answer.v1. answer must be a concise string of at most 16384 characters. "
        f"tool_result_sha256 must equal {tool_result_sha256}. Do not return a proposal, tool call, "
        "action, mutation, shell command, markdown, or surrounding prose.\n"
        "</wrench:final-answer>"
    )
    return [*messages, {"role": "system", "content": instruction}]


def _parse_final_answer_output(
    model_output: Any,
    *,
    tool_result_sha256: str,
) -> dict[str, Any]:
    """Validate the only response allowed after a verified read-only result."""

    if not isinstance(model_output, str) or not model_output.strip():
        return {"status": "abstain", "fallback_reason": "final_answer_not_text"}
    try:
        envelope = json.loads(model_output)
    except json.JSONDecodeError:
        return {"status": "abstain", "fallback_reason": "final_answer_invalid_json"}
    if not isinstance(envelope, dict):
        return {"status": "abstain", "fallback_reason": "final_answer_not_object"}
    if set(envelope) != {"schema", "answer", "tool_result_sha256"}:
        return {"status": "abstain", "fallback_reason": "final_answer_fields_invalid"}
    if envelope.get("schema") != "wrench.final-answer.v1":
        return {"status": "abstain", "fallback_reason": "final_answer_schema_invalid"}
    answer = envelope.get("answer")
    if not isinstance(answer, str) or not answer.strip() or len(answer) > MAX_FINAL_ANSWER_CHARS:
        return {"status": "abstain", "fallback_reason": "final_answer_length_invalid"}
    if envelope.get("tool_result_sha256") != tool_result_sha256:
        return {"status": "abstain", "fallback_reason": "final_answer_hash_mismatch"}
    return {
        "status": "accepted",
        "backend": "native-upstream-final-verified",
        "mechanical_fast_path": False,
        "raw_model_output": answer,
        "final_answer": True,
        "final_answer_envelope": envelope,
        "tool_result_sha256": tool_result_sha256,
        "frontier_round": 2,
    }


def _tool_settlement_result(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Turn a completed client-side read tool call into one final assistant turn.

    OpenCode and similar clients send the tool result back to the model after
    executing the model's proposed function. Without this boundary, the
    mechanical router would see the original intent again and propose the same
    function forever. Settlement is deliberately local and bounded: Wrench
    does not execute, reinterpret, or authorize the returned tool content.
    """

    if not messages:
        return None
    latest: dict[str, Any] | None = None
    for candidate in reversed(messages):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        is_tool_message = candidate.get("role") == "tool"
        if isinstance(content, list):
            is_tool_message = is_tool_message or any(
                isinstance(block, dict) and block.get("type") == "tool_result"
                for block in content
            )
        if is_tool_message:
            latest = candidate
            break
        # A new ordinary user turn after an earlier tool result starts a new
        # request and must not be settled from stale tool output.
        if candidate.get("role") == "user":
            return None
    if latest is None:
        return None
    content = latest.get("content")
    bounded = _bounded_tool_result(content)
    return {
        "status": "accepted",
        "backend": "embedded-mechanical-settlement",
        "mechanical_fast_path": True,
        "model_calls": 0,
        "repair_pass_count": 0,
        "raw_model_output": (
            "Wrench completed the requested read-only tool call. "
            "The client tool result is authoritative.\n\n"
            f"Tool result:\n{bounded}"
        ),
        "context_gate": {"mode": "tool_settlement", "tool_result_chars": len(bounded)},
    }


def _deterministic_title_result(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Answer a harness session-title preflight without routing its prompt as work."""

    title_prefix = "Generate the session title from this JSON array of human messages:"
    marker = "JSON array of human messages:"
    for message in messages:
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            continue
        content = message["content"]
        if not content.casefold().startswith(title_prefix.casefold()):
            continue
        title = "Wrench session"
        candidate = content.split(marker, 1)[-1].strip() if marker in content else ""
        try:
            parsed = json.loads(candidate)
            texts = [
                item.get("text")
                for item in parsed
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ]
        except json.JSONDecodeError:
            texts = []
        if texts:
            words = texts[0].replace("\n", " ").split()
            title = " ".join(words[:5]).strip(".,:;!?\"'") or title
        return {
            "status": "accepted",
            "backend": "embedded-title-mechanical",
            "mechanical_fast_path": True,
            "model_calls": 0,
            "repair_pass_count": 0,
            "raw_model_output": title,
            "context_gate": {"mode": "session_title_preflight"},
        }
    return None


def _native_direct_input_receipt(
    messages: list[dict[str, str]],
    raw_tokens: int,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    for message in messages:
        digest.update(
            json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        digest.update(b"\n")
    return {
        "schema": "wrench.dynamic-prefill-receipt.v1",
        "mode": "native_direct_input",
        "raw_token_count": raw_tokens,
        "model_prefill_token_count": raw_tokens,
        "compression_ratio": 1.0,
        "native_input_claim": True,
        "native_direct_input": True,
        "source_payload_sha256": digest.hexdigest(),
        "payload_hash_mode": "ordered_message_json",
        "server_staging_elapsed_ms": 0.0,
    }


class WrenchRequestHandler(BaseHTTPRequestHandler):
    server_version = "WrenchModelServer/1.0"
    # A 4M logical request is commonly tens of megabytes on the wire. The
    # stdlib handler's small default buffered reader makes localhost uploads
    # needlessly syscall-bound before MapReduce can even start. Keep the
    # package-local endpoint responsive for monster payload intake without
    # changing the logical context contract.
    rbufsize = 1024 * 1024
    wbufsize = 1024 * 1024

    def _server(self) -> "WrenchHTTPServer":
        return self.server  # type: ignore[return-value]

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_ndjson(self, status: int, payload: dict[str, Any]) -> None:
        body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, chunks: list[str]) -> None:
        body = "".join(chunks).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        server = self._server()
        route = self.path.split("?", 1)[0]
        if route == "/health":
            self._send_json(200, {"status": "ok", "model": server.model_name})
            return
        if route == "/v1/models":
            self._send_json(
                200,
                {
                    "object": "list",
                    "data": [{"id": server.model_name, "object": "model", "owned_by": "wrench"}],
                },
            )
            return
        if route == "/api/version":
            # Ollama clients probe this endpoint before /api/tags and /api/chat.
            # Keep the response compatible without claiming native Ollama
            # decoder support or exposing an upstream model version.
            self._send_json(200, {"version": "0.32.13", "wrench_api": "ollama-compatible"})
            return
        if route == "/api/tags":
            self._send_json(
                200,
                {
                    "models": [
                        {
                            "name": server.model_name,
                            "model": server.model_name,
                            "modified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "size": 0,
                            "digest": "sha256:" + ("0" * 64),
                            "details": {
                                "parent_model": "",
                                "format": "safetensors",
                                "family": "wrench",
                                "families": ["wrench"],
                                "parameter_size": "3.88B",
                                "quantization_level": "NVFP4-W4A16",
                            },
                        }
                    ]
                },
            )
            return
        if route == "/api/show":
            self._send_json(
                200,
                {
                    "name": server.model_name,
                    "details": {
                        "family": "wrench",
                        "parameter_size": "3.88B",
                        "context_length": 4_000_000,
                    },
                    "parameters": "num_ctx 4000000\ntemperature 0",
                    "wrench": {
                        "declared_input_context_tokens": 4_000_000,
                        "effective_working_context_tokens": 64_000,
                        "native_attention_context_tokens_verified": None,
                    },
                },
            )
            return
        self._send_json(404, {"error": {"message": "not_found", "type": "invalid_request_error"}})

    def do_HEAD(self) -> None:  # noqa: N802
        # The official Ollama client performs a HEAD / heartbeat before model
        # discovery. Keep this bodyless and deterministic so the compatible
        # API can be used by the CLI, not only by curl or SDK callers.
        route = self.path.split("?", 1)[0]
        if route in {"/", "/health", "/api/version"}:
            self.send_response(200)
        else:
            self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        server = self._server()
        route = self.path.split("?", 1)[0]
        # Claude Code's Anthropic client may append /v1 to a base URL that
        # already points at a versioned OpenAI-style root. Accept that one
        # harmless alias so the model directory remains easy to configure.
        if route.startswith("/v1/v1/"):
            route = route[3:]
        if route == "/api/show":
            self._send_json(
                200,
                {
                    "name": server.model_name,
                    "details": {
                        "family": "wrench",
                        "parameter_size": "3.88B",
                        "context_length": 4_000_000,
                    },
                    "parameters": "num_ctx 4000000\ntemperature 0",
                    "wrench": {
                        "declared_input_context_tokens": 4_000_000,
                        "effective_working_context_tokens": 64_000,
                        "native_attention_context_tokens_verified": None,
                    },
                },
            )
            return
        if route not in {"/v1/chat/completions", "/v1/messages", "/api/chat", "/api/generate"}:
            self._send_json(404, {"error": {"message": "not_found", "type": "invalid_request_error"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > server.max_request_bytes:
                raise ValueError("request_body_too_large_or_empty")
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            if route == "/api/generate":
                prompt = request.get("prompt")
                if not isinstance(prompt, str):
                    raise ValueError("prompt must be a string")
                messages = []
                system = request.get("system")
                if isinstance(system, str) and system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
            elif route == "/v1/messages":
                messages = _normalize_anthropic_messages(request)
            else:
                messages = request.get("messages")
            if not isinstance(messages, list):
                raise ValueError("messages must be a list")
            model_name = str(request.get("model") or server.model_name)
            raw_chars, raw_tokens, raw_payload_sha256 = _request_token_estimate(messages)
            options = request.get("options")
            declared_context_tokens = None
            if isinstance(options, dict) and "num_ctx" in options:
                declared_context_tokens = options.get("num_ctx")
                if (
                    not isinstance(declared_context_tokens, int)
                    or isinstance(declared_context_tokens, bool)
                    or declared_context_tokens < 1
                ):
                    raise ValueError("options.num_ctx must be a positive integer")
                if declared_context_tokens > MAX_INPUT_CONTEXT_TOKENS:
                    raise ValueError("options.num_ctx_exceeds_4000000_token_limit")
            if raw_tokens > MAX_INPUT_CONTEXT_TOKENS:
                raise ValueError("input_context_exceeds_4000000_token_limit")
            started = time.perf_counter()
            title_result = _deterministic_title_result(messages) if server.use_mechanical_route else None
            settlement = (
                None
                if title_result is not None or not server.use_mechanical_route
                else _tool_settlement_result(messages)
            )
            if server.test_only_proposal_router is not None:
                result = server.run_test_only_proposal()
            elif title_result is not None:
                result = title_result
            elif settlement is not None:
                result = settlement
            else:
                # Mechanical-only and native-upstream package modes keep the
                # Transformers model unloaded. Their bounded parser, verifier,
                # and read-only routes are independent per request, so holding
                # the model-generation lock would serialize otherwise cheap
                # concurrent work behind a slow health/search probe. Retain
                # the lock only when an in-process model can actually generate.
                worker_guard = (
                    server.worker_lock
                    if server.worker.model is not None
                    else nullcontext()
                )
                with worker_guard:
                    result = server.worker.propose(
                        messages,
                        max_tokens=int(request.get("max_tokens", 256)),
                        use_mechanical_route=server.use_mechanical_route,
                    )
                    if server.upstream_url and not result.get("mechanical_fast_path", False):
                        # The downloaded package accepts the complete raw request,
                        # but a native backend should only pay model compute for a
                        # deterministic hot set plus lookup cards. Preserve the
                        # original messages for verification and receipt hashing.
                        prefill_started = time.perf_counter()
                        if os.environ.get("WRENCH_NATIVE_DIRECT_INPUT", "0") == "1":
                            staged_messages = messages
                            prefill_receipt = _native_direct_input_receipt(messages, raw_tokens)
                        else:
                            staged_messages, prefill_receipt = _dynamic_prefill_messages(
                                messages,
                                mechanical_index=server.worker.prefill_index,
                                original_payload_sha256=(
                                    raw_payload_sha256
                                    or hashlib.sha256(
                                        json.dumps(
                                            messages,
                                            ensure_ascii=False,
                                            separators=(",", ":"),
                                        ).encode("utf-8")
                                    ).hexdigest()
                                ),
                            )
                            if prefill_receipt is not None:
                                prefill_receipt["server_staging_elapsed_ms"] = round(
                                    (time.perf_counter() - prefill_started) * 1000,
                                    3,
                                )
                                prefill_receipt["cache"] = server.worker.prefill_index.stats()
                        upstream_messages = (
                            staged_messages if prefill_receipt is not None else messages
                        )
                        verified_tool_result = _latest_verified_tool_result(messages)
                        final_answer_round = verified_tool_result is not None
                        if final_answer_round:
                            upstream_messages = _add_bounded_final_answer_instruction(
                                upstream_messages,
                                tool_result_sha256=verified_tool_result["sha256"],
                            )
                        upstream_attempts: list[dict[str, Any]] = []
                        upstream_usages: list[dict[str, Any]] = []
                        verified: dict[str, Any] = {}
                        upstream_output = ""
                        max_attempts = 1 if final_answer_round else 2
                        for attempt_index in range(max_attempts):
                            upstream_metadata: dict[str, Any] = {}
                            upstream_output = _forward_upstream(
                                server.upstream_url,
                                request,
                                path=route,
                                timeout_seconds=server.upstream_timeout_seconds,
                                messages_override=upstream_messages,
                                response_metadata=upstream_metadata,
                            )
                            usage = upstream_metadata.get("usage")
                            if isinstance(usage, dict):
                                upstream_usages.append(usage)
                            if final_answer_round:
                                verified = _parse_final_answer_output(
                                    upstream_output,
                                    tool_result_sha256=verified_tool_result["sha256"],
                                )
                            else:
                                verified = execute_model_output(
                                    upstream_output,
                                    server.worker.allowed_root,
                                    request_prompt=_bounded_verification_prompt(messages),
                                )
                            if verified.get("status") == "accepted" and not final_answer_round:
                                try:
                                    upstream_proposal = json.loads(upstream_output)
                                except json.JSONDecodeError:
                                    upstream_proposal = None
                                verified = enforce_ttc(
                                    upstream_proposal,
                                    _bounded_verification_prompt(messages),
                                    verified,
                                    context_pressure=prefill_receipt is not None,
                                )
                            upstream_attempts.append(
                                {
                                    "attempt": attempt_index + 1,
                                    "status": verified.get("status"),
                                    "fallback_reason": verified.get("fallback_reason"),
                                    "usage": usage if isinstance(usage, dict) else {},
                                    "frontier_round": 2 if final_answer_round else 1,
                                    "final_answer": final_answer_round,
                                }
                            )
                            retryable = (
                                not final_answer_round
                                and verified.get("fallback_reason") in _UPSTREAM_RETRYABLE_REASONS
                            )
                            if not retryable or attempt_index == 1:
                                break
                            upstream_messages = add_bounded_repair_instruction(
                                upstream_messages,
                                str(verified.get("fallback_reason")),
                            )
                        accepted_final_answer = (
                            final_answer_round and verified.get("status") == "accepted"
                        )
                        verified.update(
                            {
                                "backend": (
                                    "native-upstream-final-verified"
                                    if accepted_final_answer
                                    else (
                                        "native-upstream-final-rejected"
                                        if final_answer_round
                                        else "native-upstream-verified"
                                    )
                                ),
                                "mechanical_fast_path": False,
                                "raw_model_output": (
                                    verified.get("raw_model_output")
                                    if accepted_final_answer
                                    else upstream_output
                                ),
                                "model_calls": len(upstream_attempts),
                                "repair_pass_count": 0
                                if final_answer_round
                                else max(0, len(upstream_attempts) - 1),
                                "upstream_attempts": upstream_attempts,
                                "frontier_usage": _frontier_usage_receipt(upstream_usages),
                                "frontier_round": 2 if final_answer_round else 1,
                                "final_answer": accepted_final_answer,
                            }
                        )
                        if final_answer_round and verified_tool_result is not None:
                            verified["tool_result_sha256"] = verified_tool_result["sha256"]
                        if prefill_receipt is not None:
                            prompt_tokens = [
                                int(usage["prompt_tokens"])
                                for usage in upstream_usages
                                if isinstance(usage.get("prompt_tokens"), int)
                            ]
                            if prompt_tokens:
                                prefill_receipt["native_backend_prompt_tokens"] = prompt_tokens[-1]
                                prefill_receipt["native_backend_prompt_tokens_total"] = sum(prompt_tokens)
                                prefill_receipt["native_backend_usage_available"] = True
                            else:
                                prefill_receipt["native_backend_usage_available"] = False
                            verified["dynamic_prefill"] = prefill_receipt
                        if verified.get("status") == "abstain":
                            try:
                                verified["advisor_handoff"] = build_advisor_handoff(
                                    messages,
                                    result=verified,
                                    working_messages=staged_messages,
                                    prefill_receipt=prefill_receipt,
                                )
                            except Exception as exc:
                                verified["advisor_handoff"] = {
                                    "schema": "wrench.advisor-handoff.v1",
                                    "handoff_required": True,
                                    "authority": "proposal_only_no_mutation",
                                    "frontier_policy": {
                                        "max_frontier_calls": 2,
                                        "return_each_result_to_wrench_verifier": True,
                                        "preserve_raw_payload_out_of_band": True,
                                    },
                                    "error": type(exc).__name__,
                                }
                        result = verified
            elapsed_ms = (time.perf_counter() - started) * 1000
            if route in {"/v1/chat/completions", "/v1/messages"}:
                tool_call = _build_read_tool_call(request, result)
                if tool_call is not None:
                    result["tool_call"] = tool_call
                if route == "/v1/messages":
                    response = _anthropic_response(
                        result,
                        model_name=model_name,
                        raw_chars=raw_chars,
                        raw_tokens=raw_tokens,
                        elapsed_ms=elapsed_ms,
                    )
                else:
                    response = _completion_response(
                        result,
                        model_name=model_name,
                        raw_chars=raw_chars,
                        raw_tokens=raw_tokens,
                        elapsed_ms=elapsed_ms,
                    )
                trace_event = {
                    "schema": "wrench.runtime-observation.v1",
                    "timestamp": time.time(),
                    "protocol": (
                        "anthropic-messages"
                        if route == "/v1/messages"
                        else "openai-chat-completions"
                    ),
                    "model": model_name,
                    "stream": bool(request.get("stream", False)),
                    "message_roles": [
                        item.get("role") for item in messages if isinstance(item, dict)
                    ],
                    "tool_names": _request_tool_names(request),
                    "raw_input_chars": raw_chars,
                    "raw_input_tokens_estimate": raw_tokens,
                    "raw_payload_sha256": raw_payload_sha256,
                    "status": result.get("status"),
                    "backend": result.get("backend"),
                    "mechanical_fast_path": result.get("mechanical_fast_path", False),
                    "model_calls": result.get("model_calls", 0),
                    "fallback_reason": result.get("fallback_reason"),
                    "frontier_round": result.get("frontier_round"),
                    "final_answer": result.get("final_answer", False),
                    "tool_result_sha256": result.get("tool_result_sha256"),
                    "elapsed_ms": round(elapsed_ms, 3),
                    "context_gate": result.get("context_gate"),
                }
                test_router_status = result.get("test_only_router_status")
                if isinstance(test_router_status, dict):
                    trace_event["test_only_proposal_router"] = test_router_status
                server.record_trace(trace_event)
                if bool(request.get("stream", False)):
                    chunks = (
                        _anthropic_stream_chunks(response)
                        if route == "/v1/messages"
                        else _completion_stream_chunks(response)
                    )
                    self._send_sse(chunks)
                else:
                    self._send_json(200, response)
            else:
                response = _ollama_response(
                    result,
                    model_name=model_name,
                    raw_chars=raw_chars,
                    raw_tokens=raw_tokens,
                    elapsed_ms=elapsed_ms,
                    chat=route == "/api/chat",
                    declared_context_tokens=declared_context_tokens,
                )
                server.record_trace(
                    {
                        "schema": "wrench.runtime-observation.v1",
                        "timestamp": time.time(),
                        "protocol": "ollama",
                        "path": route,
                        "model": model_name,
                        "stream": bool(request.get("stream", False)),
                        "message_roles": [
                            item.get("role") for item in messages if isinstance(item, dict)
                        ],
                        "tool_names": _request_tool_names(request),
                        "raw_input_chars": raw_chars,
                        "raw_input_tokens_estimate": raw_tokens,
                        "raw_payload_sha256": raw_payload_sha256,
                        "status": result.get("status"),
                        "backend": result.get("backend"),
                        "mechanical_fast_path": result.get("mechanical_fast_path", False),
                        "model_calls": result.get("model_calls", 0),
                        "fallback_reason": result.get("fallback_reason"),
                        "frontier_round": result.get("frontier_round"),
                        "final_answer": result.get("final_answer", False),
                        "tool_result_sha256": result.get("tool_result_sha256"),
                        "elapsed_ms": round(elapsed_ms, 3),
                        "context_gate": result.get("context_gate"),
                    }
                )
                if bool(request.get("stream", False)):
                    self._send_ndjson(200, response)
                else:
                    self._send_json(200, response)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send_json(
                400,
                {"error": {"message": str(exc), "type": "invalid_request_error"}},
            )
        except TimeoutError as exc:
            self._send_json(
                504,
                {"error": {"message": str(exc), "type": "upstream_timeout"}},
            )
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            # The client may enforce a shorter deadline than the native
            # backend. The worker request is already bounded by the upstream
            # timeout, and there is no response left to write to this socket.
            return
        except Exception as exc:  # pragma: no cover - defensive serving boundary
            self._send_json(
                500,
                {"error": {"message": str(exc), "type": "server_error"}},
            )

    def log_message(self, format: str, *args: Any) -> None:
        return


class WrenchHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        worker: WrenchWorker,
        *,
        model_name: str,
        max_request_bytes: int,
        upstream_url: str | None = None,
        upstream_timeout_seconds: float = 600.0,
        trace_log: Path | None = None,
        use_mechanical_route: bool = True,
        test_only_proposal_router: ProposalRouter | None = None,
        test_only_proposal_invoker: Callable[[], dict[str, Any]] | None = None,
        test_only_proposal_timeout_seconds: float = 5.0,
        test_only_cancellation_token: CancellationToken | None = None,
    ) -> None:
        test_injection_requested = (
            test_only_proposal_router is not None or test_only_proposal_invoker is not None
        )
        if test_injection_requested:
            try:
                loopback = ipaddress.ip_address(address[0]).is_loopback
            except ValueError:
                loopback = False
            if not loopback:
                raise ValueError("test-only ProposalRouter injection requires an IP loopback bind")
            if upstream_url is not None:
                raise ValueError("test-only ProposalRouter injection cannot use an upstream URL")
            if test_only_proposal_router is None or test_only_proposal_invoker is None:
                raise ValueError("test-only ProposalRouter and invoker must be supplied together")
            if not callable(test_only_proposal_invoker):
                raise ValueError("test-only ProposalRouter invoker must be callable")
            if (
                isinstance(test_only_proposal_timeout_seconds, bool)
                or not isinstance(test_only_proposal_timeout_seconds, (int, float))
                or not math.isfinite(test_only_proposal_timeout_seconds)
                or not 0 < test_only_proposal_timeout_seconds <= 30
            ):
                raise ValueError("test-only ProposalRouter timeout must be in (0, 30] seconds")
        super().__init__(address, WrenchRequestHandler)
        self.worker = worker
        self.model_name = model_name
        self.max_request_bytes = max_request_bytes
        self.upstream_url = upstream_url
        self.upstream_timeout_seconds = upstream_timeout_seconds
        self.use_mechanical_route = use_mechanical_route
        self.test_only_proposal_router = test_only_proposal_router
        self.test_only_proposal_invoker = test_only_proposal_invoker
        self.test_only_proposal_timeout_seconds = float(test_only_proposal_timeout_seconds)
        self.test_only_cancellation_token = (
            test_only_cancellation_token
            if test_only_cancellation_token is not None
            else CancellationToken()
        )
        self._test_only_router_lock = threading.Lock()
        self._test_only_children_lock = threading.Lock()
        self._test_only_children: dict[int, Any] = {}
        self._test_only_shutting_down = False
        self.test_only_child_launches = 0
        self.worker_lock = threading.Lock()
        self.trace_log = trace_log.resolve() if trace_log is not None else None
        self.trace_lock = threading.Lock()

    @property
    def test_only_active_child_pids(self) -> tuple[int, ...]:
        with self._test_only_children_lock:
            return tuple(
                sorted(pid for pid, process in self._test_only_children.items() if process.is_alive())
            )

    def _test_only_child_alive(self, pid: int, process: Any) -> bool:
        with self._test_only_children_lock:
            if self._test_only_children.get(pid) is not process:
                return False
            return process.is_alive()

    def _join_test_only_child(self, pid: int, process: Any, timeout: float) -> bool:
        with self._test_only_children_lock:
            if self._test_only_children.get(pid) is not process:
                return True
            process.join(timeout=timeout)
            return not process.is_alive()

    def _reap_test_only_child(self, pid: int, process: Any) -> bool:
        with self._test_only_children_lock:
            if self._test_only_children.get(pid) is not process:
                return True
            if process.is_alive() and not _terminate_test_router_process(process):
                return False
            process.join(timeout=0)
            if process.is_alive():
                return False
            self._test_only_children.pop(pid, None)
            process.close()
            return True

    def _run_test_only_invoker(self, deadline: float) -> dict[str, Any]:
        assert self.test_only_proposal_invoker is not None
        cancellation = self.test_only_cancellation_token
        context = multiprocessing.get_context("spawn")
        receive, send = context.Pipe(duplex=False)
        process = context.Process(
            target=_test_router_child_entrypoint,
            args=(self.test_only_proposal_invoker, send),
            name="wrench-test-proposal-router",
        )
        pid: int | None = None
        try:
            with self._test_only_children_lock:
                if self._test_only_shutting_down:
                    return {
                        "status": "abstain",
                        "fallback_reason": "server_shutdown",
                    }
                process.start()
                pid = process.pid
                if pid is not None:
                    self._test_only_children[pid] = process
                    self.test_only_child_launches += 1
            send.close()
            if pid is None:
                return {
                    "status": "abstain",
                    "fallback_reason": "router_worker_exited_without_result",
                }
            while True:
                if cancellation.cancelled:
                    outcome = {"status": "abstain", "fallback_reason": "cancelled"}
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    outcome = {"status": "abstain", "fallback_reason": "router_timeout"}
                    break
                if receive.poll(min(0.02, remaining)):
                    try:
                        kind, value = receive.recv()
                    except (EOFError, OSError):
                        outcome = {"status": "abstain", "fallback_reason": "router_worker_exited_without_result"}
                        break
                    if not self._join_test_only_child(
                        pid, process, TEST_ROUTER_TERMINATE_GRACE_SECONDS
                    ):
                        outcome = {"status": "abstain", "fallback_reason": "router_worker_did_not_exit"}
                        break
                    if kind == "error":
                        outcome = {
                            "status": "abstain",
                            "fallback_reason": "router_invocation_error",
                            "detail": str(value),
                        }
                        break
                    if kind != "result":
                        outcome = {"status": "abstain", "fallback_reason": "router_worker_result_invalid"}
                        break
                    try:
                        parsed = json.loads(value)
                    except (TypeError, json.JSONDecodeError):
                        outcome = {"status": "abstain", "fallback_reason": "router_worker_result_invalid"}
                        break
                    invalid_result = (
                        not isinstance(parsed, dict)
                        or parsed.get("status") not in {"accepted", "abstain"}
                        or (
                            parsed.get("status") == "abstain"
                            and (
                                not isinstance(parsed.get("fallback_reason"), str)
                                or not parsed["fallback_reason"].strip()
                            )
                        )
                    )
                    outcome = (
                        {
                            "status": "abstain",
                            "fallback_reason": "router_worker_result_invalid",
                        }
                        if invalid_result
                        else parsed
                    )
                    break
                if not self._test_only_child_alive(pid, process):
                    outcome = {"status": "abstain", "fallback_reason": "router_worker_exited_without_result"}
                    break
        finally:
            receive.close()
            send.close()
            if pid is not None:
                if not self._reap_test_only_child(pid, process):
                    raise RuntimeError("test-only ProposalRouter child survived terminate and kill")
            else:
                process.close()
        return outcome

    def run_test_only_proposal(self) -> dict[str, Any]:
        """Exercise injected deterministic proposals through the real HTTP handler."""

        router = self.test_only_proposal_router
        if router is None:
            raise RuntimeError("test-only ProposalRouter is not configured")
        cancellation = self.test_only_cancellation_token
        # max_attempts is a lifetime call ceiling, not an in-request retry
        # count. Keep time spent waiting for the shared test router bounded by
        # the same deadline as one invocation.
        queue_deadline = time.monotonic() + self.test_only_proposal_timeout_seconds
        while True:
            if cancellation.cancelled:
                return {
                    "status": "abstain",
                    "fallback_reason": "cancelled",
                    "backend": "test-only-proposal-router",
                    "model_calls": 0,
                }
            remaining = queue_deadline - time.monotonic()
            if remaining <= 0:
                return {
                    "status": "abstain",
                    "fallback_reason": "router_queue_timeout",
                    "backend": "test-only-proposal-router",
                    "model_calls": 0,
                }
            if self._test_only_router_lock.acquire(timeout=min(0.02, remaining)):
                break
        try:
            deadline = time.monotonic() + self.test_only_proposal_timeout_seconds
            result = router.run(
                lambda: self._run_test_only_invoker(deadline),
                cancellation=cancellation,
            )
            if not isinstance(result, dict):
                result = {"status": "abstain", "fallback_reason": "router_result_invalid"}
            return {
                **result,
                "backend": "test-only-proposal-router",
                "model_calls": 0,
                "test_only_router_status": router.status(),
            }
        finally:
            self._test_only_router_lock.release()

    def server_close(self) -> None:
        with self._test_only_children_lock:
            self._test_only_shutting_down = True
            for pid, process in list(self._test_only_children.items()):
                if process.is_alive() and not _terminate_test_router_process(process):
                    raise RuntimeError("test-only ProposalRouter child survived server shutdown")
                process.join(timeout=0)
                if process.is_alive():
                    raise RuntimeError("test-only ProposalRouter child survived shutdown join")
                self._test_only_children.pop(pid, None)
                process.close()
        super().server_close()

    def record_trace(self, event: dict[str, Any]) -> None:
        """Append a metadata-only observation without persisting raw prompts."""

        if self.trace_log is None:
            return
        self.trace_log.parent.mkdir(parents=True, exist_ok=True)
        with self.trace_lock:
            with self.trace_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def serve(
    model_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 28900,
    allowed_root: Path = Path("."),
    model_name: str = "wrench-4b",
    load_model: bool = True,
    max_request_bytes: int = 256 * 1024 * 1024,
    upstream_url: str | None = None,
    upstream_timeout_seconds: float = 600.0,
    prefill_cache_bytes: int | None = None,
    trace_log: Path | None = None,
    use_mechanical_route: bool = True,
) -> None:
    worker = WrenchWorker.from_pretrained(
        model_dir,
        allowed_root=allowed_root,
        load_model=load_model,
        prefill_cache_bytes=prefill_cache_bytes,
    )
    server = WrenchHTTPServer(
        (host, port),
        worker,
        model_name=model_name,
        max_request_bytes=max_request_bytes,
        upstream_url=upstream_url,
        upstream_timeout_seconds=upstream_timeout_seconds,
        trace_log=trace_log,
        use_mechanical_route=use_mechanical_route,
    )
    print(json.dumps({"status": "READY", "host": host, "port": server.server_port, "model": model_name}))
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bundled Wrench model endpoint")
    parser.add_argument("--model-dir", type=Path, default=Path("."))
    parser.add_argument("--allowed-root", type=Path, default=Path("."))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=28900)
    parser.add_argument("--model-name", default="wrench-4b")
    parser.add_argument("--mechanical-only", action="store_true")
    parser.add_argument("--max-request-bytes", type=int, default=256 * 1024 * 1024)
    parser.add_argument("--upstream-url", default=None)
    parser.add_argument("--upstream-timeout-seconds", type=float, default=600.0)
    parser.add_argument(
        "--prefill-cache-bytes",
        type=int,
        default=None,
        help="persistent content-addressed native prefill cache; defaults to WRENCH_PREFILL_CACHE_BYTES or 256 MiB",
    )
    parser.add_argument(
        "--trace-log",
        type=Path,
        default=None,
        help="append metadata-only request observations as JSONL",
    )
    parser.add_argument(
        "--disable-mechanical-route",
        action="store_true",
        help="diagnostic only: force requests through the loaded model instead of the embedded toolbelt",
    )
    args = parser.parse_args()
    serve(
        args.model_dir.resolve(),
        host=args.host,
        port=args.port,
        allowed_root=args.allowed_root.resolve(),
        model_name=args.model_name,
        load_model=not args.mechanical_only,
        max_request_bytes=args.max_request_bytes,
        upstream_url=args.upstream_url,
        upstream_timeout_seconds=args.upstream_timeout_seconds,
        prefill_cache_bytes=args.prefill_cache_bytes,
        trace_log=args.trace_log,
        use_mechanical_route=not args.disable_mechanical_route,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
