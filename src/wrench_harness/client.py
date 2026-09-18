"""Bounded client for a local Qwen-compatible proposal server."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .core import execute_model_output


ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_RESPONSE_BYTES = 512 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _abstain(reason: str, detail: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "abstain", "fallback_reason": reason}
    if detail:
        result["detail"] = detail
    return result


def execute_local_qwen(
    endpoint: str,
    model: str,
    messages: list[dict[str, str]],
    allowed_root: str,
    *,
    max_tokens: int = 256,
    timeout_seconds: float = 10,
) -> dict[str, Any]:
    """Call one local proposal endpoint and pass its text through the verifier."""

    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_HOSTS or parsed.path != "/v1/chat/completions" or parsed.query or parsed.fragment:
        return _abstain("qwen_endpoint_not_allowlisted")
    if not isinstance(model, str) or not model or not isinstance(messages, list) or not messages:
        return _abstain("qwen_request_invalid")
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or not 1 <= max_tokens <= 512:
        return _abstain("qwen_token_limit_invalid")
    if not isinstance(timeout_seconds, (int, float)) or not 0 < timeout_seconds <= 10:
        return _abstain("qwen_timeout_invalid")
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        }
    ).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=float(timeout_seconds)) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                return _abstain("qwen_response_size_limit")
            payload = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return _abstain("qwen_http_error", str(exc.code))
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        return _abstain("qwen_transport_error", type(exc).__name__)
    if not isinstance(payload, dict):
        return _abstain("qwen_response_invalid")
    response_model = payload.get("model")
    choices = payload.get("choices")
    if response_model != model or not isinstance(choices, list) or not choices:
        return _abstain("qwen_response_identity_invalid")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        return _abstain("qwen_response_content_invalid")
    result = execute_model_output(content, allowed_root)
    result["model"] = response_model
    if isinstance(payload.get("usage"), dict):
        result["usage"] = payload["usage"]
    return result
