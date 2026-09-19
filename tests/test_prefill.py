from wrench_harness.prefill import MechanicalPrefillIndex, build_dynamic_prefill, build_lossless_structured_prefill


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
