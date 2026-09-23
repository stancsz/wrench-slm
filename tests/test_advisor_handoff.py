import json

from wrench_harness.handoff import build_advisor_handoff
from wrench_harness.worker import WrenchWorker


def test_advisor_handoff_is_bounded_and_hash_bound():
    raw = "stale reference " * 200_000
    messages = [
        {"role": "system", "content": "proposal only"},
        {"role": "assistant", "content": raw},
        {"role": "user", "content": "Review the latest failure and propose a safe next step."},
    ]
    staged = [
        {"role": "system", "content": "proposal only"},
        {"role": "user", "content": "<wrench:reference-index>lookup id=ref-1</wrench:reference-index>"},
        {"role": "user", "content": "<wrench:current-intent>Review the latest failure and propose a safe next step.</wrench:current-intent>"},
    ]
    packet = build_advisor_handoff(
        messages,
        result={
            "status": "abstain",
            "fallback_reason": "task_family_not_allowlisted",
            "raw_model_output": raw,
        },
        working_messages=staged,
        prefill_receipt={
            "schema": "wrench.dynamic-prefill-receipt.v1",
            "raw_token_count": 800_000,
            "model_prefill_token_count": 42,
            "source_payload_sha256": "a" * 64,
            "lookup_table": {"ref-1": raw},
            "lookup_table_ids": ["ref-1"],
        },
    )

    encoded = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert packet["schema"] == "wrench.advisor-handoff.v1"
    assert packet["raw_payload_sha256"] == "a" * 64
    assert packet["raw_payload_hash_bound"] is True
    assert packet["frontier_policy"]["max_frontier_calls"] == 2
    assert packet["authority"] == "proposal_only_no_mutation"
    assert packet["working_context_token_estimate"] <= 64_000
    assert len(encoded) <= 1_000_000
    assert "lookup_table" not in packet["prefill"]
    assert packet["wrench_attempt"]["raw_model_output"] != raw


def test_worker_attaches_handoff_only_to_abstention(tmp_path):
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path)
    result = worker.propose(
        [
            {"role": "system", "content": "proposal only"},
            {"role": "user", "content": "Implement a new subsystem and deploy it."},
        ]
    )

    assert result["status"] == "abstain"
    assert result["advisor_handoff"]["schema"] == "wrench.advisor-handoff.v1"
    assert result["advisor_handoff"]["handoff_required"] is True
    assert result["advisor_handoff"]["raw_payload_hash_bound"] is True
    assert result["advisor_handoff"]["frontier_policy"]["max_frontier_calls"] == 2
