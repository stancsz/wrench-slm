from pathlib import Path

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
