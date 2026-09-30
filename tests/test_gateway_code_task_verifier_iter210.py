from examples.gateway_context_mvp.run_code_task_local_mvp_iter210 import verify_code_task


CONFIG = """
[retry]
initial_backoff_ms = 250
max_backoff_ms = 4000
"""


def test_safe_fenced_function_with_docstring_annotations_and_local_assignment() -> None:
    code = """```python
def calculate_retry_delay(attempt: int, initial_backoff_ms: int, max_backoff_ms: int) -> int:
    \"\"\"Return capped retry delay.\"\"\"
    delay = initial_backoff_ms * (2 ** max(0, attempt))
    return min(delay, max_backoff_ms)
```
"""
    result = verify_code_task(code, CONFIG)
    assert result["passed"] is True
    assert result["response_format"] == "single_python_fence_removed"
    assert len(result["cases"]) == 6


def test_verifier_keeps_negative_attempt_behavior_and_safe_ast_checks() -> None:
    negative_case_bug = """def calculate_retry_delay(attempt, initial_backoff_ms, max_backoff_ms):
    delay = initial_backoff_ms * (2 ** attempt)
    return min(delay, max_backoff_ms)
"""
    unsafe = """def calculate_retry_delay(attempt, initial_backoff_ms, max_backoff_ms):
    return __import__('os').system('whoami')
"""
    mismatch = verify_code_task(negative_case_bug, CONFIG)
    rejected = verify_code_task(unsafe, CONFIG)
    assert mismatch["passed"] is False
    assert mismatch["reason"] == "behavior_mismatch"
    assert rejected["passed"] is False
    assert rejected["reason"] in {
        "unsafe_or_unsupported_syntax", "unexpected_identifier", "disallowed_call"
    }


def test_iter209_saved_outputs_expose_v1_verifier_grammar_defect() -> None:
    baseline_first = """```python
def calculate_retry_delay(attempt: int, initial_backoff_ms: int, max_backoff_ms: int) -> int:
    \"\"\"Return exponential backoff in milliseconds for a zero-based attempt, capped at max_backoff_ms.\"\"\"
    delay = initial_backoff_ms * (2 ** max(0, attempt))
    return min(delay, max_backoff_ms)
```
"""
    wrench_first = """def calculate_retry_delay(attempt: int, initial_backoff_ms: int, max_backoff_ms: int) -> int:
    \"\"\"Return exponential backoff in milliseconds for a zero-based attempt, capped at max_backoff_ms.\"\"\"
    delay = initial_backoff_ms * (2 ** max(0, attempt))
    return min(delay, max_backoff_ms)
"""
    failed_retry = """def calculate_retry_delay(attempt: int, initial_backoff_ms: int, max_backoff_ms: int) -> int:
    delay = initial_backoff_ms * (2 ** attempt)
    return min(delay, max_backoff_ms)
"""
    assert verify_code_task(baseline_first, CONFIG)["passed"] is True
    assert verify_code_task(wrench_first, CONFIG)["passed"] is True
    assert verify_code_task(failed_retry, CONFIG)["reason"] == "behavior_mismatch"
