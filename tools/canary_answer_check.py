"""Conservative output oracle for the bounded first-heading canary.

This checks returned answer content, never a tool-observed flag or an exit
code alone. It is not a general semantic judge or a production-value gate.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def check_answer(
    output: str, expected: str, *, exit_code: int | None, timed_out: bool = False
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "oracle": "bounded-first-heading-output-v1",
        "correct": False,
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "expected_observation": expected,
    }
    if timed_out or exit_code != 0:
        return {**result, "reason": "client_did_not_complete"}
    if not expected.strip():
        return {**result, "reason": "empty_expected_observation"}

    # OpenCode JSON output contains tool events and echoed inputs. Only text
    # answer events contribute, never an expected string inside a tool event.
    lines = output.splitlines()
    events = []
    for line in lines:
        try:
            value = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict) and isinstance(value.get("type"), str):
            events.append(value)
    if events:
        texts = [
            event["part"]["text"]
            for event in events
            if event.get("type") == "text"
            and isinstance(event.get("part"), dict)
            and isinstance(event["part"].get("text"), str)
        ]
        # Judge the final text event; an earlier correct fragment cannot mask
        # a wrong final answer.
        answer = texts[-1] if texts else ""
    else:
        answer = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output).strip()

    answer = answer.replace("\r\n", "\n").replace("\r", "\n")
    wanted = expected.strip()
    candidates = [line.strip() for line in answer.splitlines() if line.strip()]
    direct_forms = {wanted, f"The first heading is {wanted}.", f"The first heading is {wanted}"}
    # The deterministic worker returns an explicit final settlement followed
    # by a bounded one-line read. Treat that displayed first line as the answer.
    marker = "Wrench completed the requested read-only tool call. The client tool result is authoritative."
    if marker in answer and "Tool result:" in answer:
        observation = answer.rsplit("Tool result:", 1)[1]
        first_lines = re.findall(r"(?m)^1(?:: |\t)([^\r\n]+)$", observation)
        matched = first_lines == [wanted]
    else:
        matched = len(candidates) == 1 and candidates[0] in direct_forms
    return {
        **result,
        "correct": matched,
        "reason": "expected_answer_observed" if matched else "expected_answer_missing_or_mismatched",
    }


def audit_saved_outputs(directory: Path, expected: str) -> dict[str, Any]:
    """Recheck saved client outputs without launching a client or provider."""
    receipt_path = directory / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    checks = {}
    for client, filename in (("opencode", "opencode.stdout.txt"), ("deepseek_harness", "dsh.stdout.txt"), ("claude_code", "claude.stdout.txt")):
        path = directory / filename
        raw = path.read_bytes() if path.is_file() else b""
        checks[client] = {
            **check_answer(raw.decode("utf-8-sig"), expected, exit_code=receipt.get("clients", {}).get(client, {}).get("exit_code")),
            "source_file": str(path.resolve()),
            "source_file_sha256": hashlib.sha256(raw).hexdigest() if path.is_file() else None,
        }
    return {
        "schema": "wrench.saved-client-answer-audit.v1",
        "status": "PASS_SAVED_CLIENT_ANSWER_CHECK" if all(check["correct"] for check in checks.values()) else "FAIL_SAVED_CLIENT_ANSWER_CHECK",
        "source_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "source_smoke_status": receipt.get("status"),
        "clients": checks,
        "provider_called": False,
        "production_enablement": False,
        "scope": "Saved first-heading answers only; no general semantic or productive-value claim",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = audit_saved_outputs(args.receipt_dir, args.expected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    raise SystemExit(0 if audit["status"] == "PASS_SAVED_CLIENT_ANSWER_CHECK" else 1)
