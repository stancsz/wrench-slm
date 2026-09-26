"""Run the config-draft screen under an offline process deadline."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(r"C:\wrench-slm-data")
RUNTIME_PYTHON = DATA_ROOT / "envs" / "wrench-local-synthetic-cp313" / "Scripts" / "python.exe"
RUNNER = ROOT / "tools" / "run_local_config_review_draft_screen_01.py"
OUTPUT_ROOT = DATA_ROOT / "artifacts" / "wrench-local-acceptability"
LOG_ROOT = DATA_ROOT / "logs" / "wrench-local-acceptability"
OUTPUT = OUTPUT_ROOT / "local-config-review-draft-screen-01.json"
STDOUT_LOG = LOG_ROOT / "local-config-review-draft-screen-01.stdout.log"
STDERR_LOG = LOG_ROOT / "local-config-review-draft-screen-01.stderr.log"
HARD_TIMEOUT_SECONDS = 25 * 60
POLL_SECONDS = 30
JOB_ID = "W2-LOCAL-SLM-CONFIG-DRAFT-RUN-20260925"
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_LOG_BYTES = 16 * 1024 * 1024
MIN_DESTINATION_FREE_BYTES = 5 * 1024 * 1024 * 1024


def _assert_storage_admitted(timeout: float = 60) -> None:
    done = subprocess.run([sys.executable, str(ROOT / "tools" / "check_wrench_storage_budget.py"), "status"],
                          cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=True)
    status = json.loads(done.stdout)
    if (status.get("status") != "WITHIN_LIMIT" or status.get("errors") or
            JOB_ID not in status.get("reservations", []) or
            status.get("projected_bytes", status["limit_bytes"]) >= status["limit_bytes"]):
        raise RuntimeError("storage budget or job reservation is no longer admitted")


def _mark_stopped(status_name: str) -> bool:
    if not OUTPUT.is_file():
        return False
    try:
        _assert_storage_admitted()
        if OUTPUT.stat().st_size > MAX_OUTPUT_BYTES:
            return False
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        report["run_status"] = status_name
        report["supervisor_timeout_seconds"] = HARD_TIMEOUT_SECONDS
        temp = OUTPUT.with_name(OUTPUT.name + f".{uuid.uuid4().hex}.tmp")
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if len(rendered.encode("utf-8")) > MAX_OUTPUT_BYTES:
            return False
        with temp.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, OUTPUT)
        return True
    except Exception:
        return False


def _assert_destination_space() -> int:
    free = shutil.disk_usage(DATA_ROOT).free
    if free < MIN_DESTINATION_FREE_BYTES:
        raise RuntimeError("destination_volume_free_space_below_5_GiB")
    return free


def _pump_bounded(pipe, path: Path, stop_event: threading.Event, error_event: threading.Event) -> None:
    written = 0
    try:
        with path.open("xb") as stream:
            while True:
                chunk = pipe.read(64 * 1024)
                if not chunk:
                    break
                room = max(0, MAX_LOG_BYTES - written)
                if room:
                    kept = chunk[:room]
                    stream.write(kept)
                    written += len(kept)
                if len(chunk) > room:
                    stop_event.set()
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        error_event.set()
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def _terminate_process_tree(child: subprocess.Popen) -> None:
    if child.poll() is not None:
        return
    try:
        done = subprocess.run(
            ["taskkill.exe", "/PID", str(child.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=20, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if done.returncode == 0:
            child.wait(timeout=20)
            return
    except Exception:
        pass
    child.kill()
    child.wait(timeout=20)


def main() -> int:
    if OUTPUT.exists() or STDOUT_LOG.exists() or STDERR_LOG.exists():
        raise FileExistsError("screen output or log already exists")
    if not RUNTIME_PYTHON.is_file() or not RUNNER.is_file():
        raise FileNotFoundError("pinned runtime or screen runner is missing")
    _assert_storage_admitted()
    _assert_destination_space()
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "WRENCH_CONFIG_DRAFT_SUPERVISED": "1",
        "HF_HOME": str(DATA_ROOT / "cache" / "huggingface"),
        "TORCH_HOME": str(DATA_ROOT / "cache" / "torch"),
    })
    command = [str(RUNTIME_PYTHON), "-B", str(RUNNER), "--output", str(OUTPUT)]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=False, creationflags=flags)
    log_limit_event = threading.Event()
    log_error_event = threading.Event()
    pumps = [
        threading.Thread(target=_pump_bounded, args=(child.stdout, STDOUT_LOG, log_limit_event, log_error_event), daemon=True),
        threading.Thread(target=_pump_bounded, args=(child.stderr, STDERR_LOG, log_limit_event, log_error_event), daemon=True),
    ]
    for pump in pumps:
        pump.start()
    deadline = time.monotonic() + HARD_TIMEOUT_SECONDS
    try:
        while True:
            if log_limit_event.is_set():
                _terminate_process_tree(child)
                _mark_stopped("stopped_log_limit")
                return 2
            if log_error_event.is_set():
                raise RuntimeError("bounded_log_writer_failed")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, HARD_TIMEOUT_SECONDS)
            status = child.poll()
            if status is not None:
                for pump in pumps:
                    pump.join(timeout=5)
                if any(pump.is_alive() for pump in pumps) or log_error_event.is_set():
                    raise RuntimeError("bounded_log_drain_failed")
                return status
            _assert_storage_admitted(min(60, remaining))
            _assert_destination_space()
            time.sleep(min(POLL_SECONDS, remaining))
    except subprocess.TimeoutExpired:
        _terminate_process_tree(child)
        _mark_stopped("hard_timeout")
        raise
    except Exception:
        _terminate_process_tree(child)
        _mark_stopped("stopped_supervisor_error")
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "LAUNCH_FAILED_OR_STOPPED", "error_type": type(exc).__name__,
                          "error": str(exc)[:300]}), file=sys.stderr)
        raise SystemExit(2)
