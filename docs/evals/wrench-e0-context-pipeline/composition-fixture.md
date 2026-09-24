# Authored synthetic E0 composition fixture

Goal: [E0 caller-owned context preparation](../../goal/wrench-e0-context-pipeline/GOAL.md)

Reviewed revision: `ac9413a`, Windows, Python 3.11.16, pytest 8.3.5.

Implementer/supervisor: `e0_composition_supervisor`; integrated and accepted by the orchestrator. Independent critic: `e0_composition_critic`. Independent verifier: `e0_composition_verifier`. Both reviewers inspected the actual test and its invoked helper/API without editing or running code.

## Observed behavior

`test_authored_synthetic_composition_keeps_valid_prompt_and_records_non_text_omission` creates two Wrench-authored files, snapshots them, then invokes the real `prepare_e0_context` facade through the existing `_invoke` fixture helper. The text evidence remains selected and required; an opaque binary input is omitted as `non_text`, yielding overall `SOURCE_MISSES` while the local prompt gate is `READY`. The receipt reports route `none`, no attempts, unknown outcome, and only the outcome field missing. The fixture verifies the accounting receipt against the preparation hash and asserts zero direct facade model, provider, verifier, and tool call-site counters.

The independent verifier confirmed that `SOURCE_MISSES` is assigned after prompt compilation when the miss list is nonempty, so the READY prompt and omission receipt are internally consistent. The critic agreed that this is a useful narrow mechanics regression.

## Verification

The supervisor ran the focused test on Windows Python 3.11.16 with cached pytest 8.3.5: **1 passed in 0.84s**. `git diff --check` passed. The test was committed as `ac9413a`.

Storage job `W2-NS-E0-COMPOSE-20260924` reserved 10,000,000 bytes and released its own reservation after testing. The post-job checker reported `WITHIN_LIMIT`, 654,114,954 actual bytes, 103,000 bytes in other active reservations, and 49,345,782,045 projected headroom.

## Scope and remaining work

This is one synthetic Wrench preparation path. It does not execute a task, freeze/check a task outcome oracle, compare a downstream baseline, measure customer value, assert artifact readback or pin lifetime, or prove zero external activity. The serializer and character counter are injected fixtures, not OpenCode/provider runtime parity. Facade counters are local call-site counts, not request-wide lifecycle accounting. No OpenCode hook, client dispatch veto, provider, or model was run. This test does not establish E0 or E4 acceptance.

Next E0 work remains a verified runtime-boundary gate and complete request accounting, subject to approved integration and data authority. The full E0 acceptance criteria remain in [V2_EXPERIMENT.md](../../northstar/V2_EXPERIMENT.md).
