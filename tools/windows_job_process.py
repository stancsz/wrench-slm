"""Bounded Windows subprocess execution using an owned Job Object."""

from __future__ import annotations

import ctypes
import base64
import json
import re
import shutil
import subprocess
import threading
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any


_CREATE_SUSPENDED = 0x00000004
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_CREATE_UNICODE_ENVIRONMENT = 0x00000400
_EXTENDED_STARTUPINFO_PRESENT = 0x00080000
_STARTF_USESTDHANDLES = 0x00000100
_HANDLE_FLAG_INHERIT = 0x00000001
_PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 0x00000102
_WAIT_FAILED = 0xFFFFFFFF
_ERROR_BROKEN_PIPE = 109
_ERROR_NO_DATA = 232
_CAPTURE_LIMIT_BYTES = 1024 * 1024


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", ctypes.c_void_p),
        ("bInheritHandle", wintypes.BOOL),
    ]


class _StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


class _StartupInfoEx(ctypes.Structure):
    _fields_ = [
        ("StartupInfo", _StartupInfo),
        ("lpAttributeList", ctypes.c_void_p),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in (
        "ReadOperationCount",
        "WriteOperationCount",
        "OtherOperationCount",
        "ReadTransferCount",
        "WriteTransferCount",
        "OtherTransferCount",
    )]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _BasicAccountingInformation(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


def _bind_kernel32():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreatePipe.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        ctypes.POINTER(wintypes.HANDLE),
        ctypes.POINTER(_SecurityAttributes),
        wintypes.DWORD,
    ]
    kernel32.CreatePipe.restype = wintypes.BOOL
    kernel32.SetHandleInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
    kernel32.SetHandleInformation.restype = wintypes.BOOL
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_SecurityAttributes),
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.CreateProcessW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.BOOL,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        ctypes.POINTER(_ProcessInformation),
    ]
    kernel32.CreateProcessW.restype = wintypes.BOOL
    kernel32.InitializeProcThreadAttributeList.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
    kernel32.UpdateProcThreadAttribute.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
    kernel32.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    kernel32.DeleteProcThreadAttributeList.restype = None
    kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel32.ResumeThread.restype = wintypes.DWORD
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateJobObject.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    kernel32.ReadFile.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def _raise_last_error(operation: str) -> OSError:
    error = ctypes.get_last_error()
    return OSError(error, f"{operation} failed: {ctypes.FormatError(error).strip()}")


def _assign_windows_process(kernel32, job, process_handle) -> None:
    if not kernel32.AssignProcessToJobObject(job, process_handle):
        raise _raise_last_error("AssignProcessToJobObject")


def _resume_windows_thread(kernel32, thread_handle) -> None:
    resumed_count = kernel32.ResumeThread(thread_handle)
    if resumed_count == _WAIT_FAILED:
        raise _raise_last_error("ResumeThread")
    if resumed_count != 1:
        raise RuntimeError(f"ResumeThread returned unexpected suspend count {resumed_count}")


def _prepare_windows_command(
    command: list[str], env: dict[str, str]
) -> tuple[list[str], dict[str, str]]:
    executable = Path(command[0])
    suffix = executable.suffix.casefold()
    if suffix not in {".cmd", ".bat", ".ps1"}:
        return command, env
    if suffix in {".cmd", ".bat"} and executable.is_file():
        shim_text = executable.read_text(encoding="utf-8", errors="replace")
        native_match = re.search(r'"%dp0%\\([^\"]+\.exe)"\s+%\*', shim_text, re.IGNORECASE)
        if native_match:
            native_executable = executable.parent / native_match.group(1).replace("\\", "/")
            if native_executable.is_file():
                return [str(native_executable), *command[1:]], env
        script_match = re.search(r'"%dp0%\\([^\"]+\.js)"\s+%\*', shim_text, re.IGNORECASE)
        if script_match:
            node_executable = executable.parent / "node.exe"
            if not node_executable.is_file():
                node_path = shutil.which("node.exe") or shutil.which("node")
                if node_path:
                    node_executable = Path(node_path)
            script_path = executable.parent / script_match.group(1).replace("\\", "/")
            if node_executable.is_file() and script_path.is_file():
                return [str(node_executable), str(script_path), *command[1:]], env
    script = executable.with_suffix(".ps1") if suffix in {".cmd", ".bat"} else executable
    if not script.is_file():
        raise RuntimeError(f"No PowerShell wrapper exists for Windows script {executable}")
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise RuntimeError("powershell.exe is required to launch Windows script clients safely")
    dispatcher = (
        "$raw = $env:WRENCH_JOB_LAUNCH_PAYLOAD; "
        "Remove-Item Env:WRENCH_JOB_LAUNCH_PAYLOAD; "
        "$data = ConvertFrom-Json -InputObject "
        "([System.Text.Encoding]::UTF8.GetString("
        "[System.Convert]::FromBase64String($raw))); "
        "$scriptPath = [string]$data.script; "
        "$scriptArgs = @($data.arguments); "
        "& $scriptPath @scriptArgs; exit $LASTEXITCODE"
    )
    encoded_dispatcher = base64.b64encode(dispatcher.encode("utf-16le")).decode("ascii")
    prepared_env = dict(env)
    prepared_env["WRENCH_JOB_LAUNCH_PAYLOAD"] = base64.b64encode(
        json.dumps(
            {"script": str(script), "arguments": command[1:]},
            ensure_ascii=False,
        ).encode("utf-8")
    ).decode("ascii")
    return [
        powershell,
        "-NoProfile",
        "-NonInteractive",
        "-OutputFormat",
        "Text",
        "-ExecutionPolicy",
        "Bypass",
        "-EncodedCommand",
        encoded_dispatcher,
    ], prepared_env


def run_bounded_subprocess(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run one Windows process tree with a strict owned-job boundary."""
    command, env = _prepare_windows_command(command, env)
    kernel32 = _bind_kernel32()
    security = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), None, True)
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise _raise_last_error("CreateJobObjectW")

    pipe_handles: list[int] = []
    process_handle = thread_handle = None
    job_assigned = False
    attribute_list = None
    attribute_list_initialized = False
    readers: list[threading.Thread] = []
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    capture_errors: list[str] = []
    capture_lock = threading.Lock()
    started = time.perf_counter()
    timed_out = False
    tree_cleanup_complete = False
    job_empty = False
    exit_code: int | None = None
    try:
        limits = _ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            job,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            raise _raise_last_error("SetInformationJobObject")

        read_pipes: dict[str, wintypes.HANDLE] = {}
        write_pipes: dict[str, wintypes.HANDLE] = {}
        for stream_name in ("stdout", "stderr"):
            read_handle = wintypes.HANDLE()
            write_handle = wintypes.HANDLE()
            if not kernel32.CreatePipe(
                ctypes.byref(read_handle), ctypes.byref(write_handle), ctypes.byref(security), 0
            ):
                raise _raise_last_error("CreatePipe")
            pipe_handles.extend((read_handle.value, write_handle.value))
            if not kernel32.SetHandleInformation(read_handle, _HANDLE_FLAG_INHERIT, 0):
                raise _raise_last_error("SetHandleInformation")
            read_pipes[stream_name] = read_handle
            write_pipes[stream_name] = write_handle

        stdin_handle = kernel32.CreateFileW(
            "NUL",
            0x80000000,
            0x00000001 | 0x00000002,
            ctypes.byref(security),
            3,
            0x00000080,
            None,
        )
        if not stdin_handle or stdin_handle == wintypes.HANDLE(-1).value:
            raise _raise_last_error("CreateFileW(NUL)")
        pipe_handles.append(stdin_handle)

        startup = _StartupInfo()
        startup.cb = ctypes.sizeof(_StartupInfoEx)
        startup.dwFlags = _STARTF_USESTDHANDLES
        startup.hStdInput = stdin_handle
        startup.hStdOutput = write_pipes["stdout"]
        startup.hStdError = write_pipes["stderr"]
        attribute_size = ctypes.c_size_t()
        kernel32.InitializeProcThreadAttributeList(
            None, 1, 0, ctypes.byref(attribute_size)
        )
        if attribute_size.value == 0:
            raise _raise_last_error("InitializeProcThreadAttributeList(size)")
        attribute_buffer = ctypes.create_string_buffer(attribute_size.value)
        attribute_list = ctypes.cast(attribute_buffer, ctypes.c_void_p)
        if not kernel32.InitializeProcThreadAttributeList(
            attribute_list, 1, 0, ctypes.byref(attribute_size)
        ):
            raise _raise_last_error("InitializeProcThreadAttributeList")
        attribute_list_initialized = True
        inherited_handles = (wintypes.HANDLE * 3)(
            stdin_handle,
            write_pipes["stdout"].value,
            write_pipes["stderr"].value,
        )
        if not kernel32.UpdateProcThreadAttribute(
            attribute_list,
            0,
            _PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
            ctypes.byref(inherited_handles),
            ctypes.sizeof(inherited_handles),
            None,
            None,
        ):
            raise _raise_last_error("UpdateProcThreadAttribute(HANDLE_LIST)")
        startup_ex = _StartupInfoEx(startup, attribute_list)
        process_info = _ProcessInformation()
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        environment = "\0".join(
            f"{key}={value}" for key, value in sorted(env.items(), key=lambda item: item[0].casefold())
        ) + "\0\0"
        environment_block = ctypes.create_unicode_buffer(environment)
        creation_flags = (
            _CREATE_SUSPENDED
            | _CREATE_NEW_PROCESS_GROUP
            | _CREATE_UNICODE_ENVIRONMENT
            | _EXTENDED_STARTUPINFO_PRESENT
        )
        if not kernel32.CreateProcessW(
            command[0],
            command_line,
            None,
            None,
            True,
            creation_flags,
            ctypes.cast(environment_block, ctypes.c_void_p),
            str(cwd),
            ctypes.byref(startup_ex),
            ctypes.byref(process_info),
        ):
            raise _raise_last_error("CreateProcessW")
        kernel32.DeleteProcThreadAttributeList(attribute_list)
        attribute_list_initialized = False
        process_handle = process_info.hProcess
        thread_handle = process_info.hThread
        for handle in (stdin_handle, write_pipes["stdout"], write_pipes["stderr"]):
            kernel32.CloseHandle(handle)
            pipe_handles.remove(handle.value if hasattr(handle, "value") else handle)

        _assign_windows_process(kernel32, job, process_handle)
        job_assigned = True

        def drain_stream(name: str, handle: wintypes.HANDLE) -> None:
            while True:
                buffer = ctypes.create_string_buffer(64 * 1024)
                bytes_read = wintypes.DWORD()
                if not kernel32.ReadFile(
                    handle, buffer, len(buffer), ctypes.byref(bytes_read), None
                ):
                    error = ctypes.get_last_error()
                    if error not in (_ERROR_BROKEN_PIPE, _ERROR_NO_DATA):
                        with capture_lock:
                            capture_errors.append(
                                f"{name} ReadFile failed with Windows error {error}"
                            )
                        return
                    break
                if bytes_read.value == 0:
                    break
                with capture_lock:
                    output = captured[name]
                    output.extend(buffer.raw[: bytes_read.value])
                    if len(output) > _CAPTURE_LIMIT_BYTES:
                        del output[: len(output) - _CAPTURE_LIMIT_BYTES]

        for stream_name, read_handle in read_pipes.items():
            reader = threading.Thread(
                target=drain_stream,
                args=(stream_name, read_handle),
                daemon=True,
                name=f"wrench-{stream_name}-capture",
            )
            reader.start()
            readers.append(reader)

        _resume_windows_thread(kernel32, thread_handle)
        kernel32.CloseHandle(thread_handle)
        thread_handle = None

        deadline = time.monotonic() + timeout_seconds
        completion_error: OSError | None = None
        while True:
            process_state = kernel32.WaitForSingleObject(process_handle, 0)
            if process_state == _WAIT_FAILED:
                completion_error = _raise_last_error("WaitForSingleObject")
                break
            accounting = _BasicAccountingInformation()
            if not kernel32.QueryInformationJobObject(
                job,
                1,
                ctypes.byref(accounting),
                ctypes.sizeof(accounting),
                None,
            ):
                completion_error = _raise_last_error("QueryInformationJobObject")
                break
            job_empty = accounting.ActiveProcesses == 0
            if process_state == _WAIT_OBJECT_0 and accounting.ActiveProcesses == 0:
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            time.sleep(min(0.025, remaining))

        if completion_error is not None:
            timed_out = True
        cleanup_deadline = time.monotonic() + 5
        if timed_out and job_assigned:
            if not kernel32.TerminateJobObject(job, 1):
                completion_error = _raise_last_error("TerminateJobObject")
            else:
                while time.monotonic() < cleanup_deadline:
                    accounting = _BasicAccountingInformation()
                    if not kernel32.QueryInformationJobObject(
                        job,
                        1,
                        ctypes.byref(accounting),
                        ctypes.sizeof(accounting),
                        None,
                    ):
                        completion_error = _raise_last_error("QueryInformationJobObject")
                        break
                    job_empty = accounting.ActiveProcesses == 0
                    if job_empty:
                        break
                    time.sleep(0.025)
        if job_assigned:
            kernel32.CloseHandle(job)
            job = None

        process_signaled = kernel32.WaitForSingleObject(
            process_handle,
            max(0, int((cleanup_deadline - time.monotonic()) * 1000)),
        ) == _WAIT_OBJECT_0
        for reader in readers:
            reader.join(max(0, cleanup_deadline - time.monotonic()))
        readers_complete = all(not reader.is_alive() for reader in readers)
        if not process_signaled:
            kernel32.TerminateProcess(process_handle, 1)
            process_signaled = kernel32.WaitForSingleObject(process_handle, 0) == _WAIT_OBJECT_0
        tree_cleanup_complete = (
            completion_error is None and job_empty and process_signaled and readers_complete
        )
        if process_signaled:
            native_exit_code = wintypes.DWORD()
            if kernel32.GetExitCodeProcess(process_handle, ctypes.byref(native_exit_code)):
                exit_code = int(native_exit_code.value)
        with capture_lock:
            stdout = bytes(captured["stdout"])
            stderr = bytes(captured["stderr"])
            capture_error = "; ".join(capture_errors) or None
        return {
            "exit_code": None if timed_out else exit_code,
            "timed_out": timed_out,
            "timeout_seconds": timeout_seconds,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "stdout": stdout,
            "stderr": stderr,
            "tree_cleanup_complete": tree_cleanup_complete and capture_error is None,
            "cleanup_error": (
                str(completion_error)
                if completion_error
                else capture_error
            ),
        }
    except Exception:
        if job_assigned and job:
            kernel32.TerminateJobObject(job, 1)
        elif process_handle:
            kernel32.TerminateProcess(process_handle, 1)
        if process_handle:
            kernel32.WaitForSingleObject(process_handle, 5000)
        raise
    finally:
        if thread_handle:
            kernel32.CloseHandle(thread_handle)
        if job:
            kernel32.CloseHandle(job)
        if process_handle:
            kernel32.CloseHandle(process_handle)
        if attribute_list_initialized and attribute_list:
            kernel32.DeleteProcThreadAttributeList(attribute_list)
        for handle in pipe_handles:
            if handle:
                kernel32.CloseHandle(handle)
