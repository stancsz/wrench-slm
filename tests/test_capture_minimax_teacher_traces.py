from __future__ import annotations

from tools.capture_minimax_teacher_traces import _normalize, _parse_streaming_response


def test_parse_streaming_response_aggregates_content_and_usage() -> None:
    response = [
        b'data: {"model":"minimax","choices":[{"delta":{"content":"{\\"schema\\":\\""}}]}\n',
        b'data: {"model":"minimax","choices":[{"delta":{"content":"wrench.proposal.v1"},"finish_reason":null}]}\n',
        b'data: {"model":"minimax","choices":[{"delta":{"content":"\\"}"},"finish_reason":"stop"}],"usage":{"prompt_tokens":12,"completion_tokens":3,"total_tokens":15}}\n',
        b'data: [DONE]\n',
    ]
    content, model, finish_reason, usage = _parse_streaming_response(response)
    assert content == '{"schema":"wrench.proposal.v1"}'
    assert model == "minimax"
    assert finish_reason == "stop"
    assert usage == {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}


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
