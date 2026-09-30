# Iteration 110: random-root context-budget diagnostic

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-E0-CONTEXT-BUDGET-SWEEP-ITER110-20260928`  
Status: **REJECTED as reproducible evidence; exploratory results retained from the run log only**  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Observed diagnostic

The first scan found a best observation at context budget 160: baseline 19,289
tokens, prepared 2,076, or 89.237389%. The seven required quotations were
visible in that observed run. Repeated calls at the same nominal budget
produced changing prompt hashes and reductions around 89.02%-89.22%. The
observed coarse pattern was roughly 89% for budgets 154-170, fail-closed
evidence omissions through 171-217, then a lower reduction around 86.9% at
218 and above. These values are preserved as debugging notes, not accepted
metrics: no complete machine-readable per-row receipt or immutable prompt set
was saved for this scan.

## Why it is rejected

`run_demo.py` creates a fresh temporary source root on each call. The snapshot
identity includes that root, so nominally identical repeated calls had
different snapshot and prepared-prompt identities. A selected prompt hash
changed between repeats. That means this scan did not compare the same frozen
input and cannot establish a reproducible maximum. The apparent 89.237389%
observation is not the accepted Wrench result.

The follow-up [Iteration 111 stable-root sweep](iteration-111-stable-context-budget-sweep-20260928.md)
used a persistent source root, recorded all 897 budgets and failures in a
hash-bound receipt, and repeated the winning settings three times. Its
reproducible result is 89.227021% prompt-input reduction across the same three
synthetic cases. That remains a prompt proxy and does not count as frontier
token savings or task success.

## Accounting and disposition

The diagnostic used reservation
`WRENCH-E0-CONTEXT-BUDGET-SWEEP-ITER110-20260928` for 100,000,000 bytes.
No usable machine-readable receipt was persisted; the transcript-level
observation and rejection reason are the retained record. Do not tune or claim
against the sealed held-out split based on this exploratory run.
