from pathlib import Path

import scripts.run_authorized_selective_pilot as wrapper
from scripts.run_authorized_selective_pilot import main


def test_wrapper_rejects_current_readiness_receipt_without_starting_runner(monkeypatch, capsys):
    receipt = Path("artifacts/trusted-scenarios/production-readiness-20260910-v5/receipt.json")
    monkeypatch.setattr(
        "sys.argv",
        ["run_authorized_selective_pilot.py", "--trusted-readiness-receipt", str(receipt), "--", "--dry-run"],
    )
    assert main() == 1
    output = capsys.readouterr().out
    assert "readiness rejected" in output.lower()


def test_wrapper_forwards_only_after_readiness_pass(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "sys.argv",
        ["run_authorized_selective_pilot.py", "--trusted-readiness-receipt", "passing.json", "--", "--dry-run"],
    )
    monkeypatch.setattr(wrapper, "verify", lambda path: {"status": "PASS", "receipt": str(path)})
    monkeypatch.setattr(wrapper.subprocess, "run", lambda command, cwd, check: calls.append((command, cwd, check)) or type("R", (), {"returncode": 0})())
    assert main() == 0
    assert len(calls) == 1
    assert calls[0][0][-1] == "--dry-run"
    assert calls[0][1] == wrapper.ROOT
