# Wrench-SLM goal

This is the short project entry point. The single executable contract is
[`goals/active/selective-offload-real-runtime-v2/GOAL.md`](goals/active/selective-offload-real-runtime-v2/GOAL.md).

## North Star

Let a small local model finish only the routine developer work it can prove,
then fall back with the request intact. A local answer is valuable only when it
is safer or cheaper end to end, not merely smaller.

## Maturity ladder

| Stage | Meaning | Status |
| --- | --- | --- |
| M0: Toy | The idea runs on authored examples. | Done |
| M1: Safe prototype | A bounded read-only path runs without gold data and fails closed. | Done |
| M2: Reproducible candidate | Frozen identity, held-out evaluation, clean-clone checks, and an operator bypass exist. | Done, locally bounded |
| M3: Useful pilot | Representative redacted requests pass intake and a matched A/B/C run shows whether rules or the learned route add value. | Blocked on trusted input data and a provider budget |
| M4: Production candidate | Install, CI, security, observability, recovery, and an operational canary all pass declared thresholds. | Not started |
| M5: Production proven | A time-bounded deployment meets reliability and value SLOs on real traffic with rollback tested. | Not started |

The current decision is **DISABLE learned selective offload by default**. The
observed 90/600 locally accepted cases come from an authored held-out set. They
prove a narrow capability, not production prevalence, savings, or readiness.

## Next gate

Advance M3 only when an authorized, deterministically redacted replay package
contains joinable request context and usage records, its price ledger and time
units pass `scripts/verify_trusted_readiness.py`, and an operator supplies
finite provider attempt and token ceilings. Then run the frozen cloud-only,
rules-plus-fallback, and learned-plus-fallback comparison.

## Sources of truth

- Product direction: [`NORTHSTAR.md`](NORTHSTAR.md)
- System boundary: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Active acceptance contract: [`goals/active/selective-offload-real-runtime-v2/GOAL.md`](goals/active/selective-offload-real-runtime-v2/GOAL.md)
- Production value scorecard: [`docs/PRODUCTION_VALUE_SCORECARD.md`](docs/PRODUCTION_VALUE_SCORECARD.md)
- V21 release evidence: [`docs/reference/MODEL_RELEASE_HANDOFF.md`](docs/reference/MODEL_RELEASE_HANDOFF.md)
