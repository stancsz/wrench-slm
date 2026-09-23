# Phase 463: screen authorized capture for source locators

Date: 2026-09-24

## Scope

After the user's explicit approval for local review and preparation, a
streaming, hash-bound metadata screen checked the identified capture for
patterns that resemble source line locators. It did not print or persist prompt
or context values. The original capture remains unchanged and quarantined.

## Result

The source hash matched
`3c6e1e549a57d8b02ff20f5dcc27d061766050fa862d542808d9b381387420fe` across
397 parsed records with zero parse failures.

- 56 prompt fields had at least one locator pattern.
- 126 context fields had at least one locator pattern.
- 4 records had patterns in both fields.
- Within prompt fields, 53 records matched an explicit `line N` style and 6
  matched a `path.ext:N` style. The two categories can overlap.
- Within context fields, 45 records matched an explicit `line N` style and
  126 matched a `path.ext:N` style. The two categories can overlap.

The prompt field may contain serialized conversation history, so 56 is a
candidate count, not the number of current user requests that can safely use
`read_lines`. These matches do not establish an in-scope task, current path or
line number, expected output, verifier result, or token savings. This screen
does not authorize replay or training and does not replace privacy or rights
review.

## Evidence

- Reproducible scanner:
  [`audit_capture_locator_prevalence.py`](../../tools/audit_capture_locator_prevalence.py),
  SHA-256 `b55cdf3063455825520b2a5200d4f108c82d8f23a7f1121ae4cde31c7446d9b1`.
- Aggregate-only report on D:
  `D:\wrench-slm-data\quarantine\phase-447-capture-review-2026-09-23\locator-prevalence-v2.json`,
  SHA-256 `65A0BD1B86921889ACC9CDB98E4A8C4B0D92C954777F0348DC6E1B0F51D2E2C4`.
- `ruff check tools/audit_capture_locator_prevalence.py`: passed.
- `python -m py_compile tools/audit_capture_locator_prevalence.py`: passed.
- The output contains counts and hashes only. It records
  `text_values_emitted=false` and `text_values_persisted=false`.

## Next evidence needed

Inspect a reviewed, privacy-cleared sample to identify current user requests
that contain a valid repository-relative path and an exact line range. For
those cases, compare `read_lines` with the current route using the same
independent oracle, and measure task success, verifier results, fallback,
latency, local and frontier tokens, retries, and corrections. Do not change
the route based on this regex screen alone. Gates C and D remain open.
