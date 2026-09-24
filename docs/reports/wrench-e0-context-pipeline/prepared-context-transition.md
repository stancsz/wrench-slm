# Preparation-bound OpenCode context transition

Job: `W2-NS-E0-PREP-CONTEXT-TRANSITION-20260925`

## Change

The prompt-gate receipt records the canonical SHA-256 digest and insertion
position of the exact context message created from selected E0 evidence. The
preparation aggregate now uses `wrench.e0-preparation-refs.v2` and includes
those values. Empty, failed, or non-ready gates carry null insertion identity.

`validate_opencode_preparation_context_transition` requires a READY
preparation and prompt gate, verifies the expected message digest and position,
and checks that two bounded OpenCode projections differ by exactly that
message insertion. It returns a content-free wrapper receipt linked to the
preparation aggregate. The partial lifecycle trace verifies that receipt and
its session and after-projection identities. Route-preparation evidence now
requires a matching transition. The trace schema is
`wrench.e0.partial-lifecycle-trace.v4`.

## Verification

Windows Python 3.11.16 and the existing cached pytest runtime ran:

```powershell
$env:PYTHONPATH = 'C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_prompt_compiler.py tests/test_e0_context_pipeline.py tests/test_opencode_hook_projection.py tests/test_e0_lifecycle_accounting.py --basetemp C:\wrench-slm-data\tmp\e0-prep-transition-tests-20260925\pytest
```

Result: **97 passed in 7.60 seconds** after the verifier-bound fix. No package installation occurred. The
first combined run found a serializer-bound alias issue and three lifecycle
fixtures that did not provide the transition now required alongside
route-preparation evidence. Both issues were corrected and the focused suite
passed on rerun.

Test scratch remains under the approved data root. The first independent
read-only review found a P2 verifier-bound issue. The fix and regression were
sent for targeted independent re-review, which passed. See the evaluation for
source/test hashes and final storage status.

The targeted read-only re-review passed. It confirmed the verifier now shares
the transition's valid position range (`0` through `127`) and that the
regression recomputes a valid receipt hash around position `128`. It also
confirmed the report/evaluation record the parent-run test result and matching
source/test hashes. The review did not run tests.

## Limits

This is structural validation over caller-provided preparation, message, and
projection objects. It does not authenticate hook execution, prove OpenCode
used the transition, validate all nested OpenCode message or option schemas,
prevent dispatch, reconstruct the final provider request, or establish
provider/tokenizer parity. No OpenCode install or run, provider call, real-task
capture, or E0 acceptance occurred. E0 accounting, independent outcome truth,
and customer utility remain open.
