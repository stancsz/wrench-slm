# E0 partial lifecycle trace envelope

Date: 2026-09-24  
Implementation commit: `2e745b2`

## Scope

`src/wrench_harness/e0_lifecycle_accounting.py` adds a bounded structural
envelope joining an `OpenCodePreparationJoin`, a READY semantic context-hook
projection, and a valid finalized outcome receipt. It checks preparation and
accounting integrity, validates the preparation's own incomplete receipt,
reprojects the serialized projection input, and checks the session, snapshot,
context, and preparation-accounting digest joins.

The envelope contains only IDs/references, hashes, schema/version identifiers,
serialized projection-input bytes, and measured/unavailable labels. It labels
the caller's `run_id` as correlation metadata only. Its measured labels are
limited to preparation-facade accounting by receipt reference and the
projection function's local serialization of caller-supplied semantic input.

## Verification

The focused suite `tests/test_e0_lifecycle_accounting.py` passed **6 tests** on
Windows Python 3.11.16 with cached pytest 8.3.5. Independent review confirmed
the preparation-snapshot join check and exact measured/unavailable labels.
`git diff --check` passed. A 5,000,000-byte storage reservation was released;
the checker reported `WITHIN_LIMIT` with all remaining reservations included.

## Limits

This is a structural, caller-supplied join. It does not authenticate any
receipt, establish unique task identity from a session, observe the actual
OpenCode hook event, verify dispatch or a veto, measure the provider request,
count provider tokens or costs, observe tools/retries/auxiliary calls, or
establish task truth. Runtime resources and consent/provenance remain
unavailable. This is partial local evidence only, not full E0 accounting.

See the [independent evaluation](../../evals/wrench-e0-context-pipeline/lifecycle-trace.md)
and [context-pipeline goal](../../goal/wrench-e0-context-pipeline/GOAL.md).
