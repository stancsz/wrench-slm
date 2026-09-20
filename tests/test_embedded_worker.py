from pathlib import Path

import torch

from wrench_harness import WrenchWorker


def test_embedded_worker_handles_mechanical_proposal_without_model(tmp_path: Path):
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path)
    result = worker.propose(
        [{"role": "user", "content": "Read README.md with a 4096 byte limit."}],
    )
    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "missing_path"
    assert result["backend"] == "embedded-mechanical"
    assert result["mechanical_fast_path"] is True


def test_embedded_worker_rejects_unsafe_mechanical_request(tmp_path: Path):
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path)
    result = worker.propose(
        [{"role": "user", "content": "Delete the repository permanently."}],
    )
    assert result == {
        "status": "abstain",
        "fallback_reason": "task_family_not_allowlisted",
        "backend": "embedded-mechanical",
        "mechanical_fast_path": True,
        "raw_model_output": '{"status":"abstain","fallback_reason":"task_family_not_allowlisted"}',
    }


def test_from_pretrained_lazy_mechanical_mode_does_not_require_transformers(tmp_path: Path):
    worker = WrenchWorker.from_pretrained(tmp_path, allowed_root=tmp_path, load_model=False)
    result = worker.propose(
        [{"role": "user", "content": "Delete the repository permanently."}],
    )
    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "task_family_not_allowlisted"
    assert result["backend"] == "embedded-mechanical"
    assert result["mechanical_fast_path"] is True


def test_embedded_worker_resolves_old_reference_lookup_without_model(tmp_path: Path):
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path)
    historical = (
        "historical payload\n"
        "symbol=run_worker path=src/wrench_harness/worker.py line=218\n"
    )
    result = worker.propose(
        [{
            "role": "user",
            "content": historical
            + 'Inspect the source for symbol "run_worker" with a 65536 byte limit.',
        }],
    )
    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "missing_path"
    assert result["backend"] == "embedded-mechanical"
    assert result["mechanical_fast_path"] is True
    assert result["raw_model_output"] == (
        '{"schema":"wrench.proposal.v1","action":"read_file",'
        '"path":"src/wrench_harness/worker.py","max_bytes":65536}'
    )


def test_embedded_worker_uses_earlier_user_message_as_reference(tmp_path: Path):
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path)
    result = worker.propose(
        [
            {
                "role": "user",
                "content": "historical lookup symbol=run_worker path=src/wrench_harness/worker.py line=218",
            },
            {
                "role": "assistant",
                "content": "Reference retained for the next bounded read.",
            },
            {
                "role": "user",
                "content": 'Inspect the source for symbol "run_worker" with a 65536 byte limit.',
            },
        ],
    )
    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "missing_path"
    assert result["backend"] == "embedded-mechanical"
    assert result["mechanical_fast_path"] is True


def test_embedded_worker_recovers_review_diff_from_old_reference(tmp_path: Path):
    (tmp_path / "README.md").write_text("old line\n", encoding="utf-8")
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path)
    result = worker.propose(
        [
            {
                "role": "user",
                "content": (
                    "Historical review artifact:\n"
                    "--- a/README.md\n"
                    "+++ b/README.md\n"
                    "@@ -1 +1 @@\n"
                    "-old line\n"
                    "+new line\n"
                ),
            },
            {
                "role": "user",
                "content": "Prepare an unapplied unified diff for README.md for review.",
            },
        ]
    )
    assert result["status"] == "accepted"
    assert result["action"] == "patch_draft"
    assert result["observation"]["applied"] is False
    assert result["observation"]["diff"].endswith("+new line\n")
    assert result["backend"] == "embedded-mechanical"


def test_embedded_worker_uses_latest_suffix_as_active_intent(tmp_path: Path):
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path)
    noisy_history = "stale lookup telemetry record status observed unrelated reference-only data; " * 2_000
    result = worker.propose(
        [{
            "role": "user",
            "content": noisy_history + "\nRead README.md with a 4096 byte limit.",
        }],
    )
    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "missing_path"
    assert result["backend"] == "embedded-mechanical"
    assert result["mechanical_fast_path"] is True
    assert '"action":"read_file"' in result["raw_model_output"]


def test_model_worker_stages_monster_payload_before_generation(tmp_path: Path):
    (tmp_path / "README.md").write_text("bounded worker\n", encoding="utf-8")

    class FakeTokenizer:
        eos_token_id = 2
        pad_token_id = 2

        def __init__(self):
            self.last_prompt = ""

        def apply_chat_template(self, messages, **kwargs):
            self.last_prompt = "\n".join(message["content"] for message in messages)
            return self.last_prompt

        def __call__(self, prompt, **kwargs):
            return {"input_ids": torch.zeros((1, max(1, len(prompt.split()))), dtype=torch.long)}

        def decode(self, generated, **kwargs):
            return (
                '{"schema":"wrench.proposal.v1","action":"read_file",'
                '"path":"README.md","max_bytes":4096}'
            )

    class FakeModel:
        def parameters(self):
            yield torch.zeros(1)

        def generate(self, **batch):
            return torch.cat([batch["input_ids"], torch.tensor([[1]])], dim=1)

    tokenizer = FakeTokenizer()
    worker = WrenchWorker(tokenizer=tokenizer, model=FakeModel(), allowed_root=tmp_path)
    result = worker.propose(
        [
            {"role": "system", "content": "bounded worker"},
            {"role": "assistant", "content": "old reference " * 70_000},
            {"role": "user", "content": "Return a bounded proposal after reviewing the reference."},
        ]
    )
    assert result["status"] == "accepted"
    assert result["backend"] == "transformers"
    assert result["dynamic_prefill"]["mode"] == "staged_single_pass"
    assert result["dynamic_prefill"]["raw_token_count"] > 64_000
    assert result["dynamic_prefill"]["model_prefill_token_count"] <= 64_000
    assert "wrench:reference-index" in tokenizer.last_prompt
    assert "wrench:current-intent" in tokenizer.last_prompt
    assert result["dynamic_prefill"]["pipeline"] == "map_reduce_dynamic_native"


def test_dynamic_prefill_splits_a_monolithic_current_payload():
    from wrench_harness.worker import _dynamic_prefill_messages

    payload = (
        "old reference symbol=run_worker path=src/wrench_harness/worker.py\n"
        + ("stale unrelated context\n" * 70_000)
        + "CURRENT INTENT: return one bounded proposal for the active task."
    )
    staged, receipt = _dynamic_prefill_messages([
        {"role": "system", "content": "bounded worker"},
        {"role": "user", "content": payload},
    ])
    assert receipt is not None
    assert receipt["mode"] == "staged_single_pass"
    assert receipt["split_current_message"] is True
    assert receipt["raw_token_count"] > 64_000
    assert receipt["model_prefill_token_count"] <= 64_000
    assert receipt["source_payload_sha256"] != receipt["prepared_payload_sha256"]
    assert receipt["payload_hash_mode"] == "ordered_original_plus_content_addressed_prepared"
    assert any(message["role"] == "user" and "CURRENT INTENT" in message["content"] for message in staged)
    assert any(message["role"] == "user" and "wrench:reference-index" in message["content"] for message in staged)


def test_dynamic_prefill_raises_context_tier_only_for_complex_long_intent(monkeypatch):
    from wrench_harness.worker import _dynamic_prefill_messages

    monkeypatch.setenv("WRENCH_MODEL_PREFILL_BUDGET", "64000")
    monkeypatch.setenv("WRENCH_MODEL_PREFILL_MAX_BUDGET", "128000")
    staged, receipt = _dynamic_prefill_messages([
        {"role": "assistant", "content": "old trace\n" * 100_000},
        {"role": "user", "content": "Compare the old trace and find the root cause."},
    ])
    assert receipt is not None
    assert receipt["adaptive_selection"]["selected_budget"] == 128_000
    assert receipt["model_prefill_budget"] == 128_000
    assert receipt["model_prefill_token_count"] <= 128_000
    assert any("wrench:reference-index" in message["content"] for message in staged)
