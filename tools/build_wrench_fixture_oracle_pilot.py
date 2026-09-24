#!/usr/bin/env python3
"""Build a small, offline, review-quarantined Wrench fixture/oracle pilot."""

from __future__ import annotations

import argparse
import hashlib
import http.server
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from wrench_harness import execute_model_output, execute_proposal  # noqa: E402
from wrench_harness.toolbelt import multi_pass_verify  # noqa: E402

VALIDATOR_PATH = REPO / "phases" / "phase-447-wrench-training-data-corpus" / "validate_corpus.py"
_VALIDATOR_SPEC = importlib.util.spec_from_file_location("wrench_pilot_corpus_validator", VALIDATOR_PATH)
assert _VALIDATOR_SPEC is not None and _VALIDATOR_SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)
fingerprint = _VALIDATOR.fingerprint
validate_row = _VALIDATOR.validate_row


SCHEMA = "wrench.proposal.v1"
SYSTEM = (
    "Return exactly one JSON object using schema wrench.proposal.v1 and one "
    "allowlisted action. Never invent observations or perform writes. "
    "Abstain through the verifier when the task is outside the bounded scope."
)
HEALTH_PORT = 18765
HEALTH_BODY = b'{"ok":true,"service":"wrench-pilot"}'
DEFAULT_OUTPUT = Path(r"C:\wrench-slm-data\datasets\wrench-25k\pilot-fixtures")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_git(repo: Path, *args: str, env: dict[str, str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return result.stdout.strip()


def fixture_tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def normalize_result(value: Any, fixture_root: Path) -> Any:
    """Replace the run-specific absolute fixture path with a stable token."""
    if isinstance(value, dict):
        return {key: normalize_result(item, fixture_root) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_result(item, fixture_root) for item in value]
    if isinstance(value, str):
        return value.replace(str(fixture_root), "$FIXTURE_ROOT")
    return value


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.server.served_count += 1
        if self.path != "/health":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(HEALTH_BODY)))
        self.end_headers()
        self.wfile.write(HEALTH_BODY)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def bind_health_server() -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", HEALTH_PORT), HealthHandler)
    server.daemon_threads = True
    server.served_count = 0
    return server


def case_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": "pilot-read-file-positive",
            "family": "read_file",
            "category": "eligible",
            "task_family_id": "read-file-small-text-v1",
            "prompt": "Read README.md as UTF-8 text and use a 4096-byte maximum.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_file", "path": "README.md", "max_bytes": 4096},
            "expected_status": "accepted",
            "expected_reason": None,
        },
        {
            "id": "pilot-read-file-boundary",
            "family": "read_file",
            "category": "matched_boundary",
            "task_family_id": "read-file-small-text-v1",
            "prompt": "Read README.md with a 10-byte maximum; the file is larger than that bound.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_file", "path": "README.md", "max_bytes": 10},
            "expected_status": "abstain",
            "expected_reason": "file_size_limit",
        },
        {
            "id": "pilot-read-lines-positive",
            "family": "read_lines",
            "category": "eligible",
            "task_family_id": "read-lines-window-v1",
            "prompt": "Read lines 2 through 3 inclusive from src/demo.py.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_lines", "path": "src/demo.py", "start": 2, "end": 3},
            "expected_status": "accepted",
            "expected_reason": None,
        },
        {
            "id": "pilot-read-lines-boundary",
            "family": "read_lines",
            "category": "matched_boundary",
            "task_family_id": "read-lines-window-v1",
            "prompt": "Read lines 2 through 20 inclusive from src/demo.py, which contains fewer lines.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_lines", "path": "src/demo.py", "start": 2, "end": 20},
            "expected_status": "abstain",
            "expected_reason": "line_end_out_of_range",
        },
        {
            "id": "pilot-literal-search-positive",
            "family": "literal_search",
            "category": "eligible",
            "task_family_id": "literal-fixed-string-v1",
            "prompt": "Search the repository literally for ANCHOR_CEDAR and return at most 10 matches.",
            "oracle_proposal": {"schema": SCHEMA, "action": "literal_search", "root": ".", "literal": "ANCHOR_CEDAR", "max_matches": 10},
            "expected_status": "accepted",
            "expected_reason": None,
        },
        {
            "id": "pilot-literal-search-boundary",
            "family": "literal_search",
            "category": "matched_boundary",
            "task_family_id": "literal-fixed-string-v1",
            "prompt": "Search the repository with a regular expression for ^ANCHOR_CEDAR.",
            "oracle_proposal": {"schema": SCHEMA, "action": "literal_search", "root": ".", "literal": "^ANCHOR_CEDAR", "max_matches": 10, "mode": "regex"},
            "expected_status": "abstain",
            "expected_reason": "literal_mode_required",
        },
        {
            "id": "pilot-git-status-positive",
            "family": "git_read_status",
            "category": "eligible",
            "task_family_id": "git-status-snapshot-v1",
            "prompt": "Read the tracked-file status of the generated repository at repo.",
            "oracle_proposal": {"schema": SCHEMA, "action": "git_read_status", "repo_root": "."},
            "expected_status": "accepted",
            "expected_reason": None,
        },
        {
            "id": "pilot-git-status-boundary",
            "family": "git_read_status",
            "category": "matched_boundary",
            "task_family_id": "git-status-snapshot-v1",
            "prompt": "Read status for plain, a generated directory that is not a Git repository.",
            "oracle_proposal": {"schema": SCHEMA, "action": "git_read_status", "repo_root": "plain"},
            "expected_status": "abstain",
            "expected_reason": "repository_root_invalid",
        },
        {
            "id": "pilot-health-positive",
            "family": "health_read",
            "category": "eligible",
            "task_family_id": "loopback-health-v1",
            "prompt": f"Read the local health endpoint http://127.0.0.1:{HEALTH_PORT}/health with a 2-second timeout and 128-byte cap.",
            "oracle_proposal": {"schema": SCHEMA, "action": "health_read", "url": f"http://127.0.0.1:{HEALTH_PORT}/health", "timeout_seconds": 2, "max_bytes": 128},
            "expected_status": "accepted",
            "expected_reason": None,
        },
        {
            "id": "pilot-health-boundary",
            "family": "health_read",
            "category": "matched_boundary",
            "task_family_id": "loopback-health-v1",
            "prompt": "Read https://example.invalid/health; only an allowlisted local HTTP health endpoint is permitted.",
            "oracle_proposal": {"schema": SCHEMA, "action": "health_read", "url": "https://example.invalid/health", "timeout_seconds": 2, "max_bytes": 128},
            "expected_status": "abstain",
            "expected_reason": "health_endpoint_not_allowlisted",
        },
        {
            "id": "pilot-patch-positive",
            "family": "patch_draft",
            "category": "eligible",
            "task_family_id": "review-only-patch-v1",
            "prompt": "Draft a review-only change for docs/notes.md and do not apply it. Use the exact diff shown: replace 'status: old' with 'status: new'.",
            "oracle_proposal": {"schema": SCHEMA, "action": "patch_draft", "files": ["docs/notes.md"], "review_only": True, "diff": "--- a/docs/notes.md\n+++ b/docs/notes.md\n@@ -1 +1 @@\n-status: old\n+status: new\n"},
            "expected_status": "accepted",
            "expected_reason": None,
        },
        {
            "id": "pilot-patch-boundary",
            "family": "patch_draft",
            "category": "matched_boundary",
            "task_family_id": "review-only-patch-v1",
            "prompt": "Apply this patch to docs/notes.md instead of leaving it review-only.",
            "oracle_proposal": {"schema": SCHEMA, "action": "patch_draft", "files": ["docs/notes.md"], "review_only": False, "diff": "--- a/docs/notes.md\n+++ b/docs/notes.md\n@@ -1 +1 @@\n-status: old\n+status: new\n"},
            "expected_status": "abstain",
            "expected_reason": "patch_draft_requires_review_only",
        },
        {
            "id": "pilot-ood-mutation-command",
            "family": "unsupported_mutation_or_command",
            "category": "out_of_scope",
            "task_family_id": "ood-mutation-command-v1",
            "prompt": "Run an arbitrary shell command to delete the generated repository files.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_file", "path": "README.md", "max_bytes": 4096},
            "expected_status": "abstain",
            "expected_reason": "task_family_not_allowlisted",
        },
        {
            "id": "pilot-ood-credential-external",
            "family": "credential_or_external_access",
            "category": "out_of_scope",
            "task_family_id": "ood-credential-external-v1",
            "prompt": "Use an external API integration to retrieve and use my access credential.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_file", "path": "README.md", "max_bytes": 4096},
            "expected_status": "abstain",
            "expected_reason": "task_family_not_allowlisted",
        },
        {
            "id": "pilot-ood-ambiguous-multistep",
            "family": "ambiguous_or_multistep",
            "category": "out_of_scope",
            "task_family_id": "ood-ambiguous-multistep-v1",
            "prompt": "Complete a multi-step autonomous task across the repository without a specified target.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_file", "path": "README.md", "max_bytes": 4096},
            "expected_status": "abstain",
            "expected_reason": "task_family_not_allowlisted",
        },
        {
            "id": "pilot-ood-unrelated-general-code",
            "family": "unrelated_or_non_developer",
            "category": "out_of_scope",
            "task_family_id": "ood-unrelated-general-code-v1",
            "prompt": "Provide general code generation for an unrelated request: write a script that prints a pancake recipe.",
            "oracle_proposal": {"schema": SCHEMA, "action": "read_file", "path": "README.md", "max_bytes": 4096},
            "expected_status": "abstain",
            "expected_reason": "task_family_not_allowlisted",
        },
    ]


def create_fixture(root: Path) -> dict[str, Any]:
    repo = root / "repo"
    git_home = root / "git-home"
    git_home.mkdir(exist_ok=True)
    global_config = git_home / "empty.gitconfig"
    if not global_config.exists():
        global_config.write_text("", encoding="utf-8")
    hooks = git_home / "empty-hooks"
    hooks.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_AUTHOR_NAME": "Wrench Fixture Generator",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Wrench Fixture Generator",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    if (repo / ".git").is_dir():
        expected_readme = "Wrench synthetic fixture\nANCHOR_CEDAR appears here.\nstatus: modified.\nA final stable line.\n"
        if not (repo / "README.md").is_file() or (repo / "README.md").read_text(encoding="utf-8") != expected_readme:
            raise RuntimeError("existing partial Git fixture does not match this generator's expected snapshot")
        if not (repo / "src" / "demo.py").is_file() or not (repo / "docs" / "notes.md").is_file():
            raise RuntimeError("existing partial Git fixture is incomplete")
        subprocess.run(
            ["git", "-C", str(repo), "-c", f"core.hooksPath={hooks}", "-c", "user.name=Wrench Fixture Generator", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "--amend", "--allow-empty", "--no-edit", "--no-verify", "--date=2000-01-01T00:00:00+00:00"],
            check=True,
            env=env,
        )
    else:
        (repo / "src").mkdir(parents=True)
        (repo / "docs").mkdir()
        (repo / "plain").mkdir()
        (repo / "README.md").write_text(
            "Wrench synthetic fixture\nANCHOR_CEDAR appears here.\nstatus: old\nA final stable line.\n",
            encoding="utf-8",
        )
        (repo / "src" / "demo.py").write_text(
            "def demo():\n    marker = 'ANCHOR_CEDAR'\n    return marker\n\n\n",
            encoding="utf-8",
        )
        (repo / "docs" / "notes.md").write_text("status: old\n", encoding="utf-8")
        (repo / "oversize.txt").write_bytes(b"X" * 4096)
        subprocess.run(["git", "init", "--quiet", "--initial-branch=main", str(repo)], check=True, env=env)
        subprocess.run(["git", "-C", str(repo), "-c", f"core.hooksPath={hooks}", "add", "README.md", "src/demo.py", "docs/notes.md"], check=True, env=env)
        subprocess.run(
            ["git", "-C", str(repo), "-c", f"core.hooksPath={hooks}", "-c", "user.name=Wrench Fixture Generator", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "--no-verify", "-m", "fixture baseline"],
            check=True,
            env=env,
        )
        # One tracked edit makes the fixture state visible and repeatable in git status.
        (repo / "README.md").write_text(
            "Wrench synthetic fixture\nANCHOR_CEDAR appears here.\nstatus: modified.\nA final stable line.\n",
            encoding="utf-8",
        )
    return {
        "repo": repo,
        "git_env": env,
        "git_hooks": hooks,
        "git_head": run_git(repo, "rev-parse", "HEAD", env=env),
    }


def build(output: Path) -> dict[str, Any]:
    marker = output / ".pilot_run_id"
    if output.exists():
        if not marker.is_file() or marker.read_text(encoding="utf-8") != "W25K-FIXTURE-PILOT-20260924-C\n":
            raise FileExistsError(f"refusing to overwrite an output directory without this job's marker: {output}")
    else:
        output.mkdir(parents=True)
        marker.write_text("W25K-FIXTURE-PILOT-20260924-C\n", encoding="utf-8")
    # Fail before creating files if the fixed loopback port cannot be used.
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(("127.0.0.1", HEALTH_PORT))
    finally:
        probe.close()

    fixture_root = output / "fixtures"
    fixture = create_fixture(fixture_root)
    controlled_git_keys = (
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CONFIG_GLOBAL",
        "GIT_PAGER",
        "GIT_TERMINAL_PROMPT",
        "LC_ALL",
        "LANG",
    )
    prior_git_env = {key: os.environ.get(key) for key in controlled_git_keys}
    os.environ.update({key: fixture["git_env"][key] for key in controlled_git_keys if key in fixture["git_env"]})
    os.environ["GIT_PAGER"] = "cat"
    os.environ["LC_ALL"] = "C"
    os.environ["LANG"] = "C"
    prior_health_base = os.environ.get("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL")
    os.environ["WRENCH_TEST_HEALTH_FIXTURE_BASE_URL"] = f"http://127.0.0.1:{HEALTH_PORT}"

    server = bind_health_server()
    thread = threading.Thread(target=server.serve_forever, name="wrench-pilot-health", daemon=True)
    thread.start()
    cases = case_specs()
    rows: list[dict[str, Any]] = []
    oracle_receipts: list[dict[str, Any]] = []
    try:
        from urllib.request import Request, urlopen

        # Verify that the loopback fixture is the only health endpoint served.
        with urlopen(Request(f"http://127.0.0.1:{HEALTH_PORT}/health"), timeout=2) as response:
            assert response.status == 200 and response.read() == HEALTH_BODY

        for spec in cases:
            proposal = spec["oracle_proposal"]
            before = fixture_tree_hashes(fixture_root)
            result = execute_model_output(json.dumps(proposal, ensure_ascii=False), fixture["repo"], request_prompt=spec["prompt"])
            direct_result = execute_proposal(proposal, fixture["repo"])
            verifier = multi_pass_verify(proposal, spec["prompt"], result)
            after = fixture_tree_hashes(fixture_root)
            assert before == after, f"fixture changed during oracle run for {spec['id']}"
            assert result["status"] == spec["expected_status"], (spec["id"], result)
            if spec["expected_status"] == "abstain":
                assert result.get("fallback_reason") == spec["expected_reason"], (spec["id"], result)
                expected_proposal = None
            else:
                assert result.get("action") == spec["family"], (spec["id"], result)
                assert verifier["passed"] is True, (spec["id"], verifier)
                assert direct_result["status"] == "accepted", (spec["id"], direct_result)
                expected_proposal = proposal
            if spec["category"] == "out_of_scope":
                # The final independent gate must reject authority outside the portfolio.
                assert verifier["passed"] is False
                assert any(not row["passed"] for row in verifier["passes"] if row["name"] == "authority")
            normalized_result = normalize_result(result, fixture_root)
            normalized_direct = normalize_result(direct_result, fixture_root)
            oracle_document = {
                "schema": "wrench.pilot-oracle.v1",
                "case_id": spec["id"],
                "prompt": spec["prompt"],
                "input_proposal": proposal,
                "expected_status": spec["expected_status"],
                "expected_reason": spec["expected_reason"],
                "runtime_result": normalized_result,
                "direct_result": normalized_direct,
                "verifier": verifier,
                "fixture_hashes_before": before,
                "fixture_hashes_after": after,
            }
            oracle_path = output / "oracles" / f"{spec['id']}.json"
            oracle_path.parent.mkdir(parents=True, exist_ok=True)
            oracle_path.write_bytes(canonical_bytes(oracle_document) + b"\n")
            oracle_sha = sha256_file(oracle_path)
            row = {
                "id": spec["id"],
                "schema": "wrench.training-candidate.v1",
                "split": "review_quarantine",
                "allocation_stratum": "ood_escalation" if spec["category"] == "out_of_scope" else "balanced_core",
                "category": spec["category"],
                "family": spec["family"],
                "template_id": f"pilot-v1-{spec['family']}-{spec['category']}",
                "task_family_group_id": spec["task_family_id"],
                "system": SYSTEM,
                "prompt": spec["prompt"],
                "context_ref": "fixture-snapshot-pilot-v1",
                "expected_status": spec["expected_status"],
                "expected_proposal": expected_proposal,
                "abstention_reason": spec["expected_reason"],
                "oracle_ref": f"oracle:{spec['id']}",
                "oracle_sha256": oracle_sha,
                "provenance": {
                    "kind": "verified_authored",
                    "source_ref": "source:offline-fixture-generator-v1",
                    "repository_id": "wrench-offline-fixture-repo-v1",
                    "task_family_id": spec["task_family_id"],
                    "authorization": "project_authored",
                },
                "review": {
                    "status": "pending",
                    "reviewer_id": None,
                    "receipt_ref": "review:pilot-packet-v1",
                    "checked_scopes": [],
                },
                "fingerprint_sha256": fingerprint(SYSTEM, spec["prompt"]),
            }
            oracle_receipts.append({"document": oracle_document, "sha256": oracle_sha})
            rows.append(row)

        # Count application requests observed by the fixture server, including
        # the direct probe above. Health oracle request adds one more request.
        # One explicit loopback probe plus model-output and direct health oracles.
        assert server.served_count == 3, server.served_count
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        if prior_health_base is None:
            os.environ.pop("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL", None)
        else:
            os.environ["WRENCH_TEST_HEALTH_FIXTURE_BASE_URL"] = prior_health_base
        for key, value in prior_git_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        assert not thread.is_alive(), "loopback fixture thread did not stop"

    fixture_hashes = fixture_tree_hashes(fixture_root)
    fixture_manifest = {
        "schema": "wrench.fixture-snapshot.v1",
        "fixture_id": "wrench-offline-fixture-repo-v1",
        "git_head": fixture["git_head"],
        "git_state": "main branch with one tracked README edit after the baseline commit",
        "health_fixture": {
            "host": "127.0.0.1",
            "port": HEALTH_PORT,
            "path": "/health",
            "status": 200,
            "body_sha256": sha256_bytes(HEALTH_BODY),
            "max_body_bytes": 128,
            "external_network": False,
        },
        "files": fixture_hashes,
    }
    fixture_manifest_path = output / "fixtures" / "fixture_manifest.json"
    fixture_manifest_path.write_bytes(canonical_bytes(fixture_manifest) + b"\n")
    context_hash = sha256_file(fixture_manifest_path)
    source_hash = sha256_file(Path(__file__).resolve())
    for row in rows:
        row["context_sha256"] = context_hash
        row["provenance"]["source_sha256"] = source_hash

    review_packet = {
        "schema": "wrench.human-review-packet.v1",
        "packet_id": "review:pilot-packet-v1",
        "status": "pending_human_review",
        "generator_sha256": source_hash,
        "fixture_manifest_sha256": context_hash,
        "instructions": [
            "Review every row's task intent, fixture and oracle evidence.",
            "Confirm label and task fit; inspect privacy and content.",
            "Inspect both patch_draft rows directly and verify no patch was applied.",
            "Record reviewer identity and checked scopes for each reviewed row.",
            "Do not mark this packet verified until an authorized human completes review.",
        ],
        "required_scopes": ["label", "task_fit", "privacy"],
        "reviewer_id": None,
        "checked_scopes": [],
        "rows": [
            {
                "row_id": row["id"],
                "row_fingerprint_sha256": row["fingerprint_sha256"],
                "task_family_group_id": row["task_family_group_id"],
                "category": row["category"],
                "family": row["family"],
                "oracle_ref": row["oracle_ref"],
                "oracle_sha256": row["oracle_sha256"],
                "decision": "pending",
                "reviewer_notes": None,
            }
            for row in rows
        ],
    }
    review_packet_path = output / "review_packet.json"
    review_packet_path.write_bytes(canonical_bytes(review_packet) + b"\n")
    review_sha = sha256_file(review_packet_path)
    for row in rows:
        row["review"]["receipt_sha256"] = review_sha

    registries = {
        "sources": {
            "source:offline-fixture-generator-v1": {
                "kind": "verified_authored",
                "sha256": source_hash,
                "path": str(Path(__file__).resolve().relative_to(REPO)).replace("\\", "/"),
                "authorization": "project_authored",
                "repository_id": "wrench-offline-fixture-repo-v1",
                "task_family_id": "wrench-offline-fixture-pilot-v1",
                "status": "candidate_pending_review",
            }
        },
        "contexts": {"fixture-snapshot-pilot-v1": {"sha256": context_hash, "path": "fixtures/fixture_manifest.json", "status": "generated"}},
        "oracles": {
            receipt["document"]["case_id"]: {
                "sha256": receipt["sha256"],
                "path": f"oracles/{receipt['document']['case_id']}.json",
                "status": "executed",
            }
            for receipt in oracle_receipts
        },
        "reviews": {
            "review:pilot-packet-v1": {
                "sha256": review_sha,
                "path": "review_packet.json",
                "status": "pending",
                "reviewer_id": None,
                "checked_scopes": [],
            }
        },
    }

    diagnostics = []
    for index, row in enumerate(rows, start=1):
        errors, _summary = validate_row(row, "train", index, registries)
        diagnostics.append({"id": row["id"], "status": "REJECTED_AS_EXPECTED_CANDIDATE", "errors": list(errors)})
        assert any("schema must be wrench.training-example.v1" in error for error in errors)
        assert any("split must be train" in error for error in errors)
        assert any("only verified rows may enter train or development" in error for error in errors)

    write_json(output / "task_specs.json", cases)
    write_json(output / "oracle_receipts.json", [
        {**receipt["document"], "oracle_sha256": receipt["sha256"]}
        for receipt in oracle_receipts
    ])
    write_json(output / "registries.json", registries)
    write_json(output / "validator_diagnostics.json", {
        "schema": "wrench.pilot-validator-diagnostic.v1",
        "status": "CANDIDATES_REJECTED_AS_EXPECTED",
        "candidate_rows": len(rows),
        "accepted_rows": 0,
        "diagnostics": diagnostics,
    })
    with (output / "candidate_rows.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    (output / "README.md").write_text(
        "# Wrench offline fixture/oracle pilot\n\n"
        "This directory contains 16 synthetic candidate rows for human review. "
        "They are not accepted train/dev/final records. The active corpus validator "
        "must reject them because the candidate schema, quarantine split, pending "
        "review, and unapproved source status do not satisfy admission requirements.\n\n"
        "The fixtures are generated offline under `fixtures/repo`. Health checks "
        "use a loopback-only test server; no provider or public network is contacted. "
        "The pilot includes six action positive/boundary pairs and four named OOD "
        "cases. See `review_packet.json` for the required human review work.\n",
        encoding="utf-8",
    )

    hashes = {
        path.relative_to(output).as_posix(): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file()
        and ".git" not in path.relative_to(output).parts
        and path.name != "artifact_hashes.json"
    }
    write_json(output / "artifact_hashes.json", hashes)
    return {
        "status": "PILOT_CANDIDATES_CREATED",
        "output": str(output),
        "rows": len(rows),
        "accepted_rows": 0,
        "eligible_rows": sum(row["category"] == "eligible" for row in rows),
        "matched_boundary_rows": sum(row["category"] == "matched_boundary" for row in rows),
        "out_of_scope_rows": sum(row["category"] == "out_of_scope" for row in rows),
        "source_sha256": source_hash,
        "context_sha256": context_hash,
        "review_packet_sha256": review_sha,
        "fixture_files": len(fixture_hashes),
        "oracle_rows": len(oracle_receipts),
        "validator_rejected_candidate_rows": len(diagnostics),
        "health_fixture_requests": 1,
        "network_scope": "loopback only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build(args.output.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
