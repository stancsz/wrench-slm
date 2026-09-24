# Preparation-bound OpenCode context transition evaluation

## Decision

The focused fixture result supports this bounded offline structural slice.
It does not satisfy E0 acceptance or authorize runtime execution.

## Verification

Four focused suites passed **97 tests in 7.60 seconds** on Windows Python
3.11.16 using the existing cached pytest runtime. The first combined run found
one serializer-bound compatibility issue and three lifecycle fixtures that
needed the new transition arguments. After correction, the combined rerun
passed. No packages were installed. The test reservation remains active until
final storage accounting; scratch is under the approved data root.

The prompt gate binds the exact generated message digest and insertion
position to preparation aggregate schema v2. The lifecycle trace schema v4
requires and verifies a preparation-bound transition when a route-preparation
receipt is present. Tests cover empty/non-ready insertion identity,
message/position mismatch, changed preparation, altered after-projection,
missing transition inputs, tampered wrapper receipt, and content-free trace
output.

The first independent read-only review found that the receipt verifier allowed
impossible insertion positions. The verifier now rejects positions at or
above the hook's 128-message limit. A regression constructs a correctly hashed
receipt with the impossible position and verifies rejection. Targeted
independent re-review passed.

The targeted read-only re-review passed after the impossible-position bound,
regression, 97-test result, and hashes were recorded. The reviewer verified
the documented hashes against the source and test files and did not run tests.

Source and test SHA-256:

- `opencode_hook_projection.py`: `C543758BBB17E4E941E45D612B7AAF3E622AD301336B7238559409F4FEFF2893`
- `test_opencode_hook_projection.py`: `18482AA78672D1D96CCDC7049AA5492A3E4E1459BDDE90E2ACC5E7B15E61F646`

Storage admission and final accounting both reported `WITHIN_LIMIT`. After
releasing this slice's 10 MB test and 2 MB documentation reservations, the
checker reported 666,294,881 actual bytes and 103,000 bytes in other active
reservations (666,397,881 projected), below the 50 GB decimal cap. Pytest
scratch remains counted under `C:\wrench-slm-data\tmp`.

## Limits

The inputs remain caller supplied and unauthenticated. This does not establish
runtime hook behavior, nested OpenCode schema validity, dispatch enforcement,
final request or tokenizer parity, complete lifecycle accounting, task truth,
customer utility, or overall E0 acceptance. OpenCode remains uninstalled and
unrun.
