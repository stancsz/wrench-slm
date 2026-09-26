"""Run one frozen, provider-free synthetic E0 evidence-packet screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SRC = REPO_ROOT / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.snapshot import bind_source_root, create_snapshot


JOB_ID = "WRENCH-LOCAL-FAILURE-PACKET-20260927-01"
NONCE = "FTP01-6C2A"
SCHEMA = "wrench.failing-test-evidence-packet-receipt.v1"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "failing_test_evidence_packet_screen_01.json"
EXPECTED_FIXTURE_SHA256 = "914618905adcf48bc6d609f20b2588e61ae2b677d66b4e0f26eda05e62a3c898"
MAX_FIXTURE_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_CASES = 20
MAX_FILES_PER_CASE = 8
MAX_REQUESTS_PER_CASE = 8
MAX_SECONDS = 30
FAILURE = re.compile(r"^FAILED ([^\s:]+\.py)::([A-Za-z_][A-Za-z0-9_]*) - (.+)$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_fixture() -> tuple[dict[str, object], bytes]:
    raw = FIXTURE.read_bytes()
    if len(raw) > MAX_FIXTURE_BYTES:
        raise ValueError("fixture_byte_limit_exceeded")
    if _sha256(raw) != EXPECTED_FIXTURE_SHA256:
        raise ValueError("fixture_sha256_mismatch")
    fixture = json.loads(raw)
    if (
        not isinstance(fixture, dict)
        or fixture.get("schema") != "wrench.failing-test-evidence-packet-screen.v1"
        or fixture.get("fixture_id") != "wrench-failing-test-evidence-packet-screen-01"
        or fixture.get("provenance") != "wrench_authored_fresh_synthetic_only"
    ):
        raise ValueError("fixture_identity_invalid")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise ValueError("case_count_out_of_bounds")
    total_bytes = 0
    seen_case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case_record_invalid")
        case_id = case.get("case_id")
        files = case.get("files")
        requests = case.get("requests")
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in {".", ".."}
            or len(case_id) > 64
            or not all(char.isascii() and (char.isalnum() or char in "._-") for char in case_id)
            or case_id in seen_case_ids
            or not isinstance(files, list)
            or not 1 <= len(files) <= MAX_FILES_PER_CASE
            or not isinstance(requests, list)
            or not 1 <= len(requests) <= MAX_REQUESTS_PER_CASE
        ):
            raise ValueError("case_identity_or_shape_invalid")
        seen_case_ids.add(case_id)
        case_bytes = 0
        for row in files:
            if not isinstance(row, dict) or not isinstance(row.get("content_utf8"), str):
                raise ValueError("file_record_invalid")
            case_bytes += len(row["content_utf8"].encode("utf-8"))
        if case_bytes > MAX_FIXTURE_BYTES:
            raise ValueError("case_byte_limit_exceeded")
        total_bytes += case_bytes
    if total_bytes > MAX_FIXTURE_BYTES:
        raise ValueError("fixture_total_source_bytes_exceeded")
    return fixture, raw


def _write_fixture_tree(root: Path, files: list[dict[str, object]]) -> dict[str, str]:
    texts: dict[str, str] = {}
    total = 0
    for row in files:
        if not isinstance(row, dict):
            raise ValueError("file_record_invalid")
        path, text, expected_hash = row.get("path"), row.get("content_utf8"), row.get("sha256")
        if not isinstance(path, str) or not isinstance(text, str) or not isinstance(expected_hash, str):
            raise ValueError("file_record_fields_invalid")
        parts = path.split("/")
        if not _valid_relative_posix_path(path):
            raise ValueError("fixture_path_invalid")
        data = text.encode("utf-8")
        total += len(data)
        if len(data) > 8192 or total > MAX_FIXTURE_BYTES:
            raise ValueError("fixture_file_byte_limit_exceeded")
        digest = _sha256(data)
        if expected_hash != digest:
            raise ValueError("fixture_file_hash_mismatch")
        texts[path] = text
        target = root.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if len(texts) != len(files) or not texts:
        raise ValueError("fixture_paths_duplicate_or_empty")
    return texts


def _valid_relative_posix_path(path: object) -> bool:
    return (
        isinstance(path, str)
        and bool(path)
        and not path.startswith("/")
        and "\\" not in path
        and ":" not in path
        and all(part not in {"", ".", ".."} for part in path.split("/"))
    )


def _tree(root: Path):
    binding = bind_source_root(root)
    paths = tuple(sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()))
    return binding, create_snapshot(binding, paths)


def _route(prompt: str, binding, snapshot) -> dict[str, object]:
    route = run_e0_rule_route(prompt, root_binding=binding, snapshot=snapshot)
    return {
        "status": route.status.value,
        "action": route.action,
        "reason": route.reason,
        "observation": route.observation,
        "snapshot_sha256": route.snapshot_sha256,
        "evidence": [
            {"path": item.path, "status": item.status, "sha256": item.content_sha256, "size_bytes": item.size_bytes}
            for item in route.evidence
        ],
        "unknown_evidence": [
            {"path": item.path, "status": item.status, "sha256": item.content_sha256, "size_bytes": item.size_bytes}
            for item in route.unknown_evidence
        ],
    }


def _parse_packet(log_path: str, log_text: str, source_texts: dict[str, str]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    seen: set[str] = set()
    lines = log_text.splitlines()
    for index, line in enumerate(lines, start=1):
        if not line.startswith("FAILED "):
            continue
        match = FAILURE.fullmatch(line)
        if match is None:
            raise ValueError("unparseable_failure_record")
        source_path, test_name, _summary = match.groups()
        test_id = f"{source_path}::{test_name}"
        if test_id in seen:
            raise ValueError("duplicate_failure_test_id")
        seen.add(test_id)
        source = source_texts.get(source_path)
        if source is None:
            raise ValueError("failure_source_missing_from_snapshot")
        source_rows = source.splitlines()
        definition = f"def {test_name}("
        matches = [(line_no, value) for line_no, value in enumerate(source_rows, start=1) if value.lstrip().startswith(definition)]
        if len(matches) != 1:
            raise ValueError("failure_source_definition_missing_or_ambiguous")
        source_line, source_quote = matches[0]
        findings.append({
            "test_id": test_id,
            "source_path": source_path,
            "source_line": source_line,
            "source_quote": source_quote,
            "source_sha256": _sha256(source.encode("utf-8")),
            "log_path": log_path,
            "log_line": index,
            "log_quote": line,
            "log_sha256": _sha256(log_text.encode("utf-8")),
        })
    return findings


def _oracle_projection(packet: list[dict[str, object]] | None) -> list[dict[str, object]] | None:
    if packet is None:
        return None
    keys = ("test_id", "source_path", "source_line", "source_quote", "log_path", "log_line", "log_quote")
    return [{key: row[key] for key in keys} for row in packet]


def _run_case(base: Path, case: dict[str, object]) -> dict[str, object]:
    case_id = case.get("case_id")
    case_root = base / str(case_id)
    case_root.mkdir()
    files = case.get("files")
    requests = case.get("requests")
    if not isinstance(files, list) or not isinstance(requests, list):
        raise ValueError("case_shape_invalid")
    source_texts = _write_fixture_tree(case_root, files)
    binding, snapshot = _tree(case_root)
    mutation = case.get("mutate_after_snapshot")
    if isinstance(mutation, dict):
        for raw_path, raw_text in mutation.items():
            if not _valid_relative_posix_path(raw_path) or not isinstance(raw_text, str):
                raise ValueError("mutation_record_invalid")
            target = case_root.joinpath(*raw_path.split("/"))
            target.write_text(str(raw_text), encoding="utf-8", newline="")

    route_rows = []
    retrieved: dict[str, str] = {}
    for request in requests:
        if not isinstance(request, dict) or not isinstance(request.get("prompt"), str):
            raise ValueError("request_shape_invalid")
        result = _route(request["prompt"], binding, snapshot)
        expected_status = request.get("expected_status", "completed")
        if result["status"] != expected_status:
            raise ValueError("route_status_mismatch")
        if expected_status == "abstain":
            if result["reason"] != request.get("expected_reason"):
                raise ValueError("abstention_reason_mismatch")
        else:
            observation = result.get("observation")
            if result.get("action") != "read_file" or not isinstance(observation, dict):
                raise ValueError("route_did_not_return_exact_file_read")
            path = request.get("path")
            if observation.get("path") != path:
                raise ValueError("route_path_mismatch")
            text = observation.get("text")
            if not isinstance(text, str):
                raise ValueError("route_text_missing")
            digest = _sha256(text.encode("utf-8"))
            if digest != request.get("expected_sha256"):
                raise ValueError("route_content_hash_mismatch")
            retrieved[str(path)] = text
        route_rows.append({
            "path": request.get("path"),
            "expected_status": expected_status,
            "expected_reason": request.get("expected_reason"),
            **result,
        })

    packet = None
    packet_exact = None
    if case.get("kind") == "answerable":
        logs = [path for path in retrieved if path.lower().endswith((".log", ".txt"))]
        if len(logs) != 1:
            raise ValueError("expected_one_log_per_positive_case")
        packet = _parse_packet(logs[0], retrieved[logs[0]], retrieved)
        packet_exact = packet == case.get("expected_packet")
        if packet_exact is not True:
            raise ValueError("packet_oracle_mismatch")
    elif case.get("kind") != "boundary" or case.get("expected_packet") is not None:
        raise ValueError("case_kind_invalid")

    after = _tree(case_root)[1]
    before_paths = {row.path: row.sha256 for row in snapshot.sources}
    after_paths = {row.path: row.sha256 for row in after.sources}
    unchanged = before_paths == after_paths
    mutation_expectation = case.get("mutate_after_snapshot", {})
    expected_mutation_paths = set(mutation_expectation) if isinstance(mutation_expectation, dict) else set()
    changed_paths = {path for path in set(before_paths) | set(after_paths) if before_paths.get(path) != after_paths.get(path)}
    mutation_expected = bool(expected_mutation_paths)
    mutation_matches = changed_paths == expected_mutation_paths
    if mutation_expected:
        for raw_path, raw_text in mutation_expectation.items():
            expected_digest = _sha256(str(raw_text).encode("utf-8"))
            if after_paths.get(raw_path) != expected_digest:
                mutation_matches = False
    else:
        mutation_matches = unchanged
    if not mutation_matches:
        raise ValueError("fixture_mutation_expectation_mismatch")
    return {
        "case_id": case_id,
        "kind": case.get("kind"),
        "snapshot_sha256": snapshot.snapshot_sha256,
        "routes": route_rows,
        "packet": packet,
        "packet_exact": packet_exact,
        "expected_packet": case.get("expected_packet"),
        "fixture_tree_unchanged": unchanged,
        "expected_mutation": mutation_expected,
        "mutation_expectation_met": mutation_matches,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("refusing_to_overwrite_existing_receipt")
    output.parent.mkdir(parents=True, exist_ok=True)
    fixture, fixture_bytes = _load_fixture()
    started = time.perf_counter_ns()
    with tempfile.TemporaryDirectory(prefix="failure-packet-01-", dir=output.parent) as scratch:
        cases = [_run_case(Path(scratch), case) for case in fixture["cases"]]
    elapsed = time.perf_counter_ns() - started
    if elapsed > MAX_SECONDS * 1_000_000_000:
        raise SystemExit("execution_budget_exceeded")
    positives = [case for case in cases if case["kind"] == "answerable"]
    boundaries = [case for case in cases if case["kind"] == "boundary"]
    exact_positive_packets = sum(case["packet_exact"] is True for case in positives)
    correct_boundary_cases = sum(
        case["packet"] is None
        and len(case["routes"]) > 0
        and all(
            route["status"] == "abstain"
            and route["reason"] == route["expected_reason"]
            for route in case["routes"]
        )
        for case in boundaries
    )
    route_calls = sum(len(case["routes"]) for case in cases)
    report: dict[str, object] = {
        "schema": SCHEMA,
        "job_id": JOB_ID,
        "nonce": NONCE,
        "status": "complete",
        "claim_scope": "open_development_deterministic_evidence_packet_mechanics_only",
        "not_semantic_slm_acceptance": True,
        "not_real_work_utility": True,
        "not_frontier_token_savings": True,
        "repo_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip(),
        "runner_sha256": _sha256(Path(__file__).resolve().read_bytes()),
        "fixture_sha256": _sha256(fixture_bytes),
        "fixture_bytes": len(fixture_bytes),
        "case_count": len(cases),
        "positive_case_count": len(positives),
        "exact_positive_packet_count": exact_positive_packets,
        "boundary_case_count": len(boundaries),
        "correct_boundary_count": correct_boundary_cases,
        "route_call_count": route_calls,
        "all_positive_packets_exact": exact_positive_packets == len(positives),
        "all_boundaries_correct": correct_boundary_cases == len(boundaries),
        "expected_stale_mutation_count": sum(c["expected_mutation"] is True for c in cases),
        "unexpected_mutations": sum(c["mutation_expectation_met"] is not True for c in cases),
        "unsafe_dispatches": 0,
        "runtime_errors": 0,
        "elapsed_ns": elapsed,
        "cases": cases,
        "frontier_token_savings_percent": None,
        "eligible_matched_frontier_pairs": 0,
    }
    serialized = json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    encoded = serialized.encode("utf-8")
    if len(encoded) > MAX_OUTPUT_BYTES:
        raise SystemExit("receipt_byte_limit_exceeded")
    temp = output.with_suffix(output.suffix + ".tmp")
    temp.write_bytes(encoded)
    temp.replace(output)
    print(json.dumps({key: report[key] for key in (
        "status", "case_count", "exact_positive_packet_count", "boundary_case_count",
        "correct_boundary_count", "all_positive_packets_exact", "all_boundaries_correct",
        "unexpected_mutations", "elapsed_ns", "runner_sha256", "fixture_sha256"
    )}, sort_keys=True))
    return 0 if report["all_positive_packets_exact"] and report["all_boundaries_correct"] and report["unexpected_mutations"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
