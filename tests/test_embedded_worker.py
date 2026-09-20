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
