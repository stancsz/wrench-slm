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
    assert "WRENCH_EMBEDDED_MECHANICAL_ROUTE" in source
    assert "proposal_only_external_verifier_required" in source
    assert "history_skip_mlp_before" in source
    assert "history_skip_layers_before" in source
    assert "history_control_prefix_tokens" in source
    assert "history_control_suffix_chars" in source


def test_reference_lookup_card_promotes_only_exact_old_matches():
    namespace = _load_overlay_source()
    build_card = namespace["_build_reference_lookup_card"]
    old = (
        "irrelevant historical record\n" * 40
        + "symbol=needle_symbol path=src/worker.py line=218\n"
        + "irrelevant historical record\n" * 40
    )
    tail = 'Find "needle_symbol" in the old reference and keep the newest intent.'
    card = build_card(old + tail, tail, max_chars=1200, max_hits=4)
    assert card["status"] == "hit"
    assert any("needle_symbol" in match["line"] for match in card["matches"])
    assert len(card["rendered"]) <= 1200
    assert build_card(old + "no such token", "no such token")["status"] == "no_hit"


def test_reference_lookup_card_can_form_a_bounded_read_hint():
    namespace = _load_overlay_source()
    build_card = namespace["_build_reference_lookup_card"]
    hint = namespace["_reference_proposal_hint"]
    old = "historical lookup symbol=run_worker path=src/worker.py\n"
    tail = 'Inspect the source for symbol "run_worker" with a 4096 byte limit.'
    card = build_card(old + tail, tail)
    assert hint(tail, card) == {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "src/worker.py",
        "max_bytes": 4096,
    }


def test_embedded_read_hint_is_bounded_and_relative():
    namespace = _load_overlay_source()
    hint = namespace["_mechanical_read_hint_from_tail"]
    assert hint("Read file src/worker.py with a 4096 byte limit.") == {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "src/worker.py",
        "max_bytes": 4096,
    }
    assert hint("Read file C:/secret.txt with a 4096 byte limit.")["path"] == "C:/secret.txt"
