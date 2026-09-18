from __future__ import annotations

import subprocess
import json
import struct
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from wrench_harness import CancellationToken, ProposalRouter, RouterConfig, execute_local_qwen, execute_model_output, execute_proposal, load_router_state, save_router_state
from tools.inspect_qwen_checkpoint import inspect_checkpoint
from tools.estimate_qwen_pruned_sizes import analyze_checkpoint
from tools.validate_pruning_source import validate_pruning_source


def proposal(action: str, **fields):
    return {"schema": "wrench.proposal.v1", "action": action, **fields}


def test_read_file_and_lines_are_bounded(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    result = execute_proposal(proposal("read_file", path="note.txt"), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["text"] == "alpha\nbeta\ngamma\n"

    result = execute_proposal(proposal("read_lines", path="note.txt", start=2, end=3), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["lines"] == ["beta", "gamma"]

    rejected = execute_proposal(proposal("read_file", path="..\\outside.txt"), tmp_path)
    assert rejected == {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}


def test_literal_search_is_not_regex_and_respects_limit(tmp_path: Path):
    (tmp_path / "a.txt").write_text("needle\nneedle.*\n", encoding="utf-8")
    result = execute_proposal(proposal("literal_search", root=".", literal="needle.*", max_matches=3), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["matches"][0]["line"] == 2
    assert result["observation"]["truncated"] is False

    capped = execute_proposal(proposal("literal_search", root=".", literal="needle.*", max_matches=1), tmp_path)
    assert len(capped["observation"]["matches"]) == 1
    assert capped["observation"]["truncated"] is True

    regex = execute_proposal(
        proposal("literal_search", root=".", literal="^needle", mode="regex", max_matches=3), tmp_path
    )
    assert regex["fallback_reason"] == "literal_mode_required"


def test_git_status_is_read_only(tmp_path: Path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    result = execute_proposal(proposal("git_read_status", repo_root="."), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["mutated"] is False


def test_health_and_patch_fail_closed(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("old\n", encoding="utf-8")
    external = execute_proposal(proposal("health_read", url="https://example.com/health"), tmp_path)
    assert external["fallback_reason"] == "health_endpoint_not_allowlisted"

    patch = execute_proposal(
        proposal(
            "patch_draft",
            files=["note.txt"],
            review_only=True,
            diff="--- a/note.txt\n+++ b/note.txt\n@@ -1 +1 @@\n-old\n+new\n",
        ),
        tmp_path,
    )
    assert patch["status"] == "accepted"
    assert patch["observation"]["applied"] is False
    assert target.read_text(encoding="utf-8") == "old\n"

    applied = execute_proposal(proposal("patch_draft", files=["note.txt"], review_only=False, diff="x"), tmp_path)
    assert applied["fallback_reason"] == "patch_draft_requires_review_only"


def test_pruning_source_rejects_packed_ftw(tmp_path: Path):
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_5_moe",
                "architectures": ["Qwen3_5MoeForConditionalGeneration"],
                "text_config": {
                    "num_hidden_layers": 40,
                    "hidden_size": 2048,
                    "num_experts": 256,
                    "num_experts_per_tok": 8,
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "hf_quant_config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "freetoken-00000.ftw").write_bytes(b"packed")
    result = validate_pruning_source(tmp_path)
    assert result["eligible"] is False
    assert "packed_ftw_not_sliceable" in result["rejection_reasons"]
    assert "safetensors_index_missing" in result["rejection_reasons"]


def test_checkpoint_inspection_distinguishes_unquantized_safetensors(tmp_path: Path):
    (tmp_path / "config.json").write_text(
        json.dumps({"model_type": "qwen3_5_moe", "text_config": {"num_hidden_layers": 40}}),
        encoding="utf-8",
    )
    (tmp_path / "model.safetensors.index.json").write_text(
        json.dumps({"metadata": {"total_size": 4}, "weight_map": {"layer.weight": "model-00001-of-00001.safetensors"}}),
        encoding="utf-8",
    )
    (tmp_path / "model-00001-of-00001.safetensors").write_bytes(b"1234")
    receipt = inspect_checkpoint(tmp_path, hash_weights=False)
    assert receipt["pruning_assessment"] == {
        "source_is_packed_quantized": False,
        "safe_for_structural_tensor_slicing": True,
        "reason": "Unquantized safetensors with a local tensor index are eligible for structural slicing after architecture checks.",
        "required_source": "verified unquantized checkpoint with matching architecture and license",
    }


def test_qwen_pruned_size_estimate_uses_headers_only(tmp_path: Path):
    (tmp_path / "config.json").write_text(
        json.dumps({"text_config": {"num_hidden_layers": 1, "num_experts": 4, "num_experts_per_tok": 2}}),
        encoding="utf-8",
    )
    tensors = {
        "model.language_model.layers.0.mlp.experts.gate_up_proj": ([4, 2, 3], "BF16"),
        "model.language_model.layers.0.mlp.experts.down_proj": ([4, 3, 2], "BF16"),
        "model.language_model.layers.0.mlp.gate.weight": ([4, 5], "BF16"),
        "model.language_model.layers.0.input_layernorm.weight": ([10], "BF16"),
    }
    header = {
        name: {"dtype": dtype, "shape": shape, "data_offsets": [0, 0]}
        for name, (shape, dtype) in tensors.items()
    }
    encoded = json.dumps(header, separators=(",", ":")).encode("utf-8")
    shard = tmp_path / "model-00001-of-00001.safetensors"
    shard.write_bytes(struct.pack("<Q", len(encoded)) + encoded)
    (tmp_path / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "metadata": {"total_size": 156},
                "weight_map": {name: shard.name for name in tensors},
            }
        ),
        encoding="utf-8",
    )
    report = analyze_checkpoint(tmp_path, [2])
    scenario = report["scenarios"][0]
    assert report["evidence_scope"] == "safetensors_headers_only_no_tensor_payload_loaded"
    assert report["tensor_inventory"]["tensor_elements"] == 78
    assert scenario["estimated_tensor_elements"] == 44


def test_model_output_requires_exact_json_object(tmp_path: Path):
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    valid = '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}'
    result = execute_model_output(valid, tmp_path)
    assert result["status"] == "accepted"
    assert result["model_output_validated"] is True

    for invalid, reason in (
        ("```json\n" + valid + "\n```", "model_output_invalid_json"),
        ("Here is the proposal: " + valid, "model_output_invalid_json"),
        ("[1, 2, 3]", "model_output_not_object"),
        ("not json", "model_output_invalid_json"),
    ):
        rejected = execute_model_output(invalid, tmp_path)
        assert rejected["fallback_reason"] == reason


def test_local_qwen_adapter_is_allowlisted_and_parser_gated(tmp_path: Path):
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    expected = '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}'

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            json.loads(self.rfile.read(length))
            payload = {"model": "test-qwen", "choices": [{"message": {"content": expected}}], "usage": {"total_tokens": 9}}
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        result = execute_local_qwen(endpoint, "test-qwen", [{"role": "user", "content": "proposal"}], str(tmp_path))
        assert result["status"] == "accepted"
        assert result["usage"]["total_tokens"] == 9

        remote = execute_local_qwen("https://example.com/v1/chat/completions", "test-qwen", [], str(tmp_path))
        assert remote["fallback_reason"] == "qwen_endpoint_not_allowlisted"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_router_attempt_ceiling_circuit_bypass_and_hash_bound_reset():
    router = ProposalRouter(RouterConfig(max_attempts=2, failure_threshold=2))
    rejected = lambda: {"status": "abstain", "fallback_reason": "model_output_invalid_json"}
    first = router.run(rejected)
    second = router.run(rejected)
    assert first["status"] == "abstain"
    assert second["circuit_opened"] is True
    assert router.run(lambda: {"status": "accepted"})["fallback_reason"] == "router_disabled"

    assert router.reset("wrong-hash") is False
    assert router.reset(router.config.config_hash) is True
    assert router.run(lambda: {"status": "accepted"})["status"] == "accepted"
    router.bypass("maintenance")
    assert router.run(lambda: {"status": "accepted"})["fallback_reason"] == "router_disabled"


def test_router_state_persists_and_rejects_hash_mismatch(tmp_path: Path):
    config = RouterConfig(max_attempts=3, failure_threshold=2)
    router = ProposalRouter(config)
    router.run(lambda: {"status": "abstain", "fallback_reason": "test"})
    state_path = tmp_path / "router-state.json"
    saved = save_router_state(router, state_path)
    assert saved["schema"] == "wrench.router-state.v1"
    restored = load_router_state(config, state_path)
    assert restored.status()["attempts"] == 1
    assert restored.status()["failures"] == 1

    try:
        load_router_state(RouterConfig(max_attempts=4, failure_threshold=2), state_path)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("hash-mismatched state was accepted")


def test_router_cancellation_and_events():
    events = []
    router = ProposalRouter(RouterConfig(max_attempts=2, failure_threshold=1), event_sink=events.append)
    token = CancellationToken()
    token.cancel()
    cancelled = router.run(lambda: {"status": "accepted"}, token)
    assert cancelled["fallback_reason"] == "cancelled"
    assert events == [{"event": "cancelled", "stage": "before_attempt"}]

    result = router.run(lambda: {"status": "abstain", "fallback_reason": "test"})
    assert result["circuit_opened"] is True
    assert {event["event"] for event in events} == {"cancelled", "circuit_opened"}
    assert router.reset(router.config.config_hash) is True
    router.bypass("test")
    assert [event["event"] for event in events][-2:] == ["reset", "bypass"]
