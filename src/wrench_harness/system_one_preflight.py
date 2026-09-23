"""Cheap, conservative abstention veto for explicit Wrench boundary breaks.

This never approves a request. Ambiguous requests go to the Qwen binary gate.
It does not parse code or grant execution authority.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from .core import ALLOWED_HEALTH_HOSTS, ALLOWED_HEALTH_PATHS


_BYTES = re.compile(r"\b(?P<value>\d[\d,]*)\s*bytes?\b", re.IGNORECASE)
_LINES = re.compile(r"\blines?\s+(?P<start>\d+)\s*(?:through|to|-)\s*(?P<end>\d+)\b", re.IGNORECASE)
_LINE_TO_LINE = re.compile(r"\bline\s+(?P<start>\d+)\s+to\s+line\s+(?P<end>\d+)\b", re.IGNORECASE)
_MATCHES = re.compile(r"\b(?:at\s+most|maximum|limit|cap)\s+(?P<value>\d[\d,]*)\s+matches\b", re.IGNORECASE)
_MATCHES_MAX = re.compile(r"\b(?:with|limit|cap)\s+(?P<value>\d[\d,]*)\s+matches\s+max\b", re.IGNORECASE)
_ZERO_MATCHES = re.compile(r"\b(?:at\s+most|maximum|limit|cap|capped\s+at)\s+zero\s+matches\b", re.IGNORECASE)
_SECONDS = re.compile(r"\b(?P<value>\d+(?:\.\d+)?)\s*(?:-|\s)\s*seconds?\b", re.IGNORECASE)
_ZH_SECONDS = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*秒")
_ZH_BYTES = re.compile(r"(?P<value>\d[\d,]*)\s*字节")
_URL = re.compile(r"https?://[^\s'\"<>，。；、）】]+", re.IGNORECASE)
_UNSAFE_FIRST = re.compile(
    r"^\s*(?:please\s+|can\s+you\s+)?(?:execute|stage|commit|push|reset|delete|edit|modify|write|save|deploy|debug|implement|fix|discard|rebase|cherry-pick|install|launch)\b",
    re.IGNORECASE)
_RUN_COMMAND = re.compile(r"\brun\s+(?:pytest|npm|python|bash|a\s+shell|the\s+script|this\s+script|tests?\b)", re.IGNORECASE)
_FOLLOWUP = re.compile(
    r"\b(?:then|next|also|finally|afterwards?|after that|after reading|once done|when finished|and)\b[\s,]+(?:run|execute|stage|commit|push|save|apply|write|edit|modify|update|delete|reset|remove|send|upload|deploy|fix|implement|inspect|diagnose|redesign|refactor|optimize|repair)\b",
    re.IGNORECASE)
_GIT_MUTATION = re.compile(
    r"\b(?:git\s+clean|cherry-pick|rebase|amend\s+(?:the\s+)?commit|"
    r"(?:create|check\s+out)\s+(?:and\s+check\s+out\s+)?(?:a\s+)?branch)\b",
    re.IGNORECASE)
_MISSING_CONTEXT = re.compile(
    r"\b(?:the other file we discussed|the file I pointed to before|previous conversation|"
    r"our earlier instructions|the same change as last time|the patch we agreed on before|"
    r"the other repository we discussed|the file I meant when I mentioned|"
    r"that exact string from earlier)\b",
    re.IGNORECASE)
_OUTSIDE_ABSOLUTE = re.compile(r"\b(?:read|inspect|show|open|search)\s+(?:/|[A-Za-z]:[/\\]|~[/\\])", re.IGNORECASE)
_SECRET_FILE = re.compile(r"(?:\.env(?:\.[\w-]+)?|\.ssh[/\\]|\.aws[/\\]|private[_-]?key)", re.IGNORECASE)
_SECRET_REQUEST = re.compile(
    r"\b(?:api\s+key\s+in\s+memory|production\s+(?:database\s+)?password|"
    r"cloud\s+service\s+credential|private\s+access\s+token|"
    r"signing\s+key|secret\s+value|live\s+credential)\b",
    re.IGNORECASE)


def explicit_abstain_reason(prompt: str) -> str | None:
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    lowered = prompt.casefold()
    action_text = re.sub(r"(?<!\w)'[^']*'|\"[^\"]*\"|`[^`]*`", " ", prompt)
    for match in _BYTES.finditer(prompt):
        value = int(match["value"].replace(",", ""))
        if not 1 <= value <= 262144:
            return "explicit_invalid_byte_limit"
    for match in list(_LINES.finditer(prompt)) + list(_LINE_TO_LINE.finditer(prompt)):
        start, end = int(match["start"]), int(match["end"])
        if start < 1 or end < start or end - start + 1 > 500:
            return "explicit_invalid_line_range"
    for match in list(_MATCHES.finditer(prompt)) + list(_MATCHES_MAX.finditer(prompt)):
        if not 1 <= int(match["value"].replace(",", "")) <= 200:
            return "explicit_invalid_match_limit"
    if _ZERO_MATCHES.search(prompt):
        return "explicit_invalid_match_limit"
    if re.search(r"字节.{0,8}(?:负一|负数)", prompt):
        return "explicit_invalid_byte_limit"
    if "../" in prompt or "..\\" in prompt or _OUTSIDE_ABSOLUTE.search(prompt):
        return "explicit_outside_root"
    if _SECRET_FILE.search(prompt) and re.search(r"\b(?:read|open|print|retrieve|show|get)\b", lowered):
        return "explicit_secret_path"
    if _SECRET_REQUEST.search(action_text) and re.search(
            r"\b(?:read|open|print|retrieve|show|get|find|disclose|copy|reveal|return)\b",
            action_text, re.IGNORECASE):
        return "explicit_secret_request"
    if (_UNSAFE_FIRST.search(action_text) or _RUN_COMMAND.search(action_text)
            or _FOLLOWUP.search(action_text) or _GIT_MUTATION.search(action_text)):
        return "explicit_unsupported_action"
    if _MISSING_CONTEXT.search(action_text):
        return "explicit_unresolved_context"
    for match in _URL.finditer(action_text):
        url = match.group().rstrip(".,);]")
        if not re.search(r"\b(?:fetch|get|call|request|probe|check|download|upload|send|post|read|inspect|use)\b|请求|获取|访问|读取|检查", action_text, re.IGNORECASE):
            continue
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
        except ValueError:
            return "explicit_health_endpoint_not_allowlisted"
        if (parsed.scheme != "http" or hostname not in ALLOWED_HEALTH_HOSTS
                or parsed.path not in ALLOWED_HEALTH_PATHS or parsed.query or parsed.fragment):
            return "explicit_health_endpoint_not_allowlisted"
        if any(not 0 < float(value["value"]) <= 5
               for pattern in (_SECONDS, _ZH_SECONDS) for value in pattern.finditer(prompt)):
            return "explicit_invalid_health_timeout"
        if any(not 1 <= int(value["value"].replace(",", "")) <= 64 * 1024
               for pattern in (_BYTES, _ZH_BYTES) for value in pattern.finditer(prompt)):
            return "explicit_invalid_health_byte_limit"
    return None


class WrenchBinaryRouter:
    """Preserve Qwen's binary output contract with a fast abstain-only veto."""

    def __init__(self, qwen_gate):
        self.qwen_gate = qwen_gate

    def check_messages(self, messages):
        if (isinstance(messages, list) and len(messages) == 1
                and isinstance(messages[0], dict) and messages[0].get("role") == "user"
                and isinstance(messages[0].get("content"), str)):
            reason = explicit_abstain_reason(messages[0]["content"])
            if reason is not None:
                return {"schema": "wrench.qwen-binary-decision.v1", "decision": "abstain",
                        "reason": reason, "probabilities": None,
                        "threshold": self.qwen_gate.threshold,
                        "head_sha256": self.qwen_gate.artifact_sha256,
                        "authority": "abstain_only", "model_forwards": 0,
                        "generated_tokens": 0}
        return self.qwen_gate.check_messages(messages)
