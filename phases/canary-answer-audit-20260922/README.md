# Saved canary answer audit

The user selected the current deterministic worker versus the stronger-model
baseline as the first productive-value comparison. Learned-model comparison
remains outside this cycle.

The existing hybrid canary inferred correctness from a smoke-level read flag.
The runner now checks each client's saved answer against the expected bounded
observation, with the same check on the direct baseline. Tool-event echoes,
exit-zero-without-answer, wrong final text, timeout, and failed exit cannot
pass. The first-heading oracle is deliberately conservative. It is not a
general semantic judge for arbitrary tasks.

Rechecking the actual Phase 389 outputs found:

| Client | Expected heading observed |
| --- | --- |
| OpenCode | No |
| DeepSeek Harness | Yes |
| Claude Code | Yes |

The old source smoke says `PASSED`. The independent output audit says
`FAIL_SAVED_CLIENT_ANSWER_CHECK`. `receipt.json` binds the original receipt and
all output files by SHA-256. No client or provider was launched by this audit.

The paired runner also stops counting ordinary final-answer rows as
corrections. Actual corrections remain unknown until captured. Accounting
remains incomplete; this does not establish a canary pass or cost savings.

Reproduction, expected exit code 1 because the saved OpenCode answer is absent:

```powershell
python tools/canary_answer_check.py `
  --receipt-dir phases/phase-389-accounting-gate/receipt-hybrid `
  --expected '# Wrench SLM' `
  --output phases/canary-answer-audit-20260922/receipt.json
```

Focused regression: `18 passed` across `test_canary_answer_check.py` and
`test_paired_client_canary.py`. The actual saved Windows CRLF output was
rechecked after fixing the oracle's line-ending handling.
Full repository regression: `237 passed, 18 warnings in 24.87s`.
`git diff --check` passed. No commit, provider spending, or publication occurred.

The next value experiment should start with identical DeepSeek Harness runs
on both arms. This isolates the working client for an initial measurement;
it does not waive OpenCode or Claude Code release acceptance. The existing
all-client smoke is not a matched latency comparator. Actual provider usage,
same-client end-to-end timing, fallback and correction accounting, and the
authorized workload and spending boundary still need to be completed before
the real paired run.
