# Synthetic offline rule-route to request lease

- Date: 2026-09-24 (America/Edmonton)
- Job: `W2-NS-E0-ROUTE-TO-LEASE-20260924`
- Nonce: `R2L-94F3`
- Base HEAD: `69309d7e8312a107d2a42015e1f595ef619fc248`
- Status: implemented, independently reviewed, and committed as `a23d306baa4acc431c5ea3f3bddcd3e10e42e344`

## Behavior

`prepare_offline_e0_request` now accepts an optional bounded `route_prompt`.
When supplied, it runs the existing deterministic rule route on the enrolled
project snapshot, verifies the route-to-preparation accounting receipt, and
builds the OpenCode preparation join from that preparation. Only route-selected
exact-read paths proceed through the existing materialization, fixture message
lowering, and request lease. The artifact request pin is shared from route
preparation through terminal stream cleanup.

The content-free composition receipt now links the route/preparation receipt
digest to snapshot, selected candidates, exact-source join, preparation,
insertion, and request-body digests. `finalize_offline_e0_request` accepts only
the matching completed fixture stream after pin cleanup and returns a new
receipt whose digest includes its terminal outcome (`complete`, `cancelled`,
`failed`, or `timeout`). Receipt fields contain no prompt or source text.
Serializer and tokenizer identities remain synthetic, and exact-token status
remains unavailable. The existing selected path list still bounds which
enrolled files enter the snapshot; this change does not introduce recursive
repository discovery or client dispatch authority.

Route abstention/stale-source outcomes and non-ready or over-budget preparation
return without a request ticket and release the request pin scope. The legacy
direct preparation path remains available when `route_prompt` is omitted.

## Verification

Before the focused fixture run, storage status was `WITHIN_LIMIT`: 1,715,242,808
bytes actual with 20,103,000 bytes reserved across active jobs. C: had
173,009,674,240 bytes free. RAM was 18,641,452 KiB free of 33,486,624 KiB;
RTX 5060 Ti VRAM was 15,588 MiB free of 16,311 MiB.

The first invocation found that the new fixture's route prompt capped matches
too tightly. The prompt was corrected to a cap of ten, and the entire focused
module then passed by direct invocation under the existing `.venv` Python 3.11
environment:

```powershell
@'
import sys
sys.path.insert(0, 'tests')
import test_e0_offline_request_composition as tests
names = [name for name in dir(tests) if name.startswith('test_')]
for name in sorted(names):
    getattr(tests, name)()
    print(f'PASS {name}')
print(f'{len(names)} focused tests passed')
'@ | & .\.venv\Scripts\python.exe -
```

Result: **11 focused functions passed**, including route success, route
abstention, stale-source rejection, over-budget rejection, fixture EOF,
cancellation, failure, and existing timeout/cleanup cases. `git diff --check`
passed with Git's existing LF-to-CRLF advisories for the two edited Python
files. Initial independent read-only review PASS: job
`W2-NS-E0-ROUTE-TO-LEASE-REVIEW-20260924`, nonce `R2L-REV-A9C1`. It verified
source hash `9f2a32bb…eeef14` and then-current test hash
`6aac123e…217883`, reviewed route and preparation joins through request-body
digest, and verified finalizer matching and its synthetic terminal boundary.
No blocking finding. After that review, one assertion was added to the route
success test to check the context digest occurs exactly once in the lowered
body; the full focused module passed again. Follow-up read-only review PASS:
job `W2-NS-E0-ROUTE-TO-LEASE-REVIEW2-20260924`, nonce `R2L-REV2-B91E`, verified
the updated test hash `1e40b1a9…161e83` and the unique context-message match.
The reviewer confirmed that evidence remains fixture-only.

After the report, goal updates, second focused run, and independent review were
accounted for, the job reservation was released. Final storage status was
`WITHIN_LIMIT`: about 1.715 GB actual, 103,000 bytes reserved by other jobs,
and about 48.285 GB below the aggregate ceiling. `uv.lock` remains untouched.

SHA-256 before the review:

| File | SHA-256 |
| --- | --- |
| `src/wrench_harness/e0_offline_request_composition.py` | `9f2a32bbba3169b1768464bb46ab82f34e7e0cad7740e5e7e21e446842eeef14` |
| `tests/test_e0_offline_request_composition.py` | `1e40b1a997ce0e30c8829dd4a46dc8bf2fdbd5d5a6dcf9049dce06a63f161e83` |

## Limits and next gate

This composes local synthetic mechanics only. Receipts are caller-held values,
not authenticated client events. It does not establish OpenCode hook
registration or dispatch veto, active gateway route/model identity, final
provider request equivalence, tokenizer parity, actual tool/provider activity,
complete task accounting, real-task utility, or E0/E4 acceptance. The test
route operates only over the finite enrolled snapshot selection. The local
client and prior read-only model-list check are documented separately.

The change was committed in `a23d306baa4acc431c5ea3f3bddcd3e10e42e344` after
an independent read-only review and an orchestrator rerun of all 11 focused
functions plus `git diff --check`. Keep production client execution and
exact-token claims closed until route, model, serializer, tokenizer, and
supported dispatch-denial behavior are pinned and authorized. The broader E0
deterministic baseline still needs inventory-bound source selection and
complete end-to-end accounting.

## Follow-up: complete synthetic hook-envelope accounting

- Date: 2026-09-24 (America/Edmonton)
- Job: `W2-NS-E0-FULL-PROJECTION-20260924`
- Nonce: `E0FP-7D42`
- Base HEAD: `3ca8a5e6b5caa1ddc5b29302b5ec371cf6bdb4a3`
- Status: implemented, independently reviewed, and committed with this report

The prompt compiler now counts a bounded synthetic envelope containing every
validated OpenCode context-hook field: `sessionID`, `system`, `messages`,
`agent`, `model`, `tools`, and `options`. It inserts the compiler-prepared
messages into that envelope while preserving the other six fields. The
composition continues from the projector's private bounded JSON snapshot for
materialization, lowering, and receipt creation, so it does not reread the
caller-owned event after accounting. A content-free receipt binds the
post-insertion projection digest; the serializer identity is
`wrench-synthetic-opencode-semantic-envelope-json-v1`, and the tokenizer
identity remains the synthetic character counter.

The fixture lowerer remains a strict text-message subset. A valid hook
projection containing a tool-role message is rejected during fixture lowering
before a request ticket or retained pins can escape. This change does not model
OpenCode's final provider serializer or downstream transforms.

## Verification

The focused module was run through the existing Python 3.11 environment by
directly invoking all test functions: **14 passed**. The `pytest` package is not
installed in either available interpreter, so it was not installed. The
integration regression recomputes SHA-256 and byte count for the exact
canonical synthetic envelope and matches both to the prompt-gate receipt; it
also binds the post-insertion projection hash, verifies one context insertion,
and compares supported fixture-lowered messages to the materialized event.
The unsupported tool-role case verifies lowering rejection and lease/pin
cleanup. `git diff --check` passed with existing LF-to-CRLF advisories.

An independent read-only review returned PASS for job
`W2-NS-E0-SEMANTIC-ENVELOPE-REVIEW-20260924`, nonce `ESER-19A2`. Review found
no blockers after the input-snapshot binding and envelope-measurement
assertions were added. Source SHA-256:
`25e2f76a8f2dd596b4c8ed0527482ca9551368361e2a657a3d84651ceac0a83a`; test
SHA-256:
`869335931c4dbf1cfb97f18ab8b31cf46881b6862769d140b03a8805fd78c220`.

This remains synthetic offline evidence. It does not prove OpenCode hook
registration, actual client dispatch denial, final request equivalence,
provider routing, tokenizer parity, or complete lifecycle accounting. The
exact-token gate remains unavailable. The caller-supplied finite source
selection and broader E0 baseline are still incomplete.
