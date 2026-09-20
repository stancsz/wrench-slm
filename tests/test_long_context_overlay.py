from pathlib import Path


def _load_overlay_source():
    source = Path("runtime/freetoken_wrench_long_context/sitecustomize.py").read_text(encoding="utf-8")
    namespace = {}
    exec(compile(source, "sitecustomize.py", "exec"), namespace)
    return namespace


def test_long_context_overlay_allows_zero_global_full_layers():
    namespace = _load_overlay_source()
    resolve = namespace["_resolve_global_ids"]
    assert resolve((3, 7, 11), "none") == ()
    assert resolve((3, 7, 11), "off") == ()
    assert resolve((3, 7, 11), "7,99") == (7,)
    assert resolve((3, 7, 11), "") == (11,)


def test_long_context_overlay_patches_engine_package_alias_and_swa_only_pool():
    source = Path("runtime/freetoken_wrench_long_context/sitecustomize.py").read_text(encoding="utf-8")
    assert "qwen_family.parse_config = parse_config_with_bounded_full_attention" in source
    assert "zero-layer" in source
    assert "WRENCH_ROPE_MAX_POSITION" in source
    assert "existing_swa_ids" in source
    assert "original group would create two SWA groups" in source
    assert "WRENCH_NATIVE_DIRECT_INPUT" in source
    assert "WRENCH_HISTORY_SKIP_MLP_BEFORE" in source
    assert "WRENCH_HISTORY_SKIP_LAYERS_BEFORE" in source
    assert "WRENCH_HISTORY_CONTROL_PREFIX_TOKENS" in source
    assert "WRENCH_HISTORY_CONTROL_SUFFIX" in source
    assert "history_skip_mlp_before" in source
    assert "history_skip_layers_before" in source
    assert "history_control_prefix_tokens" in source
    assert "history_control_suffix_chars" in source
