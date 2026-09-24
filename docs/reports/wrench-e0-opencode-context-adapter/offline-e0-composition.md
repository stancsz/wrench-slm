# Synthetic offline E0 composition

- Date: 2026-09-24
- Job: `W2-NS-E0-OFFLINE-COMPOSITION-20260924`
- Nonce: `E0OC-5A80`
- Base HEAD: `cef6947b8b892bd25fb9a85ca217fd892e013767`
- Status: implemented and independently reviewed; committed as `69309d7e8312a107d2a42015e1f595ef619fc248`

## Behavioral contract

`prepare_offline_e0_request` composes an enrolled-project snapshot, deterministic
structural candidate preparation, exact snapshot retrieval and ArtifactStore
roundtrip, existing E0 context preparation, prepared-context materialization,
lowering to Chat Completions string-content messages, and the existing fixture
request/lease boundary. The lowered fixture request carries the exact prepared
context message once. A digest-only receipt joins source/candidate selection,
preparation, insertion, and final request-body hashes. Serializer and tokenizer
IDs identify synthetic fixture implementations; the exact-token gate is
unavailable.

Pins remain held through request stream cleanup. Non-ready preparation and
pre-lease failures do not issue a request. A timer-start failure removes the
pending lease, consumes the nonce, marks the lease failed, and releases the
owner callback once. Active timeout requests cancellation and retains the pins
until writer cleanup. The fixture uses an ephemeral loopback port and does not
forward upstream.

## Verification

The focused test module was invoked directly with the existing CPython 3.11
environment because `pytest` is unavailable in that interpreter:

```powershell
@'
import sys
sys.path.insert(0, 'tests')
import test_e0_offline_request_composition as tests

tests.test_compiler_message_reaches_loopback_request_and_pins_release_at_eof()
tests.test_non_ready_preparation_never_issues_request_or_retains_pins()
tests.test_invalid_fixture_response_fails_before_lease_creation()
tests.test_timer_start_failure_rolls_back_pending_lease_and_releases_once()
tests.test_boundary_rejection_consumes_lease_and_runs_release_once()
tests.test_materialization_and_lowering_failures_leave_no_lease_or_pins()
tests.test_active_timeout_keeps_composition_pins_until_writer_cleanup()
print('7 focused tests passed')
'@ | & .\.venv\Scripts\python.exe -
```

Result: **7 focused tests passed**, exit code 0. `git diff --check` passed.
Independent reviewer `offline_composition_review` returned **PASS** for the
composition, timer-start rollback, and final EOF callback-count assertion. The
reviewer confirmed the successful loopback cleanup invokes each scope's
release callback exactly once. Their non-blocking coverage gap is that direct
cancellation and writer failure/disconnect without timeout are not separately
exercised by this composition module; runtime token parity remains unavailable.

## Artifact hashes

SHA-256:

| File | SHA-256 |
| --- | --- |
| `src/wrench_harness/e0_offline_request_composition.py` | `57568764878533FED13D5C04AE949A0990D07571A16D5673FCBDF13C63BA1583` |
| `src/wrench_harness/opencode_request_boundary.py` | `69BC2578A9276780B2CCC966037BDED3793F1CBD44AF61158D8A47B8D502FB16` |
| `tests/test_e0_offline_request_composition.py` | `269FA463074B92E7CF560231E1F81DEDFF27B340EE2A961EE5C9780E41756E93` |

## Resource accounting and limits

The assigned 20,000,000-byte storage reservation was active during focused
verification. Before release, storage status was `WITHIN_LIMIT`, with
1,715,162,028 bytes actual and 20,103,000 bytes across active reservations.
C: had 173,049,282,560 bytes free. RAM free was 55.83%; the NVIDIA RTX 5060 Ti
had 15,583 MiB of 16,311 MiB free. After all tests, review, and documentation
accounting, the job reservation was released. Final storage status was
`WITHIN_LIMIT`, with 1,715,160,683 bytes actual and 103,000 bytes reserved by
other jobs.

This evidence is limited to synthetic offline fixtures. No real source tree,
OpenCode client/plugin, localhost:4000, gateway, provider, credential, prompt,
or network request was used. It does not prove runtime serializer/tokenizer
parity, dispatch denial, full lifecycle accounting, customer utility, or E0/E4
completion. Direct cancel, writer failure, or disconnect without timeout are
not separately exercised by this composition module, and a partially started
timer thread is handled by inspection rather than a dedicated fixture. No
commit was made by this job.

## Follow-up

The source, tests, and documentation in this report were integrated in commit
`69309d7e8312a107d2a42015e1f595ef619fc248`. The later
[rule-route-to-lease slice](offline-route-to-lease.md) carries deterministic
rule-route evidence through this fixture request boundary and records terminal
cleanup. Runtime integration, full accounting, E0/E4 acceptance, and exact-token
parity remain open.
