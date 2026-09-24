# E0 request and version scope

## Result

Added an offline request-scope coordinator joining an `ArtifactRequest`, a genuine `ModelLifecycle.pin`, a READY context preparation, its accounting and incomplete preparation receipt, and an explicit terminal outcome receipt. A bounded canonical envelope is produced only when all joins validate. The coordinator checks that the exposed artifact request remains active after preparation and before finalization, so an early close fails closed. Artifact pins release on normal completion, incomplete receipt, and exceptions. The model pin remains a hash-bound snapshot reference; it is not a storage retention lock, and no model is loaded.

The component is local structural plumbing. Callers set the terminal outcome receipt's `run_id` to the scope's `request_id`; the equality check is a correlation join only and is not authentication. Its reference envelope is caller-supplied, untrusted evidence. It does not establish prompt/client compatibility, inference, task outcome truth, production recovery, or accounting beyond the existing receipt validators.

## Evidence

- Repository: `C:\Users\stanc\github\wrench-slm`; shared HEAD at verification: `9f8a580812db47b4490c4a085fe9ac19c9d50cd3`.
- Implementation: `src/wrench_harness/e0_request_scope.py`, SHA-256 `30192190D67975E31CF27FCF7FE8BE9EA297D6C8F34D4C3361C37D8526272425`.
- Focused tests: `tests/test_e0_request_scope.py`, SHA-256 `4FFF28BB143217BC8F7B04C33D5DC1172CA7F3C3C1B9F702C6EDC794A28FB8D1`.
- Exact command: `python.exe -m pytest -p no:cacheprovider --basetemp=C:\wrench-slm-data\tmp\W2-NS-E0-E3-REQUEST-SCOPE-20260924\pytest-ERSC-A418-final4 tests/test_e0_request_scope.py -q`, using Python 3.11.16 and the pre-existing pytest cache through `PYTHONPATH`.
- Final result after root review repairs: `8 passed in 5.26s`, including early artifact-request close rejection, explicit snapshot identity, and request/run ID correlation.
- `git diff --check`: exit 0. The new implementation, tests, report, and evaluation were separately scanned for trailing spaces/tabs; none were found. Root should include them in the staged diff check.
- First pytest invocation stopped before test execution because the reserved scratch parent had not yet been created. After creating the directory under the approved job root, the focused run above completed successfully.
- Before the final focused run, storage checker reported `WITHIN_LIMIT`, included `C:\Users\stanc\AppData\Local\npm-cache`, and measured 2,286,886,705 bytes with 20,103,000 bytes reserved. C: had 182,648,885,248 bytes free. RAM available was 14,298,374,144 / 34,290,302,976 bytes; RTX 5060 Ti had 15,207 / 16,311 MiB free.

## Coverage and limits

The synthetic suite checks a scope pin across candidate activation, a subsequent scope observing the newly active version, complete failed outcome binding, incomplete outcome rejection, exception and absent-terminal cleanup, missing preparation-receipt rejection, mismatched request/run and snapshot rejection, and early closure of artifact pins. Fixtures use only small synthetic bytes and opaque identifiers.

`ArtifactRequest` pins and model-version pins are process-local. The artifact request pins artifact-store objects while active. `ModelLifecycle.pin` snapshots an immutable manifest identity, but does not lock the version files against external deletion or coordinate atomically with artifact-store changes. Acquiring the two references is sequential; this coordinator provides no transaction across the stores. It does not open network/client/runtime connections, invoke inference, or persist the envelope. The terminal outcome is only structurally validated; it may be false or caller supplied. The request's measured artifact pin duration is local scope lifetime, not end-to-end request latency. No real task corpus or utility oracle was used.

## Next action

Root independently reviewed the final implementation and test hashes. Next, include these four allowed files in the root-owned staged diff check and commit. Any downstream runtime/client integration requires a separately approved compatibility contract and real-data/outcome authority.
