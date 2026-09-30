from examples.gateway_context_mvp.run_code_task_local_mvp_iter209 import verify_code_task


CONFIG = """
[retry]
initial_backoff_ms = 250
max_backoff_ms = 4000
"""


def test_safe_retry_code_passes_config_boundaries() -> None:
    code = """def calculate_retry_delay(attempt, initial_backoff_ms, max_backoff_ms):
    return min(max_backoff_ms, initial_backoff_ms * (2 ** max(0, attempt)))
"""
    result = verify_code_task(code, CONFIG)
    assert result["passed"] is True
    assert len(result["cases"]) == 6


def test_code_verifier_rejects_syntax_and_unsafe_calls() -> None:
    syntax = verify_code_task("def calculate_retry_delay(:", CONFIG)
    unsafe = verify_code_task(
        "def calculate_retry_delay(attempt, initial_backoff_ms, max_backoff_ms):\n    return __import__('os').system('whoami')\n",
        CONFIG,
    )
    assert syntax["reason"] == "syntax_error"
    assert unsafe["reason"] in {"unsafe_or_unsupported_syntax", "unexpected_identifier", "disallowed_call"}
