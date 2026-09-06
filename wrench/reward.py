"""Deterministic reward functions used by GRPO and the evaluator.

Each component is an objective machine check. The reward is the sum of
weighted components, all clipped to [0, 1]. No subjective preference.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Any, Dict

from .fsm import fsm_validate
from .protocol import (
    ROUTER_FALLBACK,
    canonical_json,
    parse_call,
    target_call,
)


@dataclass(frozen=True)
class RewardBreakdown:
    total: float
    schema_valid: float
    ast_exec: float
    param_match: float
    escalation: float
    detail: str = ""


def _is_powershell_balanced(cmd: str) -> bool:
    if not cmd or not cmd.strip():
        return False
    s = cmd.strip()
    if s.endswith(("|", "&&", "||")):
        return False
    in_single = in_double = escape = False
    braces = parens = 0
    for ch in s:
        if escape:
            escape = False
            continue
        if ch == "`":
            escape = True
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "'" and not in_double:
            in_single = not in_single
        elif not in_single and not in_double:
            if ch == "{":
                braces += 1
            elif ch == "}":
                braces -= 1
            elif ch == "(":
                parens += 1
            elif ch == ")":
                parens -= 1
    return not in_single and not in_double and braces == 0 and parens == 0


def _posix_balanced(cmd: str) -> bool:
    if not cmd or not cmd.strip():
        return False
    try:
        shlex.split(cmd)
    except ValueError:
        return False
    return True


def _ast_exec(prompt: str, value: Dict[str, Any]) -> tuple[bool, str]:
    """Cheap AST/structural check that mirrors scripts/verify_execution.py."""
    tool = value.get("tool")
    args = value.get("args", {})
    if tool == "exec_command":
        cmd = args.get("cmd", "")
        if not isinstance(cmd, str) or not cmd.strip():
            return False, "empty command"
        if "powershell" in prompt:
            return _is_powershell_balanced(cmd), "powershell balance"
        if "bash" in prompt:
            return _posix_balanced(cmd), "posix shlex"
        return _is_powershell_balanced(cmd) or _posix_balanced(cmd), "either shell"
    if tool in {"write_stdin", "send_input"}:
        return isinstance(args, dict) and bool(args), f"{tool} args"
    if tool == "create_goal":
        return bool(args.get("objective") or args.get("title") or args.get("goal")), "objective"
    if tool in {"get_goal", "update_goal", "multi_agent_v1", "spawn_agent", "view_image", "apply_patch", "write_file", "edit_file", "read", "tabs"}:
        return isinstance(args, dict), f"{tool} args"
    return isinstance(args, dict), "generic"


def compute_reward(prompt: str, prediction: str, target_record: Dict[str, Any], escalation_threshold: float = 0.85) -> RewardBreakdown:
    """Sum of objective components, all clipped to [0, 1]."""
    schema_valid = ast_exec = param_match = escalation = 0.0
    detail = ""

    if prediction == ROUTER_FALLBACK:
        return RewardBreakdown(0.0, 0.0, 0.0, 0.0, 1.0 if float(target_record.get("complexity", 0.0)) > escalation_threshold else 0.0, "fallback")

    parsed, valid = parse_call(prediction)
    if valid.valid and fsm_validate(prediction):
        schema_valid = 1.0

    if parsed is not None:
        ok, why = _ast_exec(prompt, parsed)
        ast_exec = 1.0 if ok else 0.0
        detail = why

    if parsed is not None:
        target = target_call(target_record)
        try:
            param_match = 1.0 if canonical_json(parsed) == canonical_json(target) else 0.0
        except TypeError:
            param_match = 0.0

    if float(target_record.get("complexity", 0.0)) > escalation_threshold:
        escalation = 0.0 if parsed is not None else 1.0

    total = 0.35 * schema_valid + 0.30 * ast_exec + 0.30 * param_match + 0.05 * escalation
    return RewardBreakdown(round(total, 6), schema_valid, ast_exec, param_match, escalation, detail)


_RISKY_PATTERNS = (
    re.compile(r"\brm\s+-rf\b", re.I),
    re.compile(r"\bdrop\s+table\b", re.I),
)


def is_pseudo_safety_shield(record: Dict[str, Any]) -> bool:
    """Detect the banned keyword-filter pattern from anti-goal #1."""
    for key, value in record.items():
        if not isinstance(value, str):
            continue
        for pattern in _RISKY_PATTERNS:
            if pattern.search(value):
                return True
    return False
