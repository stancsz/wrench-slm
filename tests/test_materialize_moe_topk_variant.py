from pathlib import Path


def test_topk_variant_materializer_is_weight_identical_and_fail_closed():
    script = Path("tools/materialize_moe_topk_variant.py").read_text(encoding="utf-8")
    assert "DERIVED_CONFIG_WEIGHT_IDENTICAL" in script
    assert "weights_changed" in script
    assert "parameter_count_changed" in script
    assert "refusing to overwrite existing target" in script
    assert 'num_experts_per_tok"] = top_k' in script


def test_topk_variant_materializer_copies_embedded_runtime_directories():
    script = Path("tools/materialize_moe_topk_variant.py").read_text(encoding="utf-8")
    assert "item.is_dir()" in script
    assert "shutil.copytree(item, destination)" in script
