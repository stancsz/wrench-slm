from wrench_harness.prefill import (
    MechanicalPrefillIndex,
    build_dynamic_prefill,
    build_lossless_structured_prefill,
    split_monolithic_current_message,
)


def test_structured_prefill_keeps_current_intent_and_all_reference_text():
    messages = [
        {"role": "system", "content": "bounded worker"},
        {"role": "user", "content": "old lookup: symbol Foo"},
        {"role": "assistant", "content": "old observation"},
        {"role": "user", "content": "read the newest file"},
    ]
    structured, receipt = build_lossless_structured_prefill(messages)
    rendered = "\n".join(message["content"] for message in structured)
    assert "old lookup: symbol Foo" in rendered
    assert "old observation" in rendered
    assert "read the newest file" in rendered
    assert receipt["lossless"] is True
    assert receipt["omitted_messages"] == []


def test_structured_prefill_rejects_missing_current_intent():
    try:
        build_lossless_structured_prefill([{"role": "system", "content": "only policy"}])
    except ValueError as exc:
        assert "current user intent" in str(exc)
    else:
        raise AssertionError("expected validation failure")


def test_dynamic_prefill_keeps_hot_context_and_makes_old_lookup_cards():
    messages = [
        {"role": "system", "content": "bounded worker"},
        {"role": "user", "content": ("old file src/service.py class Worker\nAssertionError timeout " * 40)},
        {"role": "assistant", "content": ("old observation repeated stale lookup " * 40)},
        {"role": "user", "content": "recent tool state path src/main.py"},
        {"role": "user", "content": "read the newest file"},
    ]
    staged, receipt = build_dynamic_prefill(
        messages,
        token_counter=lambda value: len(value.split()),
        model_prefill_budget=1_000,
        hot_token_budget=6,
        include_lookup_table=True,
    )
    rendered = "\n".join(message["content"] for message in staged)
    assert "read the newest file" in rendered
    assert receipt["reference_card_count"] >= 1
    assert receipt["raw_token_count"] > receipt["model_prefill_token_count"]
    assert receipt["native_input_claim"] is False
    assert receipt["lookup_table"]


def test_dynamic_prefill_is_deterministic_for_same_payload():
    messages = [
        {"role": "user", "content": "old lookup " * 1000},
        {"role": "user", "content": "current intent"},
    ]
    first = build_dynamic_prefill(messages, token_counter=lambda value: len(value.split()), model_prefill_budget=10_000, hot_token_budget=8)[1]
    second = build_dynamic_prefill(messages, token_counter=lambda value: len(value.split()), model_prefill_budget=10_000, hot_token_budget=8)[1]
    assert first["raw_payload_sha256"] == second["raw_payload_sha256"]
    assert first["lookup_table"] == second["lookup_table"]


def test_mechanical_index_reuses_cards_for_fresh_http_message_objects():
    source = {"role": "user", "content": "src/service.py class Worker AssertionError timeout"}
    index = MechanicalPrefillIndex(token_counter=lambda value: len(value.split()))
    first = index.add(source)
    fresh = {"role": "user", "content": source["content"]}
    second = index.add(fresh)
    assert first is second
    assert index.entry(fresh) is first
    assert index.token_count(fresh) == 5


def test_dynamic_prefill_embeds_bounded_ast_and_dependency_evidence():
    messages = [
        {
            "role": "assistant",
            "content": (
                "Reference path src/service.py\n"
                "```python\n"
                "import pathlib\n"
                "class Worker:\n"
                "    def run_worker(self):\n"
                "        return pathlib.Path('README.md')\n"
                "```"
            ),
        },
        {"role": "user", "content": "Inspect Worker.run_worker in src/service.py."},
    ]
    staged, receipt = build_dynamic_prefill(
        messages,
        token_counter=lambda value: len(value.split()),
        model_prefill_budget=120,
        hot_token_budget=8,
    )
    rendered = "\n".join(message["content"] for message in staged)
    assert receipt["reference_card_count"] == 1
    assert "ast_symbols" in rendered
    assert "run_worker" in rendered
    assert "pathlib" in rendered


def test_dynamic_prefill_preserves_specific_old_lookup_evidence():
    messages = [
        {
            "role": "assistant",
            "content": "historical symbol run_worker path=src/wrench_harness/worker.py line=218\n" + ("stale context\n" * 80_000),
        },
        {"role": "user", "content": "Inspect symbol run_worker in src/wrench_harness/worker.py."},
    ]
    index = MechanicalPrefillIndex()
    index.add_all(messages)
    staged, receipt = build_dynamic_prefill(
        messages,
        model_prefill_budget=64_000,
        hot_token_budget=48_000,
        mechanical_index=index,
    )
    rendered = "\n".join(message["content"] for message in staged)
    assert receipt["reference_card_count"] == 1
    assert "src/wrench_harness/worker.py" in rendered
    assert "run_worker" in rendered


def test_dynamic_prefill_skips_ast_for_monster_reference():
    messages = [
        {"role": "assistant", "content": "class Worker:\n" + ("stale context\n" * 20_000)},
        {"role": "user", "content": "Inspect Worker in src/service.py."},
    ]
    _, receipt = build_dynamic_prefill(
        messages,
        token_counter=lambda value: len(value.split()),
        model_prefill_budget=120,
        hot_token_budget=8,
    )
    assert receipt["reference_card_count"] == 1


def test_dynamic_prefill_skips_full_text_query_scan_without_specific_lookup_term():
    messages = [
        {"role": "assistant", "content": "stale context\n" * 100_000},
        {"role": "user", "content": "Read the newest file and return a bounded proposal."},
    ]
    index = MechanicalPrefillIndex()
    index.add_all(messages)
    _, receipt = build_dynamic_prefill(
        messages,
        model_prefill_budget=64_000,
        hot_token_budget=48_000,
        mechanical_index=index,
    )
    assert receipt["reference_card_count"] == 1


def test_split_monolithic_current_message_preserves_old_prefix_as_reference():
    payload = "old reference\n" + ("stale context\n" * 20_000) + "CURRENT INTENT: read README.md"
    prepared, split = split_monolithic_current_message(
        [{"role": "user", "content": payload}],
        model_prefill_budget=1_000,
        suffix_chars=128,
    )
    assert split is True
    assert prepared[0]["role"] == "assistant"
    assert "old reference" in prepared[0]["content"]
    assert prepared[1]["role"] == "user"
    assert "CURRENT INTENT: read README.md" in prepared[1]["content"]
    assert len(prepared[1]["content"]) == 128
