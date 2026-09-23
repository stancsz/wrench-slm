from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from wrench_harness import CancellationToken, ProposalRouter, RouterConfig, execute_local_qwen, execute_model_output, execute_proposal, load_router_state, save_router_state
from tools.inspect_qwen_checkpoint import inspect_checkpoint
from tools.estimate_qwen_pruned_sizes import analyze_checkpoint
from tools.prune_qwen_experts import prune_checkpoint
from tools.validate_pruning_source import validate_pruning_source


def proposal(action: str, **fields):
    return {"schema": "wrench.proposal.v1", "action": action, **fields}


def test_read_file_and_lines_are_bounded(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    result = execute_proposal(proposal("read_file", path="note.txt"), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["text"] == "alpha\nbeta\ngamma\n"

    result = execute_proposal(proposal("read_lines", path="note.txt", start=2, end=3), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["lines"] == ["beta", "gamma"]

    rejected = execute_proposal(proposal("read_file", path="..\\outside.txt"), tmp_path)
    assert rejected == {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}


def test_read_file_reads_at_most_limit_plus_one_bytes(tmp_path: Path, monkeypatch):
    target = tmp_path / "growing.txt"
    target.write_bytes(b"x" * 4096)
    from wrench_harness import core

    real_open = core._open_contained_file
    returned_bytes = 0

    class TrackingReader:
        def __init__(self, wrapped):
            self.context = wrapped
            self.wrapped = None

        def __enter__(self):
            self.wrapped = self.context.__enter__()
            return self

        def __exit__(self, *args):
            return self.context.__exit__(*args)

        def read(self, size=-1):
            nonlocal returned_bytes
            chunk = self.wrapped.read(size)
            returned_bytes += len(chunk)
            return chunk

    def tracking_open(path, root, anchor):
        opened = real_open(path, root, anchor)
        return TrackingReader(opened) if path == target else opened

    monkeypatch.setattr(core, "_open_contained_file", tracking_open)
    result = execute_proposal(
        proposal("read_file", path="growing.txt", max_bytes=32), tmp_path
    )

    assert result == {"status": "abstain", "fallback_reason": "file_size_limit"}
    assert returned_bytes == 33


def test_read_file_rejects_leaf_symlink_swap_before_open(tmp_path: Path, monkeypatch):
    import os
    import pytest
    import wrench_harness.core as core

    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        pytest.skip("requires POSIX descriptor-relative no-follow open")

    target = tmp_path / "note.txt"
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    target.write_text("inside", encoding="utf-8")
    outside.write_text("outside-secret", encoding="utf-8")
    real_open = os.open
    swapped = False

    def swap_then_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if path == "note.txt" and dir_fd is not None and not swapped:
            target.unlink()
            target.symlink_to(outside)
            swapped = True
        return real_open(path, flags, mode, dir_fd=dir_fd) if dir_fd is not None else real_open(path, flags, mode)

    monkeypatch.setattr(core.os, "open", swap_then_open)
    result = execute_proposal(proposal("read_file", path="note.txt"), tmp_path)

    assert swapped is True
    assert result["status"] == "abstain"
    assert "outside-secret" not in json.dumps(result)
    outside.unlink(missing_ok=True)


def test_windows_handle_relative_open_reads_nested_file_and_pins_ancestors(tmp_path: Path):
    import os
    import pytest
    import wrench_harness.core as core

    if os.name != "nt":
        pytest.skip("requires Windows handle-relative file opens")

    root = tmp_path / "allowed"
    parent = root / "nested"
    parent.mkdir(parents=True)
    (parent / "note.txt").write_text("inside", encoding="utf-8")
    root_data = core._root(str(root))
    assert root_data is not None
    resolved_root, root_identity = root_data
    anchor = core._RootAnchor(resolved_root, root_identity)
    directory_fd = None
    file_fd = None
    try:
        with pytest.raises(OSError):
            root.rename(tmp_path / "allowed-renamed")
        directory_fd = core._windows_open_relative_component(
            anchor.handle, "nested", directory=True
        )
        with pytest.raises(OSError):
            parent.rename(root / "renamed")
        file_fd = core._windows_open_relative_component(
            directory_fd, "note.txt", directory=False
        )
        with pytest.raises(OSError):
            (parent / "note.txt").rename(parent / "renamed.txt")
        result = execute_proposal(
            proposal("read_file", path="nested/note.txt"), root
        )
        assert result["status"] == "accepted"
        assert result["observation"]["text"] == "inside"
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)
        anchor.close()


def test_windows_handle_relative_open_rejects_junction_swap(tmp_path: Path, monkeypatch):
    import os
    import pytest
    import wrench_harness.core as core

    if os.name != "nt":
        pytest.skip("requires Windows reparse-point handling")

    root = tmp_path / "allowed"
    nested = root / "nested"
    outside = tmp_path / "outside"
    root.mkdir()
    nested.mkdir()
    outside.mkdir()
    (nested / "secret.txt").write_text("inside", encoding="utf-8")
    sentinel = outside / "secret.txt"
    sentinel.write_text("outside-secret", encoding="utf-8")
    moved_nested = root / "nested-original"
    junction = nested
    real_open_component = core._windows_open_relative_component
    swapped = False
    junction_created = False

    def swap_to_junction(parent_fd, component, *, directory):
        nonlocal swapped, junction_created
        if component == "nested" and not swapped:
            nested.rename(moved_nested)
            command = subprocess.list2cmdline(
                ["mklink", "/J", str(junction), str(outside)]
            )
            completed = subprocess.run(
                ["cmd.exe", "/c", command], capture_output=True, text=True
            )
            if completed.returncode != 0:
                moved_nested.rename(nested)
                pytest.skip(f"junction creation unavailable: {completed.stderr.strip()}")
            junction_created = True
            swapped = True
        return real_open_component(parent_fd, component, directory=directory)

    monkeypatch.setattr(core, "_windows_open_relative_component", swap_to_junction)
    try:
        result = execute_proposal(
            proposal("read_file", path="nested/secret.txt"), root
        )
        assert swapped is True
        assert result["status"] == "abstain"
        assert result["fallback_reason"] == "path_containment_unverified"
        assert "outside-secret" not in json.dumps(result)
    finally:
        if junction_created:
            os.rmdir(junction)
        if moved_nested.exists():
            moved_nested.rename(nested)


def test_read_file_uses_pinned_root_after_root_path_swap(tmp_path: Path, monkeypatch):
    import os
    import pytest
    import wrench_harness.core as core

    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        pytest.skip("requires POSIX descriptor-relative no-follow open")

    root = tmp_path / "allowed"
    outside = tmp_path / "outside"
    moved_root = tmp_path / "allowed-original"
    root.mkdir()
    outside.mkdir()
    (root / "note.txt").write_text("inside-secret", encoding="utf-8")
    (outside / "note.txt").write_text("outside-secret", encoding="utf-8")
    real_open = core._open_contained_file
    swapped = False

    def swap_root_before_file_open(path, allowed_root, anchor):
        nonlocal swapped
        if not swapped:
            root.rename(moved_root)
            root.symlink_to(outside, target_is_directory=True)
            swapped = True
        return real_open(path, allowed_root, anchor)

    monkeypatch.setattr(core, "_open_contained_file", swap_root_before_file_open)
    result = execute_proposal(proposal("read_file", path="note.txt"), root)

    assert swapped is True
    assert result["status"] == "accepted"
    assert result["observation"]["text"] == "inside-secret"
    assert "outside-secret" not in json.dumps(result)


def test_read_file_rejects_root_replacement_before_anchor_open(tmp_path: Path, monkeypatch):
    import wrench_harness.core as core

    root = tmp_path / "allowed"
    replacement = tmp_path / "replacement"
    original_root = tmp_path / "allowed-original"
    root.mkdir()
    replacement.mkdir()
    (root / "note.txt").write_text("inside-secret", encoding="utf-8")
    (replacement / "note.txt").write_text("outside-secret", encoding="utf-8")
    real_anchor = core._RootAnchor
    swapped = False

    def swap_then_anchor(path, expected_identity):
        nonlocal swapped
        root.rename(original_root)
        replacement.rename(root)
        swapped = True
        return real_anchor(path, expected_identity)

    monkeypatch.setattr(core, "_RootAnchor", swap_then_anchor)
    result = execute_proposal(proposal("read_file", path="note.txt"), root)

    assert swapped is True
    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "path_containment_unverified"
    assert "outside-secret" not in json.dumps(result)


def test_read_lines_stops_after_requested_range_in_large_file(tmp_path: Path, monkeypatch):
    from wrench_harness import core

    target = tmp_path / "large.log"
    trailing_line = b"unrequested\n"
    target.write_bytes(
        b"first line\n"
        + trailing_line * (core.MAX_FILE_BYTES // len(trailing_line) + 1)
    )
    real_open = core._open_contained_file
    returned_bytes = 0

    class TrackingReader:
        def __init__(self, wrapped):
            self.context = wrapped
            self.wrapped = None

        def __enter__(self):
            self.wrapped = self.context.__enter__()
            return self

        def __exit__(self, *args):
            return self.context.__exit__(*args)

        def readline(self, size=-1):
            nonlocal returned_bytes
            chunk = self.wrapped.readline(size)
            returned_bytes += len(chunk)
            return chunk

    def tracking_open(path, root, anchor):
        opened = real_open(path, root, anchor)
        return TrackingReader(opened) if path == target else opened

    monkeypatch.setattr(core, "_open_contained_file", tracking_open)
    result = execute_proposal(proposal("read_lines", path="large.log", start=1, end=1), tmp_path)

    assert result["status"] == "accepted"
    assert result["observation"]["lines"] == ["first line"]
    assert returned_bytes == len(b"first line\n")
    assert core.MAX_FILE_BYTES == 256 * 1024


def test_read_lines_rejects_oversized_requested_line_and_invalid_utf8(tmp_path: Path):
    from wrench_harness import core

    oversized = tmp_path / "oversized.txt"
    oversized.write_bytes((b"x" * (core.MAX_FILE_BYTES + 32)) + b"\n")
    rejected = execute_proposal(
        proposal("read_lines", path="oversized.txt", start=1, end=1), tmp_path
    )
    assert rejected == {"status": "abstain", "fallback_reason": "file_size_limit"}

    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"good line\n\xff\n")
    rejected = execute_proposal(
        proposal("read_lines", path="invalid.txt", start=2, end=2), tmp_path
    )
    assert rejected["status"] == "abstain"
    assert rejected["fallback_reason"] == "encoding_or_read_error"


def test_literal_search_is_not_regex_and_respects_limit(tmp_path: Path):
    (tmp_path / "a.txt").write_text("needle\nneedle.*\n", encoding="utf-8")
    result = execute_proposal(proposal("literal_search", root=".", literal="needle.*", max_matches=3), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["matches"][0]["line"] == 2
    assert result["observation"]["truncated"] is False

    capped = execute_proposal(proposal("literal_search", root=".", literal="needle.*", max_matches=1), tmp_path)
    assert len(capped["observation"]["matches"]) == 1
    assert capped["observation"]["truncated"] is True

    regex = execute_proposal(
        proposal("literal_search", root=".", literal="^needle", mode="regex", max_matches=3), tmp_path
    )
    assert regex["fallback_reason"] == "literal_mode_required"


def test_literal_search_rejects_leaf_swap_before_secure_open(tmp_path: Path, monkeypatch):
    import os
    import pytest
    import wrench_harness.core as core

    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        pytest.skip("requires POSIX descriptor-relative no-follow open")

    target = tmp_path / "note.txt"
    outside = tmp_path.parent / f"{tmp_path.name}-search-outside.txt"
    target.write_text("needle inside", encoding="utf-8")
    outside.write_text("needle outside-secret", encoding="utf-8")
    real_open = core._open_contained_file
    swapped = False

    def swap_then_open(path, root, anchor):
        nonlocal swapped
        if path == target and not swapped:
            target.unlink()
            target.symlink_to(outside)
            swapped = True
        return real_open(path, root, anchor)

    monkeypatch.setattr(core, "_open_contained_file", swap_then_open)
    result = execute_proposal(
        proposal("literal_search", root=".", literal="needle", max_matches=3),
        tmp_path,
    )

    assert swapped is True
    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "path_containment_unverified"
    assert "outside-secret" not in json.dumps(result)
    outside.unlink(missing_ok=True)


def test_git_status_is_read_only(tmp_path: Path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "tracked.txt"], check=True)
    git_dir = tmp_path / ".git"
    before = {
        path.relative_to(git_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in git_dir.rglob("*")
        if path.is_file()
    }

    result = execute_proposal(proposal("git_read_status", repo_root="."), tmp_path)

    after = {
        path.relative_to(git_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in git_dir.rglob("*")
        if path.is_file()
    }
    assert result["status"] == "accepted"
    assert result["observation"]["mutated"] is False
    assert after == before


def test_git_status_rejects_gitfile_indirection(tmp_path: Path):
    repo = tmp_path / "linked-worktree"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: ../outside-metadata\n", encoding="utf-8")

    result = execute_proposal(
        proposal("git_read_status", repo_root="linked-worktree"), tmp_path
    )

    assert result == {"status": "abstain", "fallback_reason": "repository_root_invalid"}


def test_git_status_strips_environment_overrides_and_disables_external_monitor(
    tmp_path: Path, monkeypatch
):
    import subprocess as subprocess_module
    import wrench_harness.core as core

    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "outside.git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "outside-index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    observed = {}

    def fake_run(args, **kwargs):
        observed.setdefault("calls", []).append(args)
        observed["env"] = kwargs["env"]
        if args == ["git", "--version"]:
            return subprocess_module.CompletedProcess(args, 0, "git version 2.52.0.windows.1\n", "")
        observed["status_args"] = args
        return subprocess_module.CompletedProcess(args, 0, "## main\n", "")

    monkeypatch.setattr(core.subprocess, "run", fake_run)
    result = execute_proposal(proposal("git_read_status", repo_root="."), tmp_path)

    assert result["status"] == "accepted"
    assert "GIT_DIR" not in observed["env"]
    assert "GIT_INDEX_FILE" not in observed["env"]
    assert "GIT_CONFIG_COUNT" not in observed["env"]
    assert observed["env"]["GIT_OPTIONAL_LOCKS"] == "0"
    assert "core.fsmonitor=false" in observed["status_args"]
    assert "--no-optional-locks" in observed["status_args"]


def test_git_status_fails_closed_before_unsafe_fsmonitor_versions(tmp_path: Path, monkeypatch):
    import subprocess as subprocess_module
    import wrench_harness.core as core

    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    calls = []

    def old_git(args, **kwargs):
        calls.append(args)
        return subprocess_module.CompletedProcess(args, 0, "git version 2.35.1\n", "")

    monkeypatch.setattr(core.subprocess, "run", old_git)
    result = execute_proposal(proposal("git_read_status", repo_root="."), tmp_path)

    assert result == {"status": "abstain", "fallback_reason": "git_version_unsupported"}
    assert calls == [["git", "--version"]]


def test_git_status_does_not_run_repository_fsmonitor_config(tmp_path: Path):
    import shlex
    import sys

    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    marker = tmp_path / "fsmonitor-ran.txt"
    helper = tmp_path / "fsmonitor_helper.py"
    helper.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n"
        "print('token\\0', end='')\n",
        encoding="utf-8",
    )
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(helper))}"
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "core.fsmonitor", command],
        check=True,
    )

    result = execute_proposal(proposal("git_read_status", repo_root="."), tmp_path)

    assert result["status"] == "accepted"
    assert not marker.exists()


def test_git_status_overrides_repository_worktree_config(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "wrench@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Wrench Test"], check=True)
    (repo / "tracked.txt").write_text("present\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "--quiet", "-m", "baseline"], check=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    subprocess.run(
        ["git", "-C", str(repo), "config", "core.worktree", str(outside)], check=True
    )

    result = execute_proposal(
        proposal("git_read_status", repo_root="repo"), tmp_path
    )

    assert result["status"] == "accepted"
    assert "D  tracked.txt" not in result["observation"]["output"]


def test_health_and_patch_fail_closed(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("old\n", encoding="utf-8")
    external = execute_proposal(proposal("health_read", url="https://example.com/health"), tmp_path)
    assert external["fallback_reason"] == "health_endpoint_not_allowlisted"

    bool_timeout = execute_proposal(
        proposal(
            "health_read",
            url="http://localhost:4000/health",
            timeout_seconds=True,
            max_bytes=4096,
        ),
        tmp_path,
    )
    bool_limit = execute_proposal(
        proposal(
            "health_read",
            url="http://localhost:4000/health",
            timeout_seconds=3,
            max_bytes=True,
        ),
        tmp_path,
    )
    assert bool_timeout["fallback_reason"] == "invalid_health_request"
    assert bool_limit["fallback_reason"] == "invalid_health_request"

    patch = execute_proposal(
        proposal(
            "patch_draft",
            files=["note.txt"],
            review_only=True,
            diff="--- a/note.txt\n+++ b/note.txt\n@@ -1 +1 @@\n-old\n+new\n",
        ),
        tmp_path,
    )
    assert patch["status"] == "accepted"
    assert patch["observation"]["applied"] is False
    assert target.read_text(encoding="utf-8") == "old\n"

    addition_only = execute_proposal(
        proposal(
            "patch_draft",
            files=["note.txt"],
            review_only=True,
            diff="--- a/note.txt\n+++ b/note.txt\n@@ -1,1 +1,2 @@\n old\n+new\n",
        ),
        tmp_path,
    )
    assert addition_only["status"] == "accepted"
    assert addition_only["observation"]["applied"] is False

    empty_patch = execute_proposal(
        proposal(
            "patch_draft",
            files=["note.txt"],
            review_only=True,
            diff="--- a/note.txt\n+++ b/note.txt\n@@ -1 @@\n\n",
        ),
        tmp_path,
    )
    assert empty_patch["fallback_reason"] == "invalid_patch_diff"

    applied = execute_proposal(proposal("patch_draft", files=["note.txt"], review_only=False, diff="x"), tmp_path)
    assert applied["fallback_reason"] == "patch_draft_requires_review_only"


def test_localhost_health_probe_uses_deterministic_ipv4_resolution(monkeypatch, tmp_path: Path):
    import wrench_harness.core as core

    seen = {}

    class Response:
        status = 200

        def read(self, limit):
            return b'{"status":"ok"}'

    class Connection:
        def __init__(self, host, port, timeout):
            seen["host"] = host
            self.sock = self

        def connect(self):
            return None

        def settimeout(self, value):
            return None

        def request(self, method, path, headers):
            seen["request"] = (method, path)

        def getresponse(self):
            return Response()

        def close(self):
            return None

    monkeypatch.setattr(core.http.client, "HTTPConnection", Connection)
    result = execute_proposal(
        proposal(
            "health_read",
            url="http://localhost:4000/health",
            timeout_seconds=3,
            max_bytes=4096,
        ),
        tmp_path,
    )
    assert result["status"] == "accepted"
    assert seen == {"host": "127.0.0.1", "request": ("GET", "/health")}


def test_health_fixture_redirect_is_explicit_and_preserves_original_url(monkeypatch, tmp_path: Path):
    import wrench_harness.core as core

    seen = {}

    class Response:
        status = 200

        def read(self, limit):
            return b'{"fixture":true}'

    class Connection:
        def __init__(self, host, port, timeout):
            seen["host"] = host
            seen["port"] = port
            self.sock = self

        def connect(self):
            return None

        def settimeout(self, value):
            return None

        def request(self, method, path, headers):
            seen["request"] = (method, path)

        def getresponse(self):
            return Response()

        def close(self):
            return None

    monkeypatch.setenv("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL", "http://127.0.0.1:28907")
    monkeypatch.setattr(core.http.client, "HTTPConnection", Connection)
    result = execute_proposal(
        proposal(
            "health_read",
            url="http://localhost:4000/health",
            timeout_seconds=3,
            max_bytes=4096,
        ),
        tmp_path,
    )
    assert result["status"] == "accepted"
    assert result["observation"]["url"] == "http://localhost:4000/health"
    assert result["observation"]["transport_url"] == "http://127.0.0.1:28907/health"
    assert seen == {"host": "127.0.0.1", "port": 28907, "request": ("GET", "/health")}


def test_invalid_health_fixture_configuration_keeps_production_transport(monkeypatch, tmp_path: Path):
    import wrench_harness.core as core

    seen = {}

    class Response:
        status = 200

        def read(self, limit):
            return b"ok"

    class Connection:
        def __init__(self, host, port, timeout):
            seen["host"] = host
            seen["port"] = port
            self.sock = self

        def connect(self):
            return None

        def settimeout(self, value):
            return None

        def request(self, method, path, headers):
            seen["request"] = (method, path)

        def getresponse(self):
            return Response()

        def close(self):
            return None

    monkeypatch.setenv("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL", "https://external.invalid")
    monkeypatch.setattr(core.http.client, "HTTPConnection", Connection)
    result = execute_proposal(
        proposal("health_read", url="http://localhost:4000/health", timeout_seconds=3, max_bytes=4096),
        tmp_path,
    )
    assert result["status"] == "accepted"
    assert "transport_url" not in result["observation"]
    assert seen == {"host": "127.0.0.1", "port": 4000, "request": ("GET", "/health")}

def test_pruning_source_rejects_packed_ftw(tmp_path: Path):
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_5_moe",
                "architectures": ["Qwen3_5MoeForConditionalGeneration"],
                "text_config": {
                    "num_hidden_layers": 40,
                    "hidden_size": 2048,
                    "num_experts": 256,
                    "num_experts_per_tok": 8,
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "hf_quant_config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "freetoken-00000.ftw").write_bytes(b"packed")
    result = validate_pruning_source(tmp_path)
    assert result["eligible"] is False
    assert "packed_ftw_not_sliceable" in result["rejection_reasons"]
    assert "safetensors_index_missing" in result["rejection_reasons"]


def test_checkpoint_inspection_distinguishes_unquantized_safetensors(tmp_path: Path):
    (tmp_path / "config.json").write_text(
        json.dumps({"model_type": "qwen3_5_moe", "text_config": {"num_hidden_layers": 40}}),
        encoding="utf-8",
    )
    (tmp_path / "model.safetensors.index.json").write_text(
        json.dumps({"metadata": {"total_size": 4}, "weight_map": {"layer.weight": "model-00001-of-00001.safetensors"}}),
        encoding="utf-8",
    )
    (tmp_path / "model-00001-of-00001.safetensors").write_bytes(b"1234")
    receipt = inspect_checkpoint(tmp_path, hash_weights=False)
    assert receipt["pruning_assessment"] == {
        "source_is_packed_quantized": False,
        "safe_for_structural_tensor_slicing": True,
        "reason": "Unquantized safetensors with a local tensor index are eligible for structural slicing after architecture checks.",
        "required_source": "verified unquantized checkpoint with matching architecture and license",
    }


def test_qwen_pruned_size_estimate_uses_headers_only(tmp_path: Path):
    (tmp_path / "config.json").write_text(
        json.dumps({"text_config": {"num_hidden_layers": 1, "num_experts": 4, "num_experts_per_tok": 2}}),
        encoding="utf-8",
    )
    tensors = {
        "model.language_model.layers.0.mlp.experts.gate_up_proj": ([4, 2, 3], "BF16"),
        "model.language_model.layers.0.mlp.experts.down_proj": ([4, 3, 2], "BF16"),
        "model.language_model.layers.0.mlp.gate.weight": ([4, 5], "BF16"),
        "model.language_model.layers.0.input_layernorm.weight": ([10], "BF16"),
    }
    header = {
        name: {"dtype": dtype, "shape": shape, "data_offsets": [0, 0]}
        for name, (shape, dtype) in tensors.items()
    }
    encoded = json.dumps(header, separators=(",", ":")).encode("utf-8")
    shard = tmp_path / "model-00001-of-00001.safetensors"
    shard.write_bytes(struct.pack("<Q", len(encoded)) + encoded)
    (tmp_path / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "metadata": {"total_size": 156},
                "weight_map": {name: shard.name for name in tensors},
            }
        ),
        encoding="utf-8",
    )
    report = analyze_checkpoint(tmp_path, [2])
    scenario = report["scenarios"][0]
    assert report["evidence_scope"] == "safetensors_headers_only_no_tensor_payload_loaded"
    assert report["tensor_inventory"]["tensor_elements"] == 78
    assert scenario["estimated_tensor_elements"] == 44


def test_streaming_pruner_slices_experts_and_router_rows(tmp_path: Path):
    import torch
    from safetensors.torch import load_file, save_file

    source = tmp_path / "source"
    source.mkdir()
    (source / "config.json").write_text(
        json.dumps({"architectures": ["Qwen3_5MoeForConditionalGeneration"], "text_config": {"num_experts": 4, "num_experts_per_tok": 2}}),
        encoding="utf-8",
    )
    tensors = {
        "model.language_model.layers.0.mlp.experts.gate_up_proj": torch.arange(24, dtype=torch.bfloat16).reshape(4, 2, 3),
        "model.language_model.layers.0.mlp.experts.down_proj": torch.arange(24, dtype=torch.bfloat16).reshape(4, 3, 2),
        "model.language_model.layers.0.mlp.gate.weight": torch.arange(20, dtype=torch.bfloat16).reshape(4, 5),
        "model.language_model.layers.0.input_layernorm.weight": torch.arange(10, dtype=torch.bfloat16),
    }
    shard = source / "model-00001-of-00001.safetensors"
    save_file(tensors, str(shard))
    (source / "model.safetensors.index.json").write_text(
        json.dumps({"metadata": {"total_size": sum(t.numel() * t.element_size() for t in tensors.values())}, "weight_map": {name: shard.name for name in tensors}}),
        encoding="utf-8",
    )
    output = tmp_path / "output"
    receipt = prune_checkpoint(source, output, [0, 2], chunk_limit_bytes=1024)
    assert receipt["status"] == "EXPERIMENTAL_UNCALIBRATED"
    assert receipt["sliced_tensor_count"] == 3
    assert json.loads((output / "config.json").read_text(encoding="utf-8"))["text_config"]["num_experts"] == 2
    merged = {}
    for path in output.glob("*.safetensors"):
        merged.update(load_file(str(path)))
    assert merged["model.language_model.layers.0.mlp.experts.gate_up_proj"].shape == (2, 2, 3)
    assert merged["model.language_model.layers.0.mlp.gate.weight"].shape == (2, 5)
    assert merged["model.language_model.layers.0.input_layernorm.weight"].shape == (10,)


def test_streaming_pruner_applies_per_route_selection(tmp_path: Path):
    import torch
    from safetensors.torch import load_file, save_file

    source = tmp_path / "source"
    source.mkdir()
    (source / "config.json").write_text(
        json.dumps({"architectures": ["Qwen3_5MoeForConditionalGeneration"], "text_config": {"num_experts": 4, "num_experts_per_tok": 2}}),
        encoding="utf-8",
    )
    tensors = {
        "model.language_model.layers.0.mlp.experts.gate_up_proj": torch.arange(24, dtype=torch.bfloat16).reshape(4, 2, 3),
        "model.language_model.layers.0.mlp.experts.down_proj": torch.arange(24, dtype=torch.bfloat16).reshape(4, 3, 2),
        "model.language_model.layers.0.mlp.gate.weight": torch.arange(20, dtype=torch.bfloat16).reshape(4, 5),
    }
    shard = source / "model-00001-of-00001.safetensors"
    save_file(tensors, str(shard))
    (source / "model.safetensors.index.json").write_text(
        json.dumps({"metadata": {"total_size": sum(t.numel() * t.element_size() for t in tensors.values())}, "weight_map": {name: shard.name for name in tensors}}),
        encoding="utf-8",
    )
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({
        "status": "PASS_ROUTER_SELECTION_DERIVED",
        "source_num_experts": 4,
        "routes": {"model.layers.0.mlp": [1, 3]},
        "default_indices": [0, 2],
    }), encoding="utf-8")
    output = tmp_path / "output"
    receipt = prune_checkpoint(source, output, selection_receipt=selection, chunk_limit_bytes=1024)
    assert receipt["selection_rule"] == "per-route router telemetry"
    merged = {}
    for path in output.glob("*.safetensors"):
        merged.update(load_file(str(path)))
    assert merged["model.language_model.layers.0.mlp.gate.weight"][:, 0].tolist() == [5.0, 15.0]


def test_model_output_requires_exact_json_object(tmp_path: Path):
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    valid = '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}'
    result = execute_model_output(valid, tmp_path)
    assert result["status"] == "accepted"
    assert result["model_output_validated"] is True

    for invalid, reason in (
        ("```json\n" + valid + "\n```", "model_output_invalid_json"),
        ("Here is the proposal: " + valid, "model_output_invalid_json"),
        (
            '{"schema":"wrench.proposal.v1","schema":"wrench.proposal.v1",'
            '"action":"read_file","path":"README.md","max_bytes":4096}',
            "model_output_invalid_json",
        ),
        (
            '{"schema":"wrench.proposal.v1","action":"read_file",'
            '"path":"README.md","path":"outside.txt","max_bytes":4096}',
            "model_output_invalid_json",
        ),
        (
            '{"schema":"wrench.proposal.v1","action":"read_file",'
            '"path":"README.md","max_bytes":4096,"limits":{"max_bytes":1,"max_bytes":2}}',
            "model_output_invalid_json",
        ),
        ("[1, 2, 3]", "model_output_not_object"),
        ("not json", "model_output_invalid_json"),
    ):
        rejected = execute_model_output(invalid, tmp_path)
        assert rejected["fallback_reason"] == reason

    regex_literal = execute_model_output(
        '{"schema":"wrench.proposal.v1","action":"literal_search","root":"docs","literal":"^Status","max_matches":5}',
        tmp_path,
        request_prompt="Use a regex search for '^Status' in docs.",
    )
    assert regex_literal == {"status": "abstain", "fallback_reason": "literal_mode_required"}

    destructive_rewrite = execute_model_output(
        '{"schema":"wrench.proposal.v1","action":"git_read_status","repo_root":"."}',
        tmp_path,
        request_prompt="Remove the repository permanently.",
    )
    assert destructive_rewrite == {"status": "abstain", "fallback_reason": "action_not_allowlisted"}

    traversal_rewrite = execute_model_output(
        '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":1024}',
        tmp_path,
        request_prompt="Read ..\\README.md while preserving the safety boundary.",
    )
    assert traversal_rewrite == {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}


def test_local_qwen_adapter_is_allowlisted_and_parser_gated(tmp_path: Path):
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    expected = '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}'

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            request_body = self.rfile.read(length)
            json.loads(request_body)
            payload = {
                "model": "test-qwen",
                "choices": [{"message": {"content": expected}}],
                "usage": {"total_tokens": 9},
                "wrench": {
                    "request_id": "fixture-request-id",
                    "client_workflow_id": self.headers["X-Wrench-Workflow-ID"],
                    "client_attempt": int(self.headers["X-Wrench-Client-Attempt"]),
                    "request_body_sha256": hashlib.sha256(request_body).hexdigest(),
                    "backend": "embedded-mechanical",
                    "mechanical_fast_path": True,
                    "model_calls": 0,
                    "elapsed_ms": 1.25,
                },
            }
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("X-Wrench-Request-ID", "fixture-request-id")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        result = execute_local_qwen(endpoint, "test-qwen", [{"role": "user", "content": "proposal"}], str(tmp_path))
        assert result["status"] == "accepted"
        assert result["usage"]["total_tokens"] == 9
        assert result["mechanical_fast_path"] is True
        assert result["model_calls"] == 0
        assert result["backend"] == "embedded-mechanical"

        traced = execute_local_qwen(
            endpoint,
            "test-qwen",
            [{"role": "user", "content": "proposal"}],
            str(tmp_path),
            capture_trace=True,
        )
        assert traced["raw_model_output"] == expected
        assert traced["parsed_proposal"] == json.loads(expected)
        assert traced["request_parameters"] == {"temperature": 0, "max_tokens": 256, "enable_thinking": False}

        remote = execute_local_qwen("https://example.com/v1/chat/completions", "test-qwen", [], str(tmp_path))
        assert remote["fallback_reason"] == "qwen_endpoint_not_allowlisted"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_local_qwen_adapter_preserves_regex_intent(tmp_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            json.loads(self.rfile.read(length))
            proposal = '{"schema":"wrench.proposal.v1","action":"literal_search","root":"docs","literal":"^Status","max_matches":5}'
            payload = {"model": "test-qwen", "choices": [{"message": {"content": proposal}}]}
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        result = execute_local_qwen(
            endpoint,
            "test-qwen",
            [{"role": "user", "content": "Use a regex search for '^Status' in docs."}],
            str(tmp_path),
        )
        assert result["status"] == "abstain"
        assert result["fallback_reason"] == "literal_mode_required"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_local_qwen_adapter_preserves_destructive_intent(tmp_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            json.loads(self.rfile.read(length))
            proposal = '{"schema":"wrench.proposal.v1","action":"git_read_status","repo_root":"."}'
            payload = {"model": "test-qwen", "choices": [{"message": {"content": proposal}}]}
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        result = execute_local_qwen(
            endpoint,
            "test-qwen",
            [{"role": "user", "content": "Remove the repository permanently."}],
            str(tmp_path),
        )
        assert result["status"] == "abstain"
        assert result["fallback_reason"] == "action_not_allowlisted"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_router_attempt_ceiling_circuit_bypass_and_hash_bound_reset():
    router = ProposalRouter(RouterConfig(max_attempts=2, failure_threshold=2))

    def rejected():
        return {"status": "abstain", "fallback_reason": "model_output_invalid_json"}

    first = router.run(rejected)
    second = router.run(rejected)
    assert first["status"] == "abstain"
    assert second["circuit_opened"] is True
    assert router.run(lambda: {"status": "accepted"})["fallback_reason"] == "router_disabled"

    assert router.reset("wrong-hash") is False
    assert router.reset(router.config.config_hash) is True
    assert router.run(lambda: {"status": "accepted"})["status"] == "accepted"
    router.bypass("maintenance")
    assert router.run(lambda: {"status": "accepted"})["fallback_reason"] == "router_disabled"


def test_router_state_persists_and_rejects_hash_mismatch(tmp_path: Path):
    config = RouterConfig(max_attempts=3, failure_threshold=2)
    router = ProposalRouter(config)
    router.run(lambda: {"status": "abstain", "fallback_reason": "test"})
    state_path = tmp_path / "router-state.json"
    saved = save_router_state(router, state_path)
    assert saved["schema"] == "wrench.router-state.v1"
    restored = load_router_state(config, state_path)
    assert restored.status()["attempts"] == 1
    assert restored.status()["failures"] == 1

    try:
        load_router_state(RouterConfig(max_attempts=4, failure_threshold=2), state_path)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("hash-mismatched state was accepted")


def test_router_cancellation_and_events():
    events = []
    router = ProposalRouter(RouterConfig(max_attempts=2, failure_threshold=1), event_sink=events.append)
    token = CancellationToken()
    token.cancel()
    cancelled = router.run(lambda: {"status": "accepted"}, token)
    assert cancelled["fallback_reason"] == "cancelled"
    assert events == [{"event": "cancelled", "stage": "before_attempt"}]

    result = router.run(lambda: {"status": "abstain", "fallback_reason": "test"})
    assert result["circuit_opened"] is True
    assert {event["event"] for event in events} == {"cancelled", "circuit_opened"}
    assert router.reset(router.config.config_hash) is True
    router.bypass("test")
    assert [event["event"] for event in events][-2:] == ["reset", "bypass"]
