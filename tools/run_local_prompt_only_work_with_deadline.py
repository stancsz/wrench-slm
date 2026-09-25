"""Launch the prompt-only screen in an isolated process with a hard deadline."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(r"C:\wrench-slm-data")
RUNTIME_PYTHON = DATA_ROOT / "envs" / "wrench-local-synthetic-cp313" / "Scripts" / "python.exe"
RUNNER = ROOT / "tools" / "measure_local_prompt_only_work.py"
LOG_ROOT = DATA_ROOT / "logs" / "wrench-local-acceptability"
HARD_TIMEOUT_SECONDS = 25 * 60
JOB_ID = "W2-LOCAL-PROMPTONLY-SCREEN-20260925-01"


def _inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(root.resolve())
    return resolved


def _assert_storage_admitted() -> None:
    checker = ROOT / "tools" / "check_wrench_storage_budget.py"
    done = subprocess.run([sys.executable, str(checker), "status"], cwd=ROOT,
                          capture_output=True, text=True, timeout=60, check=True)
    budget = json.loads(done.stdout)
    if (budget.get("status") != "WITHIN_LIMIT" or budget.get("errors") or
            JOB_ID not in budget.get("reservations", []) or
            budget.get("projected_bytes", budget["limit_bytes"]) >= budget["limit_bytes"]):
        raise RuntimeError("storage budget or job reservation is no longer admitted")


def _mark_hard_timeout(output: Path) -> bool:
    if not output.is_file():
        return False
    try:
        _assert_storage_admitted()
        report = json.loads(output.read_text(encoding="utf-8"))
        report["run_status"] = "hard_timeout"
        report["status"] = "INCOMPLETE_HARD_TIMEOUT"
        report["supervisor_timeout_seconds"] = HARD_TIMEOUT_SECONDS
        for row in report.get("results", []):
            if row.get("status") == "running":
                row["status"] = "failed"
                row["failure"] = "outer_supervisor_hard_timeout"
        temporary = output.with_name(output.name + f".{uuid.uuid4().hex}.timeout.tmp")
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
        return True
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = _inside(args.output, DATA_ROOT / "artifacts" / "wrench-local-acceptability")
    if output.exists():
        raise FileExistsError("receipt already exists")
    _assert_storage_admitted()
    if not RUNTIME_PYTHON.is_file() or not RUNNER.is_file():
        raise FileNotFoundError("pinned runtime or measurement runner is missing")
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    stdout_path = LOG_ROOT / "prompt-only-work-01.stdout.log"
    stderr_path = LOG_ROOT / "prompt-only-work-01.stderr.log"
    if stdout_path.exists() or stderr_path.exists():
        raise FileExistsError("measurement log path already exists")
    child_env = os.environ.copy()
    child_env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "WRENCH_SCREEN_SUPERVISED": "1",
        "HF_HOME": str(DATA_ROOT / "cache" / "huggingface"),
        "TORCH_HOME": str(DATA_ROOT / "cache" / "torch"),
    })
    command = [
        str(RUNTIME_PYTHON), "-B", str(RUNNER),
        "--model-path", str(args.model_path), "--output", str(output),
    ]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        child = subprocess.Popen(command, cwd=ROOT, env=child_env, stdout=stdout,
                                 stderr=stderr, shell=False, creationflags=creationflags)
        try:
            code = child.wait(timeout=HARD_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            receipt_marked = _mark_hard_timeout(output)
            print(json.dumps({"status": "HARD_TIMEOUT", "timeout_seconds": HARD_TIMEOUT_SECONDS,
                              "receipt": str(output), "receipt_marked": receipt_marked,
                              "stdout": str(stdout_path), "stderr": str(stderr_path)}))
            return 124
    print(json.dumps({"status": "CHILD_EXITED", "exit_code": code, "receipt": str(output),
                      "stdout": str(stdout_path), "stderr": str(stderr_path)}))
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "LAUNCH_FAILED", "error_type": type(exc).__name__, "error": str(exc)}))
        raise SystemExit(2)
