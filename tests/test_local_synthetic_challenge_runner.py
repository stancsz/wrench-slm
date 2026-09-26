from __future__ import annotations

import json
from pathlib import Path

from tools.run_local_synthetic_challenge import (
    CHALLENGE_CASES,
    ChallengeError,
    FrozenSnapshot,
    classify_response,
    derive_oracle,
    load_fixture,
    parse_tool_call,
    run_case,
    sanitize_fixture_case,
    score_answer,
    Transcript,
)


class FakeTokenizer:
    """Character IDs make serialization/accounting deterministic in unit tests."""

    def __init__(self):
        self.seen_messages = []

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, return_tensors):
        assert tokenize and add_generation_prompt and return_tensors == "pt"
        self.seen_messages.append([dict(message) for message in messages])
        serialized = "".join(f"<{m['role']}>{m['content']}" for m in messages) + "<assistant>"
        return [ord(char) for char in serialized]

    def decode(self, token_ids, *, skip_special_tokens):
        assert skip_special_tokens
        return "".join(chr(token) for token in token_ids)


class FakeTensor(list):
    def __init__(self, values, device="cpu"):
        super().__init__(values)
        self.device = device

    def tolist(self):
        return list(self)

    def to(self, device):
        return FakeTensor(self, str(device))


class DeviceTokenizer(FakeTokenizer):
    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, return_tensors):
        return FakeTensor(super().apply_chat_template(
            messages, tokenize=tokenize, add_generation_prompt=add_generation_prompt,
            return_tensors=return_tensors,
        ))


class FakeModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.limits = []

    def generate(self, input_ids, *, max_new_tokens, max_time, do_sample):
        assert do_sample is False
        assert max_time == 60
        self.limits.append(max_new_tokens)
        response = self.responses.pop(0)
        tokens = [ord(char) for char in response]
        assert len(tokens) <= max_new_tokens
        return input_ids + tokens


class DeviceFakeModel(FakeModel):
    device = "cuda:0"

    def generate(self, input_ids, *, max_new_tokens, max_time, do_sample):
        assert input_ids.device == self.device
        return super().generate(input_ids, max_new_tokens=max_new_tokens, max_time=max_time, do_sample=do_sample)


def _fixtures():
    return load_fixture()[0]


def test_fixture_sanitization_exposes_only_validated_source_bytes():
    case = _fixtures()["loc-a"]
    files = sanitize_fixture_case(case)
    assert set(files) == {"src/cache.py", "src/near_match.py"}
    assert "answer_oracle" not in files
    assert "case_id" not in files
    bad = {"files": [{"path": "../secret", "content_utf8": "x"}]}
    try:
        sanitize_fixture_case(bad)
    except ChallengeError as exc:
        assert str(exc) == "invalid_relative_path"
    else:
        raise AssertionError("path traversal accepted")


def test_read_and_search_envelopes_are_bounded_and_snapshot_only():
    case = _fixtures()["context-a"]
    snapshot = FrozenSnapshot.from_fixture(case)
    result = snapshot.literal_search("src", "AUTH_HEADER", 3)
    assert result == {
        "status": "ok", "root": "src", "literal": "AUTH_HEADER",
        "matches": [{"path": "src/session.py", "line": 1, "text": "AUTH_HEADER = 'X-Account'"}],
        "truncated": False, "scope": "supplied_snapshot_sources",
    }
    assert snapshot.read_file("not/in/snapshot", 12) == {
        "status": "error", "code": "source_not_in_snapshot", "path": "not/in/snapshot",
    }
    try:
        snapshot.read_file("src/session.py", 1025)
    except ChallengeError as exc:
        assert str(exc) == "invalid_read_limit"
    else:
        raise AssertionError("oversized read limit accepted")


def test_stale_case_mutates_after_snapshot_and_returns_hash_only_error():
    case = _fixtures()["evidence-stale"]
    snapshot = FrozenSnapshot.from_fixture(case)
    result = snapshot.read_file("src/config.py", 128)
    assert result == {
        "status": "error", "code": "snapshot_read_changed", "path": "src/config.py",
        "snapshot_sha256": "90f158e7eb90939cdd446e4a56ceb26cae2b734176a4c6ed334e9217aeef1298",
        "current_sha256": "0e10c2e8a086555d4725d3e8ce74e1ea94ce0042ba938a6b1b80086985160b60",
    }
    assert "text" not in result
    assert snapshot.stale_delivered


def test_strict_tool_envelope_rejects_extra_or_disallowed_actions():
    assert parse_tool_call('{"name":"read_file","arguments":{"path":"src/a.py","max_bytes":10}}') == (
        "read_file", {"path": "src/a.py", "max_bytes": 10}
    )
    for raw in (
        '{"name":"read_file","arguments":{"path":"../a","max_bytes":10}}',
        '{"name":"shell","arguments":{"command":"whoami"}}',
        '{"name":"read_file","arguments":{"path":"src/a.py","max_bytes":10,"extra":1}}',
        '{"name":"read_file","name":"literal_search","arguments":{}}',
    ):
        try:
            parse_tool_call(raw)
        except ChallengeError:
            pass
        else:
            raise AssertionError(f"invalid tool call accepted: {raw}")


def test_scoring_requires_exact_typed_answer_and_evidence():
    case = _fixtures()["loc-a"]
    expected = derive_oracle("loc-a", case)
    assert score_answer(json.dumps(expected), expected)["answer_correct"]
    wrong_quote = dict(expected)
    wrong_quote["evidence"] = [{**expected["evidence"][0], "quote": "near match"}]
    assert not score_answer(json.dumps(wrong_quote), expected)["answer_correct"]
    assert not score_answer('{"status":"unknown","answer":null,"evidence":[],"reason":"unsupported"}', expected)["valid_json_schema"]
    assert not score_answer('{"status":"unknown","answer":null,"evidence":[],"reason":[]}', expected)["valid_json_schema"]


def test_transcript_counts_every_serialized_call_and_hides_fixture_metadata():
    fixtures = _fixtures()
    case = fixtures["context-a"]
    prompt = dict(CHALLENGE_CASES)["context-a"]
    expected = derive_oracle("context-a", case)
    model = FakeModel([
        '{"name":"literal_search","arguments":{"root":"src","literal":"AUTH_HEADER","max_matches":3}}',
        json.dumps(expected, separators=(",", ":")),
    ])
    tokenizer = FakeTokenizer()
    result = run_case("context-a", prompt, case, model, tokenizer)
    assert result["status"] == "completed"
    assert result["score"]["answer_correct"]
    assert result["tool_call_count"] == 1
    accounting = result["token_accounting"]
    assert accounting["prompt_tokens"] == sum(call["input_tokens"] for call in accounting["calls"])
    assert accounting["completion_tokens"] == sum(call["output_tokens"] for call in accounting["calls"])
    assert len(accounting["calls"]) == 2
    assert model.limits == [192, 192]
    visible = json.dumps(tokenizer.seen_messages)
    for hidden in ("context-a", "context_selection", "context-literal-boundary", "answer_oracle", "omitted_distractors"):
        assert hidden not in visible
    assert "AUTH_HEADER = 'X-Account'" in visible
    assert result["frontier_token_savings_percent"] is None
    assert result["frontier_savings_status"].startswith("N/A_")


def test_disallowed_json_action_is_a_safety_failure():
    case = _fixtures()["loc-a"]
    model = FakeModel(['{"name":"shell","arguments":{"command":"dir"}}'])
    result = run_case("loc-a", dict(CHALLENGE_CASES)["loc-a"], case, model, FakeTokenizer())
    assert result["status"] == "failed"
    assert result["failure"] == "disallowed_or_invalid_tool_call"


def test_generation_moves_serialized_input_to_cuda_device():
    model = DeviceFakeModel(['{"status":"known","answer":"x","evidence":[],"reason":null}'])
    transcript = Transcript(DeviceTokenizer(), [{"role": "user", "content": "question"}])
    answer = transcript.generate(model)
    assert answer.startswith('{"status":"known"')
