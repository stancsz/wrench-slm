from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVED_ROOT = Path(r"C:\wrench-slm-data").resolve()
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "local_context_integration_screen_01.json"
PROTOCOL_PATH = REPO_ROOT / "docs" / "evals" / "wrench-local-acceptability" / "local-context-integration-screen-01-protocol.md"
PIPELINE_PATH = REPO_ROOT / "src" / "wrench_harness" / "e0_context_pipeline.py"
EXPECTED_PARENT_HEAD = "5a0d67f5f5bc94d8e0c5886bf0ba41b1e87150a3"
EXPECTED_JOB_ID = "NS-E0-CTX-SCREEN-20260926"
EXPECTED_NONCE = "E0CS-91B6"
EXPECTED_OUTPUT = APPROVED_ROOT / "artifacts" / "wrench-local-acceptability" / "local-context-integration-screen-01.json"
EXPECTED_WORK_ROOT = APPROVED_ROOT / "artifacts" / "wrench-local-acceptability" / "tmp" / "local-context-integration-screen-01"
EXPOSURE_MARKER = APPROVED_ROOT / "artifacts" / "wrench-local-acceptability" / "local-context-integration-screen-01.used"
PROXY_SERIALIZER_ID = "fixture-json-v1"
PROXY_COUNTER_ID = "fixture-character-count-v1"


class ScreenError(ValueError):
    pass


def _sha256(path: Path) -> str:
    # Pin text identities consistently across Windows CRLF worktrees and the
    # LF blobs stored in Git.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _is_beneath(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _git_head() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise ScreenError("git_head_unavailable")
    return proc.stdout.strip()


def _git_parent() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD^"], cwd=REPO_ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise ScreenError("git_parent_unavailable")
    return proc.stdout.strip()


def _git_dirty() -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise ScreenError("git_status_unavailable")
    return bool(proc.stdout.strip())


def _source_evidence_id(snapshot_sha256: str, path: str, content_sha256: str) -> str:
    encoded = _canonical_json([snapshot_sha256, path, content_sha256]).encode("utf-8")
    return "source-" + hashlib.sha256(encoded).hexdigest()


def _check_expected(result: Any, case: dict[str, Any], snapshot_sha256: str) -> dict[str, Any]:
    expected = case["expected"]
    observed: dict[str, Any] = {
        "status": result.status.value,
        "route": result.route,
        "reason": result.reason,
        "prompt_present": result.prompt is not None,
        "prompt_gate_status": result.prompt_gate.status.value if result.prompt_gate else None,
        "retrieval_miss_statuses": [status for _, status in result.retrieval_misses],
        "outcome_receipt_status": result.outcome_receipt.status.value if result.outcome_receipt else None,
        "outcome_receipt_present": result.outcome_receipt is not None,
    }
    for key in (
        "status", "route", "reason", "prompt_present", "prompt_gate_status",
        "retrieval_miss_statuses", "outcome_receipt_status", "outcome_receipt_present",
    ):
        if key in expected and observed[key] != expected[key]:
            raise ScreenError(f"{case['case_id']}:oracle_mismatch:{key}")

    if "required_evidence_reason" in expected:
        reasons = list(result.prompt_gate.required_evidence_reasons) if result.prompt_gate else []
        if not any(reason == expected["required_evidence_reason"] for _, reason in reasons):
            raise ScreenError(f"{case['case_id']}:oracle_mismatch:required_evidence_reason")

    source_check = expected.get("source_identity")
    if source_check is not None:
        source_path = source_check["path"]
        row = next((item for item in result.sources if item.path == source_path), None)
        if row is None or row.status != "ok":
            raise ScreenError(f"{case['case_id']}:required_source_identity_missing")
        if row.content_sha256 != source_check["content_sha256"]:
            raise ScreenError(f"{case['case_id']}:source_content_hash_mismatch")
        if row.evidence_id != _source_evidence_id(snapshot_sha256, row.path, row.content_sha256):
            raise ScreenError(f"{case['case_id']}:source_evidence_id_mismatch")
        if row.evidence_id not in result.selected_evidence_ids:
            raise ScreenError(f"{case['case_id']}:required_evidence_not_selected")
        observed["source_identity"] = {
            "path": row.path,
            "status": row.status,
            "content_sha256": row.content_sha256,
            "evidence_id": row.evidence_id,
            "selected": True,
        }
    if result.outcome_receipt is not None:
        receipt = result.outcome_receipt.receipt
        if receipt is None:
            raise ScreenError(f"{case['case_id']}:outcome_receipt_payload_missing")
        payload = json.loads(receipt.payload_json)
        if payload.get("outcome", {}).get("status") != "unknown":
            raise ScreenError(f"{case['case_id']}:unexpected_task_outcome_claim")
    observed["selected_evidence_count"] = len(result.selected_evidence_ids)
    observed["omitted_evidence_count"] = len(result.omitted_evidence)
    observed["prompt_sha256"] = result.prompt_gate.prompt_sha256 if result.prompt_gate else None
    observed["proxy_character_count"] = result.prompt_gate.exact_token_count if result.prompt_gate else None
    return observed


def _run_case(case: dict[str, Any], common: dict[str, Any], work_root: Path) -> dict[str, Any]:
    from wrench_harness.artifact_store import ArtifactStore
    from wrench_harness.e0_context_pipeline import prepare_e0_context
    from wrench_harness.namespace_registry import NamespaceRegistry
    from wrench_harness.prompt_compiler import materialize_prompt_messages
    from wrench_harness.snapshot import create_snapshot

    case_root = work_root / case["case_id"]
    source_root = case_root / "source"
    source_root.mkdir(parents=True, exist_ok=False)
    try:
        source_files = common["source_files"]
        for entry in source_files:
            relpath = Path(entry["path"])
            if relpath.is_absolute() or ".." in relpath.parts:
                raise ScreenError("fixture_source_path_unsafe")
            target = source_root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry["utf8"].encode("utf-8"))

        snapshot_paths = tuple(case["snapshot_paths"])
        snapshot = create_snapshot(source_root, snapshot_paths)
        mutation = case.get("post_snapshot_mutation")
        if mutation:
            target = source_root / mutation["path"]
            if mutation["operation"] == "delete":
                target.unlink()
            elif mutation["operation"] == "replace_utf8":
                target.write_bytes(mutation["utf8"].encode("utf-8"))
            else:
                raise ScreenError("fixture_mutation_unsupported")

        base_messages = common["base_messages"]
        serializer = lambda messages: _canonical_json(materialize_prompt_messages(messages))
        result = prepare_e0_context(
            source_root=source_root,
            snapshot=snapshot,
            paths=tuple(case["paths"]),
            store=ArtifactStore(case_root / "store"),
            query=case["query"],
            source_order_start=common["source_order_start"],
            context_token_budget=case["context_token_budget"],
            prompt_token_budget=common["prompt_token_budget"],
            namespace_registry=NamespaceRegistry([]),
            schema_lookups=tuple(common["schema_lookups"]),
            base_messages=tuple(base_messages),
            context_position=common["context_position"],
            serializer=serializer,
            tokenizer_counter=lambda value: len(value) if isinstance(value, str) else len(value),
            serializer_id=PROXY_SERIALIZER_ID,
            tokenizer_id=PROXY_COUNTER_ID,
            required_source_paths=tuple(case["required_source_paths"]),
            preserve_source_paths=tuple(case["preserve_source_paths"]),
        )
        observed = _check_expected(result, case, snapshot.snapshot_sha256)
        return {"case_id": case["case_id"], "passed": True, **observed}
    finally:
        if _is_beneath(case_root, work_root) and case_root.exists():
            shutil.rmtree(case_root)


def run_screen(work_root: Path) -> dict[str, Any]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if fixture.get("expected_parent_head") != EXPECTED_PARENT_HEAD or _git_parent() != EXPECTED_PARENT_HEAD:
        raise ScreenError("unexpected_repository_head")
    if _git_dirty():
        raise ScreenError("dirty_source_tree")
    if fixture.get("pipeline_source_sha256") != _sha256(PIPELINE_PATH):
        raise ScreenError("pipeline_source_hash_mismatch")
    common = fixture["common_inputs"]
    results = [_run_case(case, common, work_root) for case in fixture["cases"]]
    return {
        "schema": "wrench.local-context-integration-screen-receipt.v1",
        "screen_id": fixture["screen_id"],
        "job_id": EXPECTED_JOB_ID,
        "nonce": EXPECTED_NONCE,
        "repository_head": _git_head(),
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "pipeline_source_sha256": _sha256(PIPELINE_PATH),
        "fixture_sha256": _sha256(FIXTURE_PATH),
        "case_count": len(results),
        "passed_cases": sum(1 for row in results if row["passed"]),
        "route": "none",
        "model_calls": 0,
        "provider_calls": 0,
        "frontier_token_savings_percent": None,
        "token_counter_id": PROXY_COUNTER_ID,
        "claim_boundary": "synthetic E0 preparation mechanics only; proxy characters are not model tokens",
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="One-shot synthetic E0 context integration screen")
    parser.add_argument("--admit", required=True, help="must be NS-E0-CTX-SCREEN-20260926:E0CS-91B6")
    parser.add_argument("--expected-runner-sha256", required=True)
    parser.add_argument("--expected-fixture-sha256", required=True)
    parser.add_argument("--expected-protocol-sha256", required=True)
    parser.add_argument("--expected-pipeline-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--work-root", required=True)
    args = parser.parse_args()
    if args.admit != f"{EXPECTED_JOB_ID}:{EXPECTED_NONCE}":
        raise SystemExit("admission_token_mismatch")
    for path, expected, label in (
        (Path(__file__), args.expected_runner_sha256, "runner"),
        (FIXTURE_PATH, args.expected_fixture_sha256, "fixture"),
        (PROTOCOL_PATH, args.expected_protocol_sha256, "protocol"),
        (PIPELINE_PATH, args.expected_pipeline_sha256, "pipeline"),
    ):
        if _sha256(path) != expected:
            raise SystemExit(f"{label}_hash_mismatch")
    output = Path(args.output).resolve()
    work_root = Path(args.work_root).resolve()
    if not _is_beneath(output, APPROVED_ROOT) or not _is_beneath(work_root, APPROVED_ROOT):
        raise SystemExit("output_outside_approved_root")
    if output != EXPECTED_OUTPUT.resolve() or work_root != EXPECTED_WORK_ROOT.resolve():
        raise SystemExit("unexpected_output_or_work_root")
    if EXPOSURE_MARKER.exists():
        raise SystemExit("fixture_already_exposed")
    if output.exists() or work_root.exists():
        raise SystemExit("output_or_work_root_already_exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        marker_fd = os.open(EXPOSURE_MARKER, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise SystemExit("fixture_already_exposed")
    with os.fdopen(marker_fd, "w", encoding="utf-8") as marker:
        marker.write(_canonical_json({
            "schema": "wrench.synthetic-fixture-exposure.v1",
            "screen_id": "local-context-integration-screen-01",
            "job_id": EXPECTED_JOB_ID,
            "nonce": EXPECTED_NONCE,
            "runner_sha256": _sha256(Path(__file__).resolve()),
            "fixture_sha256": _sha256(FIXTURE_PATH),
            "protocol_sha256": args.expected_protocol_sha256,
            "pipeline_source_sha256": _sha256(PIPELINE_PATH),
        }) + "\n")
    work_root.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(REPO_ROOT / "src"))
    try:
        receipt = run_screen(work_root)
        receipt["protocol_sha256"] = args.expected_protocol_sha256
        output.write_text(_canonical_json(receipt) + "\n", encoding="utf-8")
    except Exception as exc:
        output.write_text(_canonical_json({
            "schema": "wrench.local-context-integration-screen-receipt.v1",
            "screen_id": "local-context-integration-screen-01",
            "job_id": EXPECTED_JOB_ID,
            "nonce": EXPECTED_NONCE,
            "protocol_sha256": args.expected_protocol_sha256,
            "runner_sha256": _sha256(Path(__file__).resolve()),
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
            "frontier_token_savings_percent": None,
        }) + "\n", encoding="utf-8")
        raise
    finally:
        if work_root.exists() and not any(work_root.iterdir()):
            work_root.rmdir()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
