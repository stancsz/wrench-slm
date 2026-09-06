"""Policy and routing tests."""
from __future__ import annotations

import json

from wrench import (
    ProductionDataBaseline,
    ROUTER_FALLBACK,
    load_json_prediction,
)
from wrench.policy import Prediction


def test_baseline_emits_exec_command_for_windows_prompt():
    baseline = ProductionDataBaseline()
    prediction = baseline.predict("Execute shell command (powershell on Windows): Get-ChildItem")
    parsed = json.loads(prediction.text)
    assert parsed == {"tool": "exec_command", "args": {"cmd": "Get-ChildItem"}}
    assert prediction.route == "local"


def test_baseline_emits_exec_command_for_posix_prompt():
    baseline = ProductionDataBaseline()
    prediction = baseline.predict("Execute shell command (bash on Linux/macOS): ls -la")
    parsed = json.loads(prediction.text)
    assert parsed == {"tool": "exec_command", "args": {"cmd": "ls -la"}}


def test_baseline_returns_fallback_outside_envelope():
    baseline = ProductionDataBaseline()
    prediction = baseline.predict("Solve a math proof please")
    assert prediction.text == ROUTER_FALLBACK
    assert prediction.route == "fallback"


def test_load_json_prediction_promotes_valid():
    prediction = load_json_prediction(json.dumps({"tool": "exec_command", "args": {"cmd": "ls"}}))
    assert prediction.route == "local"


def test_load_json_prediction_demotes_invalid():
    prediction = load_json_prediction("not-json")
    assert prediction.text == ROUTER_FALLBACK


def test_baseline_handles_empty_prompt():
    prediction = ProductionDataBaseline().predict("")
    assert prediction.text == ROUTER_FALLBACK


def test_baseline_rejects_empty_command_after_prefix():
    prediction = ProductionDataBaseline().predict("Execute shell command (powershell on Windows):    ")
    assert prediction.text == ROUTER_FALLBACK


def test_prediction_dataclass_round_trip():
    prediction = Prediction("text", 0.5, "local", "ok")
    assert prediction.route == "local" and prediction.confidence == 0.5
