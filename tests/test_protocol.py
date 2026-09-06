"""Protocol and FSM unit tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wrench import (
    REQUIRED_KEYS,
    ROUTER_FALLBACK,
    canonical_json,
    exact_match,
    fsm_validate,
    iter_jsonl,
    parse_call,
    target_call,
    validate_call,
)
from wrench.fsm import JsonToolCallFSM


def _call_text(tool, args):
    return json.dumps({"tool": tool, "args": args}, ensure_ascii=False)


def test_required_keys_locked():
    assert REQUIRED_KEYS == {"tool", "args"}


def test_validate_call_accepts_valid():
    ok = validate_call({"tool": "exec_command", "args": {"cmd": "ls"}})
    assert ok.valid
    assert ok.error == ""


def test_validate_call_rejects_extra_keys():
    ok = validate_call({"tool": "exec_command", "args": {}, "extra": 1})
    assert not ok.valid


def test_parse_call_rejects_markdown_fences():
    text = "```json\n" + _call_text("exec_command", {"cmd": "ls"}) + "\n```"
    parsed, ok = parse_call(text)
    assert parsed is None
    assert not ok.valid


def test_parse_call_rejects_empty():
    parsed, ok = parse_call("")
    assert parsed is None and not ok.valid


def test_canonical_json_is_key_order_invariant():
    left = canonical_json({"tool": "exec_command", "args": {"a": 1, "b": 2}})
    right = canonical_json({"args": {"b": 2, "a": 1}, "tool": "exec_command"})
    assert left == right


def test_exact_match_does_not_depend_on_dict_order():
    pred = {"tool": "exec_command", "args": {"cmd": "ls"}}
    target = {"tool": "exec_command", "args": {"cmd": "ls"}}
    assert exact_match(pred, target)


def test_fsm_walks_a_complete_call():
    assert fsm_validate(_call_text("exec_command", {"cmd": "ls"}))


def test_fsm_rejects_unbalanced_json():
    assert not fsm_validate('{"tool": "exec_command", "args": {"cmd": "ls"}')


def test_fsm_rejects_suffix_after_complete_call():
    head = _call_text("exec_command", {"cmd": "ls"})
    fsm = JsonToolCallFSM()
    assert fsm.consume(head)
    assert fsm.complete
    assert fsm.constrained_prefix(head + "x") == head


def test_target_call_uses_args_default():
    assert target_call({"tool": "exec_command"}) == {"tool": "exec_command", "args": {}}


def test_iter_jsonl_handles_blank_lines(tmp_path: Path):
    path = tmp_path / "x.jsonl"
    path.write_text('{"tool":"exec_command","args":{"cmd":"ls"}}\n\n', encoding="utf-8")
    assert len(list(iter_jsonl(str(path)))) == 1


def test_router_fallback_is_a_distinct_token():
    assert ROUTER_FALLBACK != "exec_command"
    assert isinstance(ROUTER_FALLBACK, str)


@pytest.mark.parametrize("prompt", [
    "Execute shell command (powershell on Windows): Get-ChildItem",
    "Execute shell command (bash on Linux/macOS): ls -la",
])
def test_dataset_prompt_prefixes_in_canonical_data(prompt):
    from wrench.dataset import build_training_prompt
    rendered = build_training_prompt({"prompt": prompt})
    assert rendered.startswith("You are Wrench, a local edge SLM")
    assert prompt in rendered
