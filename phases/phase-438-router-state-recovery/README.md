# Phase 438: fail-closed router-state recovery

Date: 2026-09-22

## Decision and scope

Harden the existing schema- and configuration-hash-bound router-state loader
so an inconsistent persisted snapshot cannot silently restore an unsafe
router state. The change is limited to local state validation and tests. It
does not enable production routing, alter the serving lifecycle, or launch
another soak.

## Finding and change

Before the change, `load_router_state` validated the schema, configuration
hash, counter types, and flag types, but accepted internally inconsistent
snapshots. The new regression suite demonstrated eight accepted invalid
shapes, including attempts above the configured ceiling, failures greater
than attempts, an enabled open circuit, a circuit inconsistent with its
failure threshold, and invalid bypass metadata.

The loader now rejects snapshots unless attempts stay within the configured
ceiling, failures do not exceed attempts, circuit state agrees with the
failure threshold and enabled flag, and bypass metadata is consistent with
the enabled state. Valid open-circuit and operator-bypass snapshots remain
recoverable. After restoration, the open circuit abstains without invoking the
callback until a reset with the exact configuration hash.

## Verification

- Before the loader change, the new suite reported 8 failures and 1 pass. The
  failures confirmed each malformed snapshot was accepted.
- Focused router-state plus harness tests: 29 passed.
- Full repository suite: 334 passed, with 18 existing Windows asyncio
  deprecation warnings, in 45.81 seconds.
- Ruff passed for the changed state loader and new tests.
- Q4 collaboration contract validation returned `VALID`.
- `git diff --check` and `git diff --cached --check` passed.
- No provider request, credential access, model inference, or paid spend
  occurred. No sustained soak was run.

## Source identity

- Base `HEAD`: `b383306771e7d434397c539711f30e4e678455e9`
- `src/wrench_harness/state.py` SHA-256:
  `8ba4e879d77f1959286c8c6bfcfe8dc23e45bac5484655dc86f2bcee8271196a`
- `tests/test_router_state.py` SHA-256:
  `7160277e3c9feec8cce2d047eac76ce4c7dd451cf407ef9841eb7c6503086ce5`

The checkout also contains unrelated staged and unstaged changes. This phase
was not committed, and no unrelated changes were staged or reverted.

## Evidence boundary and remaining gap

These tests cover the persistence helper across `ProposalRouter` object
reconstruction. They do not show that the live server persists or reloads
router state, do not exercise a model-worker process restart, and do not
establish Gate E acceptance. Production routing remains disabled. Gate E still
needs restart and recovery evidence through the authorized serving lifecycle,
full accounting and no-mutation checks, and sustained operational evidence.

## Next decision

Continue with repository-only, deterministic checks that do not broaden the
approved test boundary. Any production-equivalent router integration,
provider call, additional soak, or routing enablement remains subject to its
Q4 authorization and the active stop conditions in `GOAL.md`.
