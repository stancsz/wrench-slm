import json

import pytest

from tools.canary_answer_check import audit_saved_outputs, check_answer
from tools import probe_paired_real_client_canary as canary


@pytest.mark.parametrize("text", [
    "",
    "Read README.md [limit=1]",
    "The first heading is NOT # Wrench SLM.",
    "The first heading is # Wrong.",
    json.dumps({"type": "tool_use", "part": {"text": "# Wrench SLM"}}),
    json.dumps({"type": "step_start", "expected": "# Wrench SLM"}),
])
def test_read_flags_echoes_and_wrong_answers_do_not_pass(text):
    assert not check_answer(text, "# Wrench SLM", exit_code=0)["correct"]


@pytest.mark.parametrize("text", [
    "# Wrench SLM",
    "The first heading is # Wrench SLM.",
    json.dumps({"type": "text", "part": {"text": "The first heading is # Wrench SLM."}}),
    "Wrench completed the requested read-only tool call. The client tool result is authoritative.\n\nTool result:\n<content>\n1: # Wrench SLM\n</content>",
    "Wrench completed the requested read-only tool call. The client tool result is authoritative.\r\n\r\nTool result:\r\n<content>\r\n1: # Wrench SLM\r\n</content>",
])
def test_observed_first_heading_answers_pass(text):
    assert check_answer(text, "# Wrench SLM", exit_code=0)["correct"]


def test_wrong_final_text_overrides_earlier_correct_text():
    output = "\n".join(json.dumps({"type": "text", "part": {"text": text}}) for text in ("# Wrench SLM", "# Wrong"))
    assert not check_answer(output, "# Wrench SLM", exit_code=0)["correct"]
    assert not check_answer("# Wrench SLM", "# Wrench SLM", exit_code=1)["correct"]
    assert not check_answer("# Wrench SLM", "# Wrench SLM", exit_code=0, timed_out=True)["correct"]


@pytest.mark.parametrize("wrong_client", ["opencode", "deepseek_harness", "claude_code"])
def test_hybrid_smoke_pass_cannot_mask_any_client_without_answer(tmp_path, monkeypatch, wrong_client):
    clients = {name: {"exit_code": 0, "structured_read_observed": True} for name in ("opencode", "deepseek_harness", "claude_code")}
    (tmp_path / "receipt.json").write_text(json.dumps({"status": "PASSED", "clients": clients}))
    output_by_client = {
        "opencode": "The first heading is # Wrench SLM.",
        "deepseek_harness": "The first heading is # Wrench SLM.",
        "claude_code": "The first heading is # Wrench SLM.",
    }
    output_by_client[wrong_client] = "The first heading is # Incorrect."
    for client, output in output_by_client.items():
        filename = {
            "opencode": "opencode.stdout.txt",
            "deepseek_harness": "dsh.stdout.txt",
            "claude_code": "claude.stdout.txt",
        }[client]
        (tmp_path / filename).write_text(output)
    monkeypatch.setattr(canary.shutil, "which", lambda _: "powershell.exe")
    monkeypatch.setattr(canary, "_run_bounded_subprocess", lambda *args, **kwargs: {
        "exit_code": 0, "timed_out": False, "timeout_seconds": 180,
        "elapsed_ms": 2, "stdout": "", "stderr": "",
    })
    result = canary._run_hybrid(tmp_path, tmp_path, 29120, prompt=canary.PROMPT, expected=canary.EXPECTED)
    assert not result["correct"]
    assert not result["client_answers"][wrong_client]["correct"]
    assert all(
        result["client_answers"][client]["correct"]
        for client in output_by_client
        if client != wrong_client
    )
    assert result["accounting"]["corrections"] is None
    audit = audit_saved_outputs(tmp_path, canary.EXPECTED)
    assert audit["status"] == "FAIL_SAVED_CLIENT_ANSWER_CHECK"
    assert audit["source_smoke_status"] == "PASSED"
    assert not audit["provider_called"]


def test_explicit_opencode_binary_is_used_by_both_arms(tmp_path, monkeypatch):
    commands = []
    executable = str(tmp_path / "pinned-opencode.exe")
    monkeypatch.setattr(canary.shutil, "which", lambda name: name)

    def capture(command, **kwargs):
        commands.append(command)
        return {"exit_code": 0, "timed_out": False, "timeout_seconds": 120,
                "elapsed_ms": 1, "stdout": "The first heading is # Wrench SLM.", "stderr": ""}

    monkeypatch.setattr(canary, "_run_bounded_subprocess", capture)
    direct = canary._run_direct_clients(
        tmp_path / "baseline", base_url="http://127.0.0.1:1/v1",
        model="local", api_key="test-only", prompt=canary.PROMPT,
        expected=canary.EXPECTED, opencode_executable=executable,
    )
    assert commands[0][0] == executable
    assert direct["opencode"]["executable"] == executable
    canary._run_hybrid(tmp_path, tmp_path, 29120, prompt=canary.PROMPT,
                       expected=canary.EXPECTED, opencode_executable=executable)
    assert commands[-1][-2:] == ["-OpenCodeExecutable", executable]
