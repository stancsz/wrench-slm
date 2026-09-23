"""Diagnose local OpenCode stdout versus persisted answers without provider calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading

try:
    from .probe_paired_real_client_canary import _baseline_server, BASELINE_TEXT
except ImportError:
    from probe_paired_real_client_canary import _baseline_server, BASELINE_TEXT


def run(output: Path, executable: str | None = None) -> dict:
    executable = executable or shutil.which("opencode.cmd") or shutil.which("opencode")
    if not executable:
        raise RuntimeError("opencode unavailable")
    executable = str(Path(shutil.which(executable) or executable).resolve())
    version = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    server, calls = _baseline_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    output.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="wrench-opencode-output-") as temp:
            root = Path(temp)
            env = dict(os.environ)
            env["HOME"] = env["USERPROFILE"] = str(root / "home")
            for key, name in (("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache"), ("XDG_DATA_HOME", "data"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
                folder = root / name
                folder.mkdir()
                env[key] = str(folder)
            config = {
                "$schema": "https://opencode.ai/config.json",
                "share": "disabled", "autoupdate": False,
                "enabled_providers": ["baseline"],
                "provider": {"baseline": {
                    "npm": "@ai-sdk/openai-compatible", "name": "Local diagnostic",
                    "options": {"baseURL": f"http://127.0.0.1:{server.server_port}/v1", "apiKey": "local-test-only"},
                    "models": {"baseline-local": {"name": "Local diagnostic", "limit": {"context": 64000, "output": 256}}},
                }},
                "model": "baseline/baseline-local",
            }
            (root / "opencode.json").write_text(json.dumps(config), encoding="utf-8")
            cmd = [executable, "run", "--pure", "--print-logs", "--format", "json", "--title", "Local output diagnostic", "-m", "baseline/baseline-local", "Report the first heading."]
            process = subprocess.run(cmd, cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40)
            (output / "stdout.jsonl").write_text(process.stdout, encoding="utf-8")
            (output / "stderr.log").write_text(process.stderr, encoding="utf-8")
            events = []
            for line in process.stdout.splitlines():
                try:
                    events.append(json.loads(line))
                except ValueError:
                    pass
            session_id = next((e.get("sessionID") for e in events if e.get("sessionID")), None)
            if not session_id:
                found = re.search(r"session[.]id=(ses_[A-Za-z0-9]+)", process.stderr)
                session_id = found.group(1) if found else None
            assistant_parts = []
            export_exit = None
            if session_id:
                exported = subprocess.run([executable, "export", session_id], cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
                export_exit = exported.returncode
                data = json.loads(exported.stdout)
                for message in data.get("messages", []):
                    if message.get("info", {}).get("role") == "assistant":
                        assistant_parts.extend(p for p in message.get("parts", []) if p.get("type") in {"text", "step-finish"})
            result = {
                "schema": "wrench.opencode-output-diagnostic.v1",
                "executable": executable,
                "executable_sha256": hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
                "version": version,
                "client_exit_code": process.returncode,
                "event_types": [event.get("type") for event in events],
                "expected_answer": BASELINE_TEXT,
                "stdout_contains_answer": BASELINE_TEXT in process.stdout,
                "session_id": session_id,
                "export_exit_code": export_exit,
                "persisted_assistant_parts": assistant_parts,
                "persisted_answer_present": any(BASELINE_TEXT in p.get("text", "") for p in assistant_parts),
                "local_endpoint_calls": len(calls),
                "paid_provider_called": False,
                "config": config,
            }
            (output / "receipt.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", help="Isolated OpenCode executable; does not change the global install")
    args = parser.parse_args()
    print(json.dumps(run(args.output.resolve(), args.executable), indent=2))
