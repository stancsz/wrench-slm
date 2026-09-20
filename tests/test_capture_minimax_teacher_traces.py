from __future__ import annotations

from tools.capture_minimax_teacher_traces import _normalize


def test_normalize_extracts_proposal_after_minimax_thinking_block() -> None:
    content = (
        "<think>Choose the narrow read action.</think>\n"
        '{"schema":"wrench.proposal.v1","action":"read_file",'
        '"path":"README.md","max_bytes":131072}'
    )
    assert _normalize(content) == {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "README.md",
        "max_bytes": 131072,
    }


def test_normalize_rejects_json_without_wrench_schema() -> None:
    assert _normalize('{"action":"read_file","path":"README.md"}') is None
