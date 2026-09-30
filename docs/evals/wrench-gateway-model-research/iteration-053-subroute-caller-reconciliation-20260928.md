# Iteration 053: reconcile the SubRoute caller path (2026-09-28)

## Current source identity

The SubRoute teacher-capture path is already implemented in
`tools/capture_subroute_teacher_traces.py`, with campaign admission and the
shared SQLite ledger in `tools/subroute_budget_guard.py`. This is a distinct
path from the older `tools/capture_minimax_teacher_traces.py`, whose direct
OpenRouter transport should not be mistaken for SubRoute routing.

The bounded capture emits `wrench.mechanical-worker-teacher-traces.v1`, which
`tools/run_diagnostic_worker_arms.py` accepts through its `--teacher-traces`
replay path. The source requires human approval tied to the current Git HEAD,
caller-bundle hash, and exact synthetic case hash; it reserves worst-case
request cost in the campaign ledger before dispatch; requests disable retries
and fallbacks; and settlement checks selected provider/model identity,
generation ID, token counts, and billed cost. Unresolved requests retain the
full reserve and block later dispatch.

The exact current hashes match the source-only Iteration 033/036 receipts:

| File | SHA-256 |
| --- | --- |
| `tools/capture_subroute_teacher_traces.py` | `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6` |
| `tools/subroute_budget_guard.py` | `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B` |
| `tests/test_subroute_budget_guard.py` | `62B8C3BFE58A0D46BE2189C766DF1FB348540A9A5B1A6363E64DF5076A8801B9` |
| `tools/run_diagnostic_worker_arms.py` | `91C028A6C10C921973DC4734B75D0ADD90EC4AEF15340D3F963627935336EBE1` |

## Verification and remaining gaps

The test file contains a mock-transport capture case and a missing-approval
case. Those tests were not run against this host during this iteration. The
source-only SubRoute review established that its adapter maps provider
controls into the final OpenRouter body, but the real inbound HTTP metadata
handoff to that transformer has not been demonstrated. No public-provider
request, billing receipt, model-quality result, or Wrench LoRA evaluation is
claimed here.

The hourly heartbeat `wrench-hourly-token-reduction-monitor` was updated in
place and confirmed ACTIVE/hourly. Its next gates now point to the existing
hash-bound SubRoute caller tests, provider-control metadata verification
without upstream transport, and isolated no-provider OpenCode v2.0.12 request
capture. It preserves the under-10B candidate scope, 95% acceptance criteria,
10% resource floor, 25% LoRA start requirement, and no-spend rule until a
numeric campaign cap and current approval exist.

At the live sample, free RAM was 3,353.1 / 32,701.8 MiB (10.25%). This is only
0.25 percentage points above the 10% reserve, so no tests, runtime, inference,
training, benchmark, packaging, or delegated job ran. No provider POST or
credential read occurred. Storage including SubRoute and the automation
directory remained below the 50 GB decimal limit.

## Disposition

The correct bounded caller is identified and its source contract is linked to
the diagnostic replay schema. Runtime correctness, local learning, end-to-end
metadata handling, 95/5 completion, 95% frontier-token reduction, 95% all-in
cost reduction, and all-day engineering remain unproven. Keep the goal active.
