from __future__ import annotations

import json
from pathlib import Path

from tools.materialize_long_context_artifact import materialize


def test_materialize_long_context_artifact_does_not_copy_weights(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "config.json").write_text(
        json.dumps({"model_type": "qwen3_5_moe", "text_config": {"max_position_embeddings": 262144, "rope_parameters": {}}}),
        encoding="utf-8",
    )
    (source / "model.safetensors").write_bytes(b"immutable")
    (source / "tokenizer.json").write_text("{}", encoding="utf-8")
    receipt = materialize(source, target, 2_000_000)
    assert receipt["weights_copied"] is False
    assert receipt["weight_link_count"] == 1
    assert json.loads((target / "config.json").read_text(encoding="utf-8"))["text_config"]["max_position_embeddings"] == 2_000_000
    assert (source / "model.safetensors").read_bytes() == (target / "model.safetensors").read_bytes()
