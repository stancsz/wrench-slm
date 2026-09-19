from __future__ import annotations

from tools.prepare_native_context_config import prepare_config


def test_native_context_config_preserves_architecture_and_scales_rope():
    source = {
        "model_type": "qwen3_5_moe",
        "text_config": {
            "max_position_embeddings": 262144,
            "rope_parameters": {"rope_type": "default", "rope_theta": 10000000},
        },
    }
    candidate = prepare_config(source, 2_000_000)
    assert candidate["model_type"] == source["model_type"]
    assert candidate["text_config"]["max_position_embeddings"] == 2_000_000
    assert candidate["text_config"]["rope_parameters"]["original_max_position_embeddings"] == 262144
    assert candidate["text_config"]["rope_parameters"]["factor"] == 2_000_000 / 262144
    assert source["text_config"]["max_position_embeddings"] == 262144


def test_native_context_config_rejects_shrinking_context():
    source = {
        "text_config": {
            "max_position_embeddings": 262144,
            "rope_parameters": {},
        }
    }
    try:
        prepare_config(source, 128000)
    except ValueError as exc:
        assert "smaller" in str(exc)
    else:
        raise AssertionError("shrinking a native context config was accepted")
