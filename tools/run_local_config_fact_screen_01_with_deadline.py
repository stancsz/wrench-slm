#!/usr/bin/env python3
"""Supervise the authorized local configuration fact screen with hard limits.

The caller must separately authorize the underlying local inference by setting
WRENCH_CONFIG_FACT_SCREEN_01_AUTHORIZED=1. This wrapper never sets that gate.
It reserves storage before creating logs or starting the runner, then enforces a
20-minute process-tree deadline and independent stdout/stderr size caps.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import BinaryIO


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(r"C:\wrench-slm-data")
ARTIFACT_ROOT = DATA_ROOT / "artifacts" / "wrench-local-acceptability"
LOG_ROOT = DATA_ROOT / "logs" / "wrench-local-acceptability"
WEIGHTS_ROOT = DATA_ROOT / "weights"
PINNED_PYTHON = DATA_ROOT / "envs" / "wrench-local-synthetic-cp313" / "Scripts" / "python.exe"
RUNNER = ROOT / "tools" / "run_local_config_fact_screen_01.py"
CHECKER = ROOT / "tools" / "check_wrench_storage_budget.py"
RUN_JOB_ID = "W2-LOCAL-CONFIG-FACT-SCREEN-20260926-01"
EXPECTED_RUNNER_SHA256 = "2e984911b1fcddbcc2a35c56ff76d2f97573316a65a87da4e19852d80f6bf19e"
RESERVE_BYTES = 100_000_000
MIN_FREE_DISK_BYTES = 5 * 1024**3
DEADLINE_SECONDS = 20 * 60
LOG_CAP_BYTES = 16 * 1024 * 1024
POLL_SECONDS = 30
AUTH_ENV = "WRENCH_CONFIG_FACT_SCREEN_01_AUTHORIZED"
SUPERVISOR_ENV = "WRENCH_CONFIG_FACT_SCREEN_01_SUPERVISOR"
SUPERVISOR_HASH_ENV = "WRENCH_CONFIG_FACT_SCREEN_01_SUPERVISOR_SHA256"
SUPERVISOR_VALUE = "deadline-logcap-wrapper-v1"


class SupervisorError(RuntimeError):
    pass


def storage_command(*args: str) -> dict[str, object]:
    done = subprocess.run(
        [str(PINNED_PYTHON), str(CHECKER), "--repo-root", str(ROOT),
         "--storage-root", str(DATA_ROOT), *args],
        cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
    )
    if done.returncode != 0:
        detail = done.stderr[-500:].replace("\r", " ").replace("\n", " ")
        raise SupervisorError(f"storage_command_failed:{args[0]}:{done.returncode}:{detail}")
    try:
        result = json.loads(done.stdout)
    except json.JSONDecodeError as exc:
        raise SupervisorError("storage_command_returned_invalid_json") from exc
    if not isinstance(result, dict):
        raise SupervisorError("storage_command_returned_invalid_shape")
    return result


def status_check(require_reservation: bool) -> dict[str, object]:
    report = storage_command("status")
    if report.get("status") != "WITHIN_LIMIT":
        raise SupervisorError("storage_budget_not_within_limit")
    if require_reservation and RUN_JOB_ID not in report.get("reservations", []):
        raise SupervisorError("supervisor_reservation_not_active")
    return report


def reserve_storage() -> None:
    result = storage_command("reserve", "--job-id", RUN_JOB_ID,
                             "--reserve-bytes", str(RESERVE_BYTES))
    if result.get("status") != "RESERVED" or result.get("job_id") != RUN_JOB_ID:
        raise SupervisorError("storage_reservation_not_confirmed")
    if result.get("reserve_bytes") != RESERVE_BYTES:
        raise SupervisorError("storage_reservation_size_mismatch")


def check_free_disk() -> int:
    free = shutil.disk_usage(Path("C:\\")).free
    if free < MIN_FREE_DISK_BYTES:
        raise SupervisorError("minimum_free_disk_space_not_available")
    return free


def resource_snapshot() -> dict[str, float]:
    if os.name != "nt":
        raise SupervisorError("windows_resource_monitor_required")

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    memory = MemoryStatusEx()
    memory.dwLength = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)) or not memory.ullTotalPhys:
        raise SupervisorError("system_ram_snapshot_unavailable")
    ram_free = memory.ullAvailPhys / memory.ullTotalPhys

    try:
        done = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SupervisorError(f"vram_snapshot_unavailable:{type(exc).__name__}") from exc
    rows: list[float] = []
    for line in done.stdout.splitlines():
        fields = line.split(",")
        if len(fields) != 2:
            raise SupervisorError("vram_snapshot_invalid")
        free_mib, total_mib = (int(value.strip()) for value in fields)
        if total_mib <= 0:
            raise SupervisorError("vram_total_invalid")
        rows.append(free_mib / total_mib)
    if not rows:
        raise SupervisorError("vram_snapshot_empty")
    result = {"ram_free_fraction": ram_free, "vram_free_fraction": min(rows)}
    if any(value < 0.10 for value in result.values()):
        raise SupervisorError("ram_or_vram_reserve_breached")
    return result


def copy_capped(source: BinaryIO, destination: Path, capped: threading.Event,
                stream_error: list[str]) -> None:
    try:
        written = 0
        with destination.open("xb") as output:
            while True:
                block = source.read(64 * 1024)
                if not block:
                    break
                remaining = LOG_CAP_BYTES - written
                if remaining > 0:
                    kept = block[:remaining]
                    output.write(kept)
                    written += len(kept)
                if len(block) > remaining:
                    capped.set()
            output.flush()
            os.fsync(output.fileno())
    except Exception as exc:
        stream_error.append(f"{type(exc).__name__}:{exc}")
        capped.set()
    finally:
        source.close()


def terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name != "nt":
        raise SupervisorError("windows_process_tree_termination_required")
    done = subprocess.run(
        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if done.returncode != 0:
        detail = (done.stderr or done.stdout)[-300:].replace("\r", " ").replace("\n", " ")
        raise SupervisorError(f"child_process_tree_termination_unconfirmed:{done.returncode}:{detail}")
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise SupervisorError("child_process_did_not_stop_after_tree_termination") from exc
    if process.poll() is None:
        raise SupervisorError("child_process_stop_unverified_after_tree_termination")


def report_and_log_bytes(stdout_log: Path, stderr_log: Path) -> tuple[int, dict[str, int]]:
    files: dict[str, int] = {}
    for path in (stdout_log, stderr_log):
        if path.exists():
            files[str(path)] = path.stat().st_size
    if ARTIFACT_ROOT.exists():
        for path in ARTIFACT_ROOT.glob("local-config-fact-screen-01-*.json"):
            if path.is_file():
                files[str(path)] = path.stat().st_size
    return sum(files.values()), files


def main() -> int:
    if os.environ.get(AUTH_ENV) != "1":
        print("blocked: caller must explicitly set WRENCH_CONFIG_FACT_SCREEN_01_AUTHORIZED=1", file=sys.stderr)
        return 2
    if os.name != "nt":
        print("blocked: this supervisor requires Windows process-tree controls", file=sys.stderr)
        return 2
    if not PINNED_PYTHON.is_file() or not RUNNER.is_file() or not CHECKER.is_file():
        print("blocked: pinned Python, runner, or storage checker is missing", file=sys.stderr)
        return 2
    if hashlib.sha256(RUNNER.read_bytes()).hexdigest() != EXPECTED_RUNNER_SHA256:
        print("blocked: runner SHA-256 differs from the reviewed protocol", file=sys.stderr)
        return 2

    reservation_owned = False
    child: subprocess.Popen[bytes] | None = None
    stdout_log = LOG_ROOT / f"{RUN_JOB_ID}.stdout.log"
    stderr_log = LOG_ROOT / f"{RUN_JOB_ID}.stderr.log"
    stdout_thread: threading.Thread | None = None
    stderr_thread: threading.Thread | None = None
    child_stopped = True
    capture_threads_stopped = True
    forced_stop_required = False
    forced_stop_confirmed = False
    run_result: int | None = None
    stop_reason: str | None = None
    accounted_bytes = 0
    accounted_files: dict[str, int] = {}

    try:
        # Admission order is intentional: status, exact peak reserve, then
        # free-space/resource checks. No run logs or model process exist yet.
        status_check(require_reservation=False)
        reserve_storage()
        reservation_owned = True
        disk_free = check_free_disk()
        initial_resources = resource_snapshot()
        status_check(require_reservation=True)

        LOG_ROOT.mkdir(parents=True, exist_ok=True)
        if stdout_log.exists() or stderr_log.exists():
            raise SupervisorError("refusing_to_overwrite_existing_run_logs")
        child_env = os.environ.copy()
        child_env[SUPERVISOR_ENV] = SUPERVISOR_VALUE
        child_env[SUPERVISOR_HASH_ENV] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        child_env["HF_HUB_OFFLINE"] = "1"
        child_env["TRANSFORMERS_OFFLINE"] = "1"
        for secret_name in (
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
            "GOOGLE_APPLICATION_CREDENTIALS", "AZURE_OPENAI_API_KEY", "AZURE_CLIENT_SECRET",
        ):
            child_env.pop(secret_name, None)
        command = [str(PINNED_PYTHON), str(RUNNER), "--model-path", str(WEIGHTS_ROOT / "Qwen3.5-0.8B")]
        child = subprocess.Popen(
            command, cwd=ROOT, env=child_env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        assert child.stdout is not None and child.stderr is not None
        log_cap = threading.Event()
        stream_errors: list[str] = []
        stdout_thread = threading.Thread(target=copy_capped, args=(child.stdout, stdout_log, log_cap, stream_errors), daemon=True)
        stderr_thread = threading.Thread(target=copy_capped, args=(child.stderr, stderr_log, log_cap, stream_errors), daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        deadline = time.monotonic() + DEADLINE_SECONDS
        next_poll = time.monotonic() + POLL_SECONDS
        while child.poll() is None:
            now = time.monotonic()
            if log_cap.is_set():
                stop_reason = "log_cap_or_log_write_failure"
                forced_stop_required = True
                terminate_process_tree(child)
                forced_stop_confirmed = True
                break
            if now >= deadline:
                stop_reason = "20_minute_deadline"
                forced_stop_required = True
                terminate_process_tree(child)
                forced_stop_confirmed = True
                break
            if now >= next_poll:
                try:
                    status_check(require_reservation=True)
                    disk_free = check_free_disk()
                    resource_snapshot()
                except Exception as exc:
                    stop_reason = f"monitor_breach:{type(exc).__name__}:{exc}"
                    forced_stop_required = True
                    terminate_process_tree(child)
                    forced_stop_confirmed = True
                    break
                next_poll = now + POLL_SECONDS
            time.sleep(min(1.0, max(0.0, next_poll - time.monotonic())))

        run_result = child.wait(timeout=30)
        child_stopped = child.poll() is not None
        stdout_thread.join(timeout=30)
        stderr_thread.join(timeout=30)
        if stdout_thread.is_alive() or stderr_thread.is_alive():
            capture_threads_stopped = False
            stop_reason = stop_reason or "log_capture_threads_did_not_stop"
            raise SupervisorError(stop_reason)
        if log_cap.is_set() and stop_reason is None:
            stop_reason = "log_cap_or_log_write_failure"
        if stream_errors:
            stop_reason = stop_reason or "log_capture_failed"
            raise SupervisorError("log_capture_failed:" + ";".join(stream_errors)[:500])

        accounted_bytes, accounted_files = report_and_log_bytes(stdout_log, stderr_log)
        # The full storage scan is the authoritative aggregate-size accounting
        # check while the reservation is still active.
        status_check(require_reservation=True)
        print(json.dumps({
            "job_id": RUN_JOB_ID, "exit_code": run_result, "stop_reason": stop_reason,
            "initial_resources": initial_resources, "c_free_bytes_at_admission": disk_free,
            "deadline_seconds": DEADLINE_SECONDS, "stdout_cap_bytes": LOG_CAP_BYTES,
            "stderr_cap_bytes": LOG_CAP_BYTES, "accounted_report_and_log_bytes": accounted_bytes,
            "accounted_files": accounted_files,
        }, indent=2))
        return run_result if stop_reason is None else 2
    except Exception as exc:
        print(f"supervisor blocked: {type(exc).__name__}: {str(exc)[:500]}", file=sys.stderr)
        return 2
    finally:
        if child is not None:
            if child.poll() is None or (forced_stop_required and not forced_stop_confirmed):
                try:
                    terminate_process_tree(child)
                    if forced_stop_required:
                        forced_stop_confirmed = True
                except Exception as exc:
                    child_stopped = False
                    print(f"child stop unverified: {type(exc).__name__}: {exc}", file=sys.stderr)
            child_stopped = child.poll() is not None and (not forced_stop_required or forced_stop_confirmed)
            for thread in (stdout_thread, stderr_thread):
                if thread is not None:
                    thread.join(timeout=30)
            capture_threads_stopped = all(
                thread is None or not thread.is_alive() for thread in (stdout_thread, stderr_thread)
            )

        if reservation_owned:
            try:
                if not child_stopped or not capture_threads_stopped:
                    raise SupervisorError("reservation_retained_child_or_capture_stop_unverified")
                accounted_bytes, accounted_files = report_and_log_bytes(stdout_log, stderr_log)
                status_check(require_reservation=True)
                # Only release after the child is stopped, output sizes are
                # recorded, and the aggregate inventory has completed.
                result = storage_command("release", "--job-id", RUN_JOB_ID)
                if result.get("status") != "RELEASED":
                    raise SupervisorError("storage_reservation_release_unconfirmed")
                print(json.dumps({"reservation": "RELEASED", "accounted_report_and_log_bytes": accounted_bytes,
                                  "accounted_files": accounted_files}))
            except Exception as exc:
                print(f"reservation retained: {type(exc).__name__}: {str(exc)[:500]}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
