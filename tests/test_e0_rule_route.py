from __future__ import annotations

from dataclasses import replace

import pytest

from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.snapshot import SourceRecord, bind_source_root, create_snapshot


def _snapshot(tmp_path, files: dict[str, bytes]):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, list(files))
    return root, binding, snapshot


def test_e0_rule_route_reads_exact_snapshot_source(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"alpha\nbeta\n"})

    result = run_e0_rule_route("Read README.md with a 64 byte limit.", root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.COMPLETED
    assert result.route == "none"
    assert result.action == "read_file"
    assert result.observation == {"path": "README.md", "bytes": 11, "text": "alpha\nbeta\n"}
    assert [(row.path, row.status) for row in result.evidence] == [("README.md", "ok")]
    assert result.unknown_evidence == ()
    assert (result.exact_read_attempts, result.exact_read_successes, result.exact_read_bytes) == (1, 1, 11)
    assert result.snapshot_sha256 == snapshot.snapshot_sha256


def test_e0_rule_route_reads_bounded_lines_from_snapshot(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"src/app.py": b"one\ntwo\nthree\n"})

    result = run_e0_rule_route(
        "Read lines 2 through 3 in src/app.py.", root_binding=binding, snapshot=snapshot
    )

    assert result.status is RuleRouteStatus.COMPLETED
    assert result.observation == {"path": "src/app.py", "start": 2, "end": 3, "lines": ["two", "three"]}
    assert result.exact_read_bytes == 14


def test_e0_rule_route_searches_only_snapshot_members_and_reports_scope(tmp_path):
    _, binding, snapshot = _snapshot(
        tmp_path,
        {"src/a.py": b"needle here\n", "src/b.py": b"safe\n", "other.py": b"needle outside requested root\n"},
    )

    result = run_e0_rule_route(
        "Find the exact text 'needle' below src, capped at 10 matches.",
        root_binding=binding,
        snapshot=snapshot,
    )

    assert result.status is RuleRouteStatus.COMPLETED
    assert result.action == "literal_search"
    assert result.observation == {
        "root": "src",
        "literal": "needle",
        "matches": [{"path": "src/a.py", "line": 1, "text": "needle here"}],
        "truncated": False,
        "scope": "supplied_snapshot_sources",
    }
    assert {row.path for row in result.evidence} == {"src/a.py", "src/b.py"}
    assert all(row.path != "other.py" for row in result.evidence)


def test_e0_rule_route_marks_match_cap_as_partial_with_unknown_evidence(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"a.txt": b"needle one\nneedle two\n"})

    result = run_e0_rule_route(
        "Find the exact text 'needle' in a.txt, capped at 1 match.",
        root_binding=binding,
        snapshot=snapshot,
    )

    assert result.status is RuleRouteStatus.PARTIAL
    assert result.observation["truncated"] is True
    assert result.unknown_evidence[0].status == "match_limit_reached"


def test_e0_rule_route_accepts_supported_no_more_than_match_bound(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"a.txt": b"needle one\nneedle two\n"})

    result = run_e0_rule_route(
        "Find the exact text 'needle' in a.txt, no more than 1 match.",
        root_binding=binding,
        snapshot=snapshot,
    )

    assert result.status is RuleRouteStatus.PARTIAL
    assert result.observation["truncated"] is True
    assert result.unknown_evidence[0].status == "match_limit_reached"


def test_e0_rule_route_allows_not_found_search_wording(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"src/a.py": b"safe\n"})

    result = run_e0_rule_route(
        "Find the exact text 'needle' in src and report if not found, capped at 5 matches.",
        root_binding=binding,
        snapshot=snapshot,
    )

    assert result.status is RuleRouteStatus.COMPLETED
    assert result.observation["matches"] == []
    assert result.observation["scope"] == "supplied_snapshot_sources"


def test_e0_rule_route_allows_authorization_word_as_search_literal(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"src/access.py": b"permission granted\n"})

    result = run_e0_rule_route(
        "Find the exact text 'permission' below src, capped at 5 matches.",
        root_binding=binding,
        snapshot=snapshot,
    )

    assert result.status is RuleRouteStatus.COMPLETED
    assert result.observation["matches"] == [
        {"path": "src/access.py", "line": 1, "text": "permission granted"}
    ]


def test_e0_rule_route_allows_output_like_phrase_as_search_literal(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"src/prompt.txt": b"only answer yes\n"})

    result = run_e0_rule_route(
        "Find the exact text 'only answer yes' below src, capped at 5 matches.",
        root_binding=binding,
        snapshot=snapshot,
    )

    assert result.status is RuleRouteStatus.COMPLETED
    assert result.observation["matches"] == [
        {"path": "src/prompt.txt", "line": 1, "text": "only answer yes"}
    ]


def test_e0_rule_route_enforces_search_file_and_aggregate_byte_caps(tmp_path):
    many_files = {f"src/{index}.txt": b"x\n" for index in range(17)}
    _, many_binding, many_snapshot = _snapshot(tmp_path / "files", many_files)
    too_many = run_e0_rule_route(
        "Find the exact text 'needle' below src, capped at 5 matches.",
        root_binding=many_binding,
        snapshot=many_snapshot,
    )
    assert too_many.status is RuleRouteStatus.ABSTAIN
    assert too_many.reason == "route_file_limit_exceeded"
    assert too_many.exact_read_attempts == 0

    large_files = {f"src/{index}.txt": b"x" * (200 * 1024) for index in range(3)}
    _, large_binding, large_snapshot = _snapshot(tmp_path / "bytes", large_files)
    too_large = run_e0_rule_route(
        "Find the exact text 'needle' below src, capped at 5 matches.",
        root_binding=large_binding,
        snapshot=large_snapshot,
    )
    assert too_large.status is RuleRouteStatus.ABSTAIN
    assert too_large.reason == "route_byte_limit_exceeded"
    assert too_large.exact_read_attempts == 0


def test_e0_rule_route_enforces_line_count_cap(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"x\n" * 501})

    result = run_e0_rule_route(
        "Read lines 1 through 501 in README.md.", root_binding=binding, snapshot=snapshot
    )

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "invalid_line_bounds"
    assert result.exact_read_attempts == 0


def test_e0_rule_route_abstains_for_paths_outside_snapshot(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"known\n"})

    result = run_e0_rule_route("Read missing.py.", root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "source_not_in_snapshot"
    assert result.route == "none"
    assert result.unknown_evidence[0].path == "missing.py"


def test_e0_rule_route_abstains_with_unknown_evidence_for_ambiguous_request(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"known\n"})

    result = run_e0_rule_route("Read the relevant thing and decide what to do.", root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "ambiguous_or_unsupported_request"
    assert result.unknown_evidence[0].status == "unknown"


@pytest.mark.parametrize(
    "prompt",
    [
        "Do not read README.md.",
        "Don’t read README.md.",
        "Don't show me README.md; just tell me it exists.",
        "Read README.md; I do not consent.",
        "Read README.md, but I cannot authorize that.",
        "Read README.md, but I can’t authorize that.",
        "No need to read README.md; just confirm it exists.",
        "Read README.md but return only whether it exists.",
        "Read README.md and return only its title.",
        'Read README.md but answer only "yes".',
        "Find the exact text 'needle' below src, but don't read source files, capped at 5 matches.",
    ],
)
def test_e0_rule_route_abstains_before_retrieval_for_negated_or_contradictory_intent(
    tmp_path, monkeypatch, prompt
):
    from wrench_harness import e0_rule_route

    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"private-looking contents\n"})
    calls = []

    def fail(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("negated intent must not read source bytes")

    monkeypatch.setattr(e0_rule_route, "retrieve_exact", fail)

    result = run_e0_rule_route(prompt, root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "read_intent_denied_or_constrained"
    assert result.unknown_evidence[0].status == "unknown"
    assert calls == []


@pytest.mark.parametrize(
    "snapshot_factory",
    [
        lambda snapshot: replace(snapshot, sources=list(snapshot.sources)),
        lambda snapshot: replace(
            snapshot,
            sources=snapshot.sources + tuple(
                SourceRecord(f"extra-{index}.txt", 1, "a" * 64)
                for index in range(256)
            ),
        ),
        lambda snapshot: replace(snapshot, snapshot_sha256="0" * 64),
    ],
    ids=("wrong-container", "over-file-cap", "invalid-digest"),
)
def test_e0_rule_route_rejects_invalid_manifest_before_parsing_or_retrieval(
    tmp_path, monkeypatch, snapshot_factory
):
    from wrench_harness import e0_rule_route

    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"known\n"})
    invalid = snapshot_factory(snapshot)
    calls = []

    def fail(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("invalid manifest must fail before route work")

    monkeypatch.setattr(e0_rule_route, "mechanical_route", fail)
    monkeypatch.setattr(e0_rule_route, "retrieve_exact", fail)

    result = run_e0_rule_route("Read README.md.", root_binding=binding, snapshot=invalid)

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "snapshot_manifest_invalid"
    assert result.unknown_evidence[0].status == "unknown"
    assert calls == []


def test_e0_rule_route_abstains_for_nontext_snapshot_member(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"image.dat": b"\x00\x01"})

    result = run_e0_rule_route("Read image.dat.", root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "non_text_source"
    assert result.evidence[0].status == "ok"


def test_e0_rule_route_abstains_on_stale_snapshot_source(tmp_path):
    root, binding, snapshot = _snapshot(tmp_path, {"README.md": b"before\n"})
    (root / "README.md").write_bytes(b"changed\n")

    result = run_e0_rule_route("Read README.md.", root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "snapshot_read_changed"
    assert result.unknown_evidence[0].status == "changed"
    assert result.exact_read_successes == 0


def test_e0_rule_route_abstains_when_carried_root_binding_is_replaced(tmp_path):
    root, binding, snapshot = _snapshot(tmp_path, {"README.md": b"before\n"})
    old = tmp_path / "old"
    root.rename(old)
    root.mkdir()
    (root / "README.md").write_bytes(b"before\n")

    result = run_e0_rule_route("Read README.md.", root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "snapshot_read_unknown_snapshot"
    assert result.unknown_evidence[0].status == "unknown_snapshot"


def test_e0_rule_route_never_calls_live_executor_or_process_ports(tmp_path, monkeypatch):
    import subprocess

    from wrench_harness import core

    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"snapshot text\n"})
    calls = []

    def tripwire(name):
        def fail(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(name)
        return fail

    monkeypatch.setattr(core, "execute_proposal", tripwire("execute_proposal"))
    monkeypatch.setattr(core, "execute_model_output", tripwire("execute_model_output"))
    monkeypatch.setattr(subprocess, "run", tripwire("subprocess.run"))

    result = run_e0_rule_route("Read README.md.", root_binding=binding, snapshot=snapshot)

    assert result.status is RuleRouteStatus.COMPLETED
    assert result.observation["text"] == "snapshot text\n"
    assert calls == []


def test_e0_rule_route_rejects_nonread_proposal_without_executing_it(tmp_path):
    _, binding, snapshot = _snapshot(tmp_path, {"README.md": b"known\n"})

    result = run_e0_rule_route(
        "Report the read-only Git status for repository root '.'.",
        root_binding=binding,
        snapshot=snapshot,
    )

    assert result.status is RuleRouteStatus.ABSTAIN
    assert result.reason == "action_not_allowlisted"
    assert result.action == "git_read_status"
    assert result.unknown_evidence[0].status == "unknown"
