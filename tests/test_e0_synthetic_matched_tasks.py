from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.snapshot import bind_source_root, create_snapshot


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "e0_synthetic_matched_tasks_v1"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
SIDECAR_PATH = FIXTURE_DIR / "manifest.sha256"


def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _extract_function(text: str, attribute: str) -> tuple[str, int] | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^def\s+([A-Za-z_]\w*)\s*\(", line)
        if match is None:
            continue
        end = next(
            (offset for offset in range(index + 1, len(lines)) if re.match(r"^def\s+", lines[offset])),
            len(lines),
        )
        if any(attribute in body_line for body_line in lines[index + 1 : end]):
            return match.group(1), index + 1
    return None


def _derive_fixture_answer(case: dict[str, Any]) -> dict[str, Any]:
    """Independent frozen oracle over authored fixture bytes, not route output."""
    rule = case["answer_oracle"]["rule"]
    files = {item["path"]: item["content_utf8"] for item in case["files"]}
    kind = rule["kind"]

    if kind == "function_for_attribute":
        found = _extract_function(files[rule["source_path"]], rule["attribute"])
        assert found is not None
        symbol, line = found
        return {"symbol": symbol, "evidence": [{"path": rule["source_path"], "line": line}]}

    if kind == "log_error_type":
        for number, line in enumerate(files[rule["source_path"]].splitlines(), start=1):
            match = re.match(rule["pattern"], line)
            if match is not None:
                return {
                    "reported_error_type": match.group(1),
                    "evidence": [{"path": rule["source_path"], "line": number}],
                }
        raise AssertionError("frozen failure log has no supported error type")

    if kind == "literal_paths":
        root = rule["root"].rstrip("/") + "/"
        selected = sorted(
            path for path, text in files.items()
            if path.startswith(root) and rule["literal"] in text
        )
        candidates = sorted(path for path in files if path.startswith(root))
        return {"selected_evidence": selected, "omitted_distractors": [p for p in candidates if p not in selected]}

    if kind == "availability":
        requested = rule["requested_path"]
        item = next((source for source in case["files"] if source["path"] == requested), None)
        mutation = case.get("mutate_after_snapshot")
        if item is None or (mutation is not None and mutation["path"] == requested):
            return {"status": "unknown", "evidence": []}
        return {"status": "known", "evidence": [{"path": requested, "line": 1}]}

    if kind == "ambiguous_sources":
        if any(path not in files for path in rule["candidate_paths"]):
            raise AssertionError("ambiguity oracle candidates must exist in the synthetic snapshot")
        return {"status": "unknown", "evidence": []}

    if kind == "config_value":
        text = files[rule["source_path"]]
        pattern = rf"^{re.escape(rule['key'])}\s*=\s*'([^']+)'$"
        for number, line in enumerate(text.splitlines(), start=1):
            match = re.match(pattern, line)
            if match is not None:
                return {
                    "status": "known", rule["key"]: match.group(1),
                    "evidence": [{"path": rule["source_path"], "line": number}],
                }
        raise AssertionError("frozen config fixture is missing the requested key")

    raise AssertionError(f"unsupported frozen oracle kind: {kind}")


def _candidate_from_route(case: dict[str, Any], result: Any) -> dict[str, Any]:
    """Derive a task answer from actual bounded route output."""
    rule = case["answer_oracle"]["rule"]
    kind = rule["kind"]
    if result.status is RuleRouteStatus.ABSTAIN:
        return {"status": "unknown", "evidence": []}

    if kind == "function_for_attribute":
        found = _extract_function(result.observation["text"], rule["attribute"])
        assert found is not None
        symbol, line = found
        return {"symbol": symbol, "evidence": [{"path": rule["source_path"], "line": line}]}

    if kind == "log_error_type":
        text = result.observation["text"]
        for number, line in enumerate(text.splitlines(), start=1):
            match = re.match(rule["pattern"], line)
            if match is not None:
                return {
                    "reported_error_type": match.group(1),
                    "evidence": [{"path": rule["source_path"], "line": number}],
                }
        raise AssertionError("route read does not contain a supported error type")

    if kind == "literal_paths":
        selected = sorted({match["path"] for match in result.observation["matches"]})
        root = rule["root"].rstrip("/") + "/"
        candidates = sorted(item["path"] for item in case["files"] if item["path"].startswith(root))
        return {"selected_evidence": selected, "omitted_distractors": [p for p in candidates if p not in selected]}

    if kind == "config_value":
        text = result.observation["text"]
        pattern = rf"^{re.escape(rule['key'])}\s*=\s*'([^']+)'$"
        for number, line in enumerate(text.splitlines(), start=1):
            match = re.match(pattern, line)
            if match is not None:
                return {
                    "status": "known", rule["key"]: match.group(1),
                    "evidence": [{"path": rule["source_path"], "line": number}],
                }
        raise AssertionError("route read does not contain the requested config key")

    raise AssertionError(f"unexpected completed route for oracle kind: {kind}")


def _task_answer_matches(case: dict[str, Any], answer: object) -> bool:
    """Check a route-derived candidate against source-derived frozen truth."""
    if type(answer) is not dict:
        return False
    derived = _derive_fixture_answer(case)
    frozen = case["answer_oracle"]["expected"]
    return (
        _canonical_bytes(derived) == _canonical_bytes(frozen)
        and _canonical_bytes(answer) == _canonical_bytes(derived)
    )


def _route_case(case: dict[str, Any], tmp_path: Path):
    root = tmp_path / case["case_id"]
    root.mkdir()
    for item in case["files"]:
        path = root.joinpath(*item["path"].split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(item["content_utf8"].encode("utf-8"))

    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, [item["path"] for item in case["files"]])
    mutation = case.get("mutate_after_snapshot")
    if mutation is not None:
        changed_path = root.joinpath(*mutation["path"].split("/"))
        changed_path.write_bytes(mutation["content_utf8"].encode("utf-8"))

    return run_e0_rule_route(case["prompt"], root_binding=binding, snapshot=snapshot)


def _assert_mechanics(case: dict[str, Any], result: Any) -> None:
    expected = case["expected_mechanics"]
    assert result.status.value == expected["status"]
    assert result.action == expected["action"]
    if expected["status"] == "abstain":
        assert result.reason == expected["reason"]
        assert result.observation is None
    else:
        observation = dict(expected["observation"])
        if result.action == "read_file":
            observation["bytes"] = len(observation["text"].encode("utf-8"))
        assert result.observation == observation
    assert result.route == "none"


def _normalize_pair_input(pair: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """Mask one declared boundary input and compare every other input byte."""
    boundary = pair["boundary"]
    kind = boundary["kind"]
    prompt = case["prompt"]
    files = [
        {"path": item["path"], "content_utf8": item["content_utf8"]}
        for item in case["files"]
    ]
    mutation = case.get("mutate_after_snapshot")
    if mutation is not None:
        mutation = {"path": mutation["path"], "content_utf8": mutation["content_utf8"]}

    if kind == "text_token":
        value = boundary["values"][case["case_id"]]
        target = next(item for item in files if item["path"] == boundary["path"])
        assert target["content_utf8"].count(value) == 1
        target["content_utf8"] = target["content_utf8"].replace(value, "<BOUNDARY>", 1)
    elif kind == "snapshot_source_state":
        target_path = boundary["path"]
        files = [item for item in files if item["path"] != target_path]
        if mutation is not None and mutation["path"] == target_path:
            mutation = None
    elif kind == "prompt_value":
        value = boundary["values"][case["case_id"]]
        assert prompt.count(value) == 1
        prompt = prompt.replace(value, "<BOUNDARY>", 1)
    else:
        raise AssertionError(f"unsupported pair boundary kind: {kind}")

    return {"prompt": prompt, "files": files, "mutate_after_snapshot": mutation}


def test_manifest_sidecar_and_inline_source_hashes_are_frozen():
    manifest = _load_manifest()
    expected_sidecar = SIDECAR_PATH.read_text(encoding="ascii").strip()
    digest, filename = expected_sidecar.split()

    assert filename == MANIFEST_PATH.name
    assert digest == hashlib.sha256(_canonical_bytes(manifest)).hexdigest()
    assert manifest["schema"] == "wrench.synthetic-matched-tasks.v1"
    assert manifest["provenance"] == "wrench_authored_synthetic_only"
    assert manifest["usage"] == "open_development_fixture_only"
    assert manifest["not_a_utility_claim"] is True

    for pair in manifest["pairs"]:
        assert len(pair["cases"]) == 2
        for case in pair["cases"]:
            for item in case["files"]:
                raw = item["content_utf8"].encode("utf-8")
                assert hashlib.sha256(raw).hexdigest() == item["sha256"]
            mutation = case.get("mutate_after_snapshot")
            if mutation is not None:
                raw = mutation["content_utf8"].encode("utf-8")
                assert hashlib.sha256(raw).hexdigest() == mutation["sha256"]


def test_four_synthetic_groups_have_declared_single_boundary_pairs():
    manifest = _load_manifest()
    groups = {pair["group"] for pair in manifest["pairs"]}
    assert groups == {
        "localization",
        "failing_test_log_triage",
        "context_selection",
        "missing_stale_ambiguous_evidence",
    }
    assert all(pair["pair_id"] and pair["changed_boundary_fact"] and pair["boundary"] for pair in manifest["pairs"])
    assert len({case["case_id"] for pair in manifest["pairs"] for case in pair["cases"]}) == 10

    pairs = {pair["pair_id"]: pair["cases"] for pair in manifest["pairs"]}
    assert pairs["loc-function-name"][0]["prompt"] == pairs["loc-function-name"][1]["prompt"]
    for pair in manifest["pairs"]:
        boundary_values = pair["boundary"]["values"]
        case_ids = {case["case_id"] for case in pair["cases"]}
        assert set(boundary_values) == case_ids, pair["pair_id"]
        assert len(set(boundary_values.values())) == 2, pair["pair_id"]
        normalized = [_normalize_pair_input(pair, case) for case in pair["cases"]]
        assert _canonical_bytes(normalized[0]) == _canonical_bytes(normalized[1]), pair["pair_id"]


def test_mechanics_and_task_oracles_match_each_frozen_case(tmp_path):
    manifest = _load_manifest()
    count = 0
    for pair in manifest["pairs"]:
        for case in pair["cases"]:
            result = _route_case(case, tmp_path)
            _assert_mechanics(case, result)

            candidate = _candidate_from_route(case, result)
            assert _task_answer_matches(case, candidate)
            wrong = dict(candidate)
            wrong["unexpected_field"] = "mutated"
            assert not _task_answer_matches(case, wrong)
            count += 1
    assert count == 10


def test_route_oracle_distinguishes_unknown_evidence_from_known_answer(tmp_path):
    manifest = _load_manifest()
    cases = {
        case["case_id"]: case
        for pair in manifest["pairs"]
        for case in pair["cases"]
    }

    for case_id in ("evidence-missing", "evidence-stale", "evidence-ambiguous"):
        result = _route_case(cases[case_id], tmp_path)
        assert result.status is RuleRouteStatus.ABSTAIN
        assert cases[case_id]["answer_oracle"]["expected"]["status"] == "unknown"

    specific = cases["evidence-specific"]
    result = _route_case(specific, tmp_path)
    assert result.status is RuleRouteStatus.COMPLETED
    assert specific["answer_oracle"]["expected"]["status"] == "known"
