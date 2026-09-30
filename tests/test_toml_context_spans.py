from __future__ import annotations

from wrench_harness.toml_context_spans import extract_toml_key_spans, extract_toml_table_spans


def test_valid_toml_returns_query_ranked_exact_key_lines():
    source = (
        "[auth]\n"
        "session_timeout_seconds = 1800\n"
        "refresh_before_expiry_seconds = 300\n"
        "cookie_name = \"wrench_session\"\n"
        "\n"
        "[retry]\n"
        "max_retries = 3\n"
        "initial_backoff_ms = 250\n"
    )

    spans = extract_toml_key_spans(source, "session timeout refresh before expiry")

    assert {span.name for span in spans} == {
        "auth.session_timeout_seconds",
        "auth.refresh_before_expiry_seconds",
    }
    assert {span.start_line for span in spans} == {2, 3}
    assert all(span.end_line == span.start_line for span in spans)
    assert {span.text for span in spans} == {
        "session_timeout_seconds = 1800\n",
        "refresh_before_expiry_seconds = 300\n",
    }
    assert all(span.match_score >= 2 for span in spans)


def test_invalid_multiline_or_unrecognized_toml_fails_closed():
    assert extract_toml_key_spans("[auth\nsession_timeout = 1\n", "session timeout") == ()
    assert extract_toml_key_spans(
        '[auth]\nnotice = """\n[retry]\nthis is string data\n"""\n',
        "retry",
    ) == ()
    assert extract_toml_key_spans(
        "[[servers]]\nname = \"api\"\n", "servers api"
    ) == ()


def test_unmatched_query_returns_no_span_for_whole_file_fallback():
    source = "[auth]\nsession_timeout_seconds = 1800\n"

    assert extract_toml_key_spans(source, "database pool size") == ()


def test_table_spans_keep_header_and_all_assignments_in_matching_table():
    source = (
        "[auth]\n"
        "session_timeout_seconds = 1800\n"
        'cookie_name = "wrench_session"\n'
        "\n"
        "[retry]\n"
        "max_retries = 3\n"
        "session_timeout_seconds = 45\n"
    )

    spans = extract_toml_table_spans(source, "auth session timeout")

    by_name = {span.name: span for span in spans}
    assert set(by_name) == {"auth", "retry"}
    assert (by_name["auth"].start_line, by_name["auth"].end_line) == (1, 4)
    assert "[auth]\nsession_timeout_seconds = 1800\ncookie_name = \"wrench_session\"" in by_name["auth"].text
    assert "[retry]\nmax_retries = 3\nsession_timeout_seconds = 45" in by_name["retry"].text


def test_table_spans_fail_closed_for_valid_but_unsupported_toml():
    assert extract_toml_table_spans(
        "[auth]\nmessage = \"\"\"\n[retry]\ntext\n\"\"\"\n", "auth retry"
    ) == ()
    assert extract_toml_table_spans("[[servers]]\nname = \"api\"\n", "servers api") == ()
    assert extract_toml_table_spans("[auth]\nitems = [\n  1,\n  2,\n]\n", "auth items") == ()


def test_table_spans_do_not_repeat_table_name_as_multiple_query_matches():
    source = (
        "[retry]\n"
        "retry_statuses = [429, 502]\n"
        "max_retries = 3\n"
        "initial_backoff_ms = 250\n"
        "\n"
        "[http]\n"
        "connect_timeout_seconds = 5\n"
        "read_timeout_seconds = 25\n"
    )

    spans = extract_toml_table_spans(source, "HTTP 429 retry initial backoff")

    assert [span.name for span in spans] == ["retry"]
