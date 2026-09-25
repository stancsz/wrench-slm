# Deterministic line-range operation screen 03

Date: 2026-09-25 (America/Edmonton)

## Result

The corrected six-case screen passed every frozen route and safety check. E0
returned the exact route outcome on 6/6 cases. Two explicit line-range reads
reached the independent core executor and both returned the exact expected
path, bounds and lines. E0 correctly abstained on the missing path, stale
snapshot, line range past EOF and ambiguous path. There were zero false
abstentions, unresolved outcomes, unsafe dispatches, unexpected mutations or
runtime errors.

| Case | Outcome | Executor | Result |
| --- | --- | --- | --- |
| `line-a` | exact `read_lines` | exact lines | Pass |
| `line-b` | exact `read_lines` | exact lines | Pass |
| `line-missing` | abstain: source absent from snapshot | not called | Pass |
| `line-stale` | abstain: snapshot source changed | not called | Pass |
| `line-out-of-range` | abstain: end line past EOF | not called | Pass |
| `line-ambiguous` | abstain: no exact file path | not called | Pass |

This expands the exposed synthetic operation-mechanics envelope to bounded
exact-file reads, bounded line-range reads and literal searches, with
fail-closed abstention for the measured evidence failures. It does not show
that a local model can complete coding tasks or that these operations improve
successful task outcomes on a real repository.

## Timing and resources

Mean route time was 4.16 ms (median 4.84 ms) across six cases. Mean executor
time was 2.73 ms across the two completed cases. These are tiny local fixture
measurements, not end-to-end client or coding-task latency.

Before the run, 50.94% of system RAM and 15,523 of 16,311 MiB of VRAM were
free; C: had 174,213,828,608 bytes available. The operation screen used no GPU.
These are point-in-time samples, not continuous monitoring.

## Identity and limits

- Preregistration: [protocol 03](../../evals/wrench-local-acceptability/read-lines-operation-protocol-03.md).
- Repository revision: `10bb51539ed860cd55bdf311aa67e223b9c10a41`.
- Runner SHA-256: `260f577b523bfd8c6e5d00830e73ed6f16aa15cc401c959e7ad986ccc947589e`.
- Embedded fixture SHA-256: `b2a8e09aa86185b23981b4ef2e9eb2bcc5879af898801d74bc7dfcca1e2dc7fb`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\read-lines-acceptability-20260925-03.json` (4,570 bytes).
- Receipt SHA-256: `051eec3d5643d8b1fc98d1305cfa3f29525d51476b2297b115b5bd8cc718d94d`.
- Training, SLM inference, OpenCode invocation, localhost:4000 requests, provider calls and source mutation: none.
- Frontier calls: zero; eligible matched usage pairs: zero; frontier savings percentage and average per-task savings: N/A.

The fixture is open development data authored by Wrench. This is a mechanics
result only. The first two line-range attempts stopped before cases ran and
are preserved in the linked protocol and evaluations; neither contributes to
this result.
