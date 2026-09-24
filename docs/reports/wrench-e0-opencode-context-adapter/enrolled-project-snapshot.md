# Enrolled OpenCode project snapshot input seam

Job: `W2-NS-E0-ENROLLED-SNAPSHOT-20260924`  
Nonce: `ESNP-40C9`  
Base HEAD: `169a6258582ec8685780b7858872347c3d6c360a`

## Result

The explicit Wrench project registry is connected to the existing snapshot
primitive through `prepare_opencode_project_snapshot`. It resolves the event
and session record using the enrolled registry, validates the complete
selection before reading source, and accepts only a finite, explicit subset of
enrolled relative paths. It rejects invalid containers, overlong iterables,
duplicate paths, excluded or unenrolled paths, and invalid path forms. It
passes the enrolled binding and the stricter of the global and enrollment
source-byte caps into snapshot creation. The result is in memory; this slice
does not use an artifact store or persist project content.

The returned preparation state marks the snapshot `SNAPSHOT_INPUT_READY` and
the exact-token gate `UNAVAILABLE`. This is an input seam for later work, not
context assembly, a client plugin, a dispatch gate, or full E0 acceptance.

## Verification

Focused synthetic test command:

```text
python -B -m unittest discover -s tests -p test_opencode_project_snapshot.py -v
```

Interpreter: CPython 3.11.16. Result: **9 tests passed in 1.229 seconds**,
exit code 0. `PYTHONPATH=src` was set, bytecode writing was disabled, and
`TEMP`/`TMP` pointed below
`C:\wrench-slm-data\tmp\W2-NS-E0-ENROLLED-SNAPSHOT-20260924`.

Cases cover result binding and non-persistence, event/record session mismatch,
root replacement, invalid and overlong selections before snapshot reads,
duplicate and unenrolled paths, tighter per-file and aggregate caps, registry
cap ceilings, and propagation of source-changed and reparse-point read errors.
The last two cases mock the lower-level read errors to test propagation; they
do not exercise the failures through native reads. Existing snapshot tests
provide separate POSIX symlink rejection and changed-data retrieval coverage.

Independent read-only static review by `e0_goal_evidence` returned **PASS** on
the following final hashes. The reviewer did not run tests:

| File | SHA-256 |
| --- | --- |
| `src/wrench_harness/snapshot.py` | `F54F835A40ED894550F7EC0C709E6C9E33494D8EAEC9E41DCD9715FB627CD78D` |
| `src/wrench_harness/opencode_project_snapshot.py` | `C7D0447054199820525A9ECE4CB83A14F7E5F7135AB3B0B96F491C94AFD640E7` |
| `tests/test_opencode_project_snapshot.py` | `BDFFDCB0565655A0FFADF8B352BBB1D5C899BFEB2D869818CCDBD94B8900CF89` |

`git diff --check` passed with an LF-to-CRLF advisory for `snapshot.py`.
Storage was `WITHIN_LIMIT` before and after the run. Post-run accounting was
1,714,866,044 bytes actual and 20,103,000 bytes reserved, including this
workstream's 20,000,000-byte reservation. C: had 173,041,635,328 bytes free
at preflight. RAM free was 54.5–54.6% during the run and 54.6% after; VRAM
free was 15,588–15,591 MiB during the run and 15,595/16,311 MiB after.

The orchestrator attempted the broader existing `tests/test_snapshot.py`
compatibility suite, but it did not start because `pytest` is not installed in
the available interpreter (`ModuleNotFoundError`). No tests from that suite
ran, and no dependency installation was attempted.

## Limits

All fixtures used synthetic temporary roots under the assigned temp path. No
real project source was opened or admitted. This job did not install, launch,
load, or invoke an OpenCode client or plugin; the isolated OpenCode CLI had
already been installed by a separate job. No request was made to
`localhost:4000` or a provider. Filesystem revalidation remains path-based and
does not prove transaction safety against concurrent adversarial replacement.
The snapshot is not a full context or dispatch integration, and no production
runtime, final request identity, tokenizer parity, request-lifetime handling,
or user utility has been established. E0 and E4 remain incomplete; exact-token
acceptance remains closed.
