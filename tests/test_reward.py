"""Reward function tests."""
from __future__ import annotations

import pytest

from wrench import compute_reward, is_pseudo_safety_shield


def _call_text(tool, args):
    import json
    return json.dumps({"tool": tool, "args": args}, ensure_ascii=False)


def test_reward_full_match_scores_one():
    record = {"tool": "exec_command", "args": {"cmd": "ls"}, "complexity": 0.1}
    breakdown = compute_reward("Execute shell command (bash on Linux/macOS): ls", _call_text("exec_command", {"cmd": "ls"}), record)
    # 0.35 schema + 0.30 ast + 0.30 params + 0.05 escalation == 0.95
    assert breakdown.total == pytest.approx(0.95)


def test_reward_rejects_invalid_json():
    record = {"tool": "exec_command", "args": {"cmd": "ls"}, "complexity": 0.1}
    breakdown = compute_reward("Execute shell command (bash on Linux/macOS): ls", "not-json", record)
    assert breakdown.total == 0.0


def test_reward_escalation_penalises_local_answer_for_complex():
    record = {"tool": "exec_command", "args": {"cmd": "ls"}, "complexity": 1.0}
    breakdown = compute_reward("Execute shell command (bash on Linux/macOS): ls", _call_text("exec_command", {"cmd": "ls"}), record)
    assert breakdown.escalation == 0.0


def test_reward_escalation_rewards_proper_fallback_for_complex():
    record = {"tool": "exec_command", "args": {"cmd": "ls"}, "complexity": 1.0}
    breakdown = compute_reward("Execute shell command (bash on Linux/macOS): ls", "ROUTER_FALLBACK", record)
    assert breakdown.escalation == 1.0


def test_pseudo_safety_shield_detection_positive():
    assert is_pseudo_safety_shield({"label": "rm -rf /", "comment": "drop table x"})


def test_pseudo_safety_shield_detection_negative():
    assert not is_pseudo_safety_shield({"label": "ls -la"})
