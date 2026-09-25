# Explicit-operation M3 proxy 01: superseded before measurement

Status: pre-measurement review found an eligibility-check defect; zero cases
run.
Date: 2026-09-25 (America/Edmonton)
Preregistered job: `LOCAL-M3-OPS-PROXY-20260925-01`
Repository revision: `51c610d412bfc1aa20531a3cdf7393012aba0c36`.

Before invoking the tokenizer, root review found that `_render_untrusted_context`
JSON-quotes the assembled source text. The original eligibility check searched
the escaped wrapper for literal source bytes, which would falsely exclude valid
cases. The check also needed to compare the actual route result to the frozen
operation mechanics before token scoring. No case was run and no measurement
receipt was created. The 8 MB reservation was released.

The runner now decodes the untrusted-context payload and validates the route
against the frozen operation observation before deciding evidence completeness.
That corrected code and a fresh job identity are preregistered in
[protocol 02](operation-prompt-m3-token-proxy-protocol-02.md).
