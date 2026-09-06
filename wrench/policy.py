"""Local policy interface and transparent production-data baseline."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .protocol import ROUTER_FALLBACK, canonical_json


@dataclass(frozen=True)
class Prediction:
    text: str
    confidence: float
    route: str
    reason: str = ""


_PROMPT_PREFIXES = (
    "Execute shell command (powershell on Windows): ",
    "Execute shell command (bash on Linux/macOS): ",
)


class ProductionDataBaseline:
    """Deterministic baseline that reconstructs calls from canonical prompts.

    Exists so the protocol, routing, FSM, and GRPO reward paths can be
    exercised before model weights are available. Not a prompt lookup
    table: each prompt family uses a small regex specific to its shape.
    """

    def predict(self, prompt: str) -> Prediction:
        if not isinstance(prompt, str) or not prompt.strip():
            return Prediction(ROUTER_FALLBACK, 0.0, "fallback", "empty prompt")
        for prefix in _PROMPT_PREFIXES:
            if prompt.startswith(prefix):
                command = prompt[len(prefix):]
                if not command.strip():
                    return Prediction(ROUTER_FALLBACK, 0.0, "fallback", "empty command")
                return self._call("exec_command", {"cmd": command}, 0.99)

        match = re.fullmatch(r"Send input to active process: ?(.*)", prompt, re.S)
        if match:
            return self._call("write_stdin", {"text": match.group(1)}, 0.90)
        match = re.fullmatch(r"Get status and details for goal ?(.*)", prompt, re.S)
        if match:
            goal_id = match.group(1).strip()
            return self._call("get_goal", ({"goal_id": goal_id} if goal_id else {}), 0.90)
        match = re.fullmatch(r"Create a new goal with objective: ?(.*)", prompt, re.S)
        if match:
            return self._call("create_goal", {"objective": match.group(1)}, 0.90)
        match = re.fullmatch(r"Inspect and view image at: ?(.*)", prompt, re.S)
        if match:
            return self._call("view_image", {"path": match.group(1)}, 0.90)
        return Prediction(ROUTER_FALLBACK, 0.0, "fallback", "prompt outside deterministic envelope")

    @staticmethod
    def _call(tool: str, args: dict[str, Any], confidence: float) -> Prediction:
        return Prediction(json.dumps({"tool": tool, "args": args}, ensure_ascii=False), confidence, "local")


def load_json_prediction(text: str) -> Prediction:
    """Wrap a model's raw text with the mandatory confidence route gate."""
    if text == ROUTER_FALLBACK:
        return Prediction(text, 0.0, "fallback", "model requested fallback")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return Prediction(ROUTER_FALLBACK, 0.0, "fallback", "invalid model JSON")
    if set(value) != {"tool", "args"} or not isinstance(value.get("tool"), str) or not isinstance(value.get("args"), dict):
        return Prediction(ROUTER_FALLBACK, 0.0, "fallback", "invalid tool-call schema")
    return Prediction(canonical_json(value), 1.0, "local")
