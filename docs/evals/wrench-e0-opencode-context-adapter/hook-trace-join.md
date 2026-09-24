# OpenCode hook observation lifecycle join evaluation

Job: `W2-NS-E0-HOOK-TRACE-JOIN-20260925`, nonce `HTRACE-31C9`  
Base commit: `6b651a159ad737a803dd506bb01b23a30a97cc4e`

## Result

Independent review passed with no blocking findings. Review covered concurrent
row ordering, strict observation validation, timing/count invariants, getter
purity limits, and conditional envelope schema versions. The two focused test
modules passed **89 tests in 5.98 seconds** using the existing Python 3.11.16
and pytest environment. `git diff --check` passed.

Coverage includes scoped digest collection; ordinary and `BaseException`
getter failures that do not prevent callback invocation; successful trace
joining; v4 compatibility when the optional observation is omitted; v5 when
it is included; observation schema v2; and rejection of unscoped,
mixed-session, incomplete, capped, saturated, timing-inconsistent, and
schema/version-mismatched observations, including hostile equality values.

## Scope and limits

The observer and trace builder provide bounded structural evidence only. The
session getter is caller supplied and must be side-effect-free because it sees
the original invocation arguments. The observation is unauthenticated and does
not prove OpenCode actually ran the hook, applied a mutation, or dispatched a
request. Runtime provenance, atomic capture, dispatch enforcement, final
provider request and tokenizer parity, and overall E0 acceptance remain open.
No client, prompt, provider request, inference, or deployment was used.

The storage checker finished `WITHIN_LIMIT` at **1,710,537,759 actual bytes**
with **103,000 bytes** in other active reservations. This job released its
5,000,000-byte reservation after final accounting. `uv.lock` was preserved.

See the [implementation report](../../reports/wrench-e0-opencode-context-adapter/hook-trace-join.md)
and [E0 context-pipeline goal](../../goal/wrench-e0-context-pipeline/GOAL.md).
