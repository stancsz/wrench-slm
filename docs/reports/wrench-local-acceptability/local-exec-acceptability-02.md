# Deterministic local operation screen 02

Date: 2026-09-25 (America/Edmonton)

## Result

The corrected route-to-executor screen passed all ten open-development
mechanics cases. The snapshot-bound E0 route returned the exact expected
outcome for 10/10 cases. The independent core executor returned the exact
expected observation for all seven completed read/search operations. E0 made
the correct missing, stale, or ambiguous abstention on the other three cases.
There were zero false abstentions, unresolved outcomes, unexpected mutations,
unsafe dispatches, or runtime errors.

| Frozen fixture pair | Cases | Exact completed operations | Correct abstentions | Unresolved | Screen |
| --- | ---: | ---: | ---: | ---: | --- |
| `loc-function-name` | 2 | 2 | 0 | 0 | Pass, bounded source read only |
| `triage-error-type` | 2 | 2 | 0 | 0 | Pass, bounded log read only |
| `context-literal-boundary` | 2 | 2 | 0 | 0 | Pass, literal search incl. exact empty result |
| `evidence-availability` | 2 | 0 | 2 | 0 | Pass, missing and stale both abstained |
| `evidence-specificity` | 2 | 1 | 1 | 0 | Pass, exact path read and ambiguous request abstention |
| **Total** | **10** | **7** | **3** | **0** | **10/10 fixture mechanics** |

The prompts are explicit operation requests such as “Read this named file”
and “Find this exact literal.” The host-side fixture oracle checks exact
observation bytes/lines/matches and abstention reasons. The measurement does
not test answering the fixture's separate semantic questions, general
localization, root-cause diagnosis, code edits, test fixes, or multi-step
coding work. The class names in the fixture must not be read as semantic task
acceptance. No local SLM was used; the Qwen 0.8B screen remains 0/10, with no
accepted SLM class.

The first attempt, [screen 01](local-exec-acceptability-01.md), remains
scorer-invalid and was not combined with this result. Its report/evaluation
document the omitted UTF-8 byte-count normalization and the correction.

## Timing and token accounting

Mean E0 route time was 7.06 ms per case (median 5.04 ms). Mean core executor
time across the seven completed operations was 21.76 ms (median 1.73 ms).
These are local fixture-path timings, not full-client or end-to-end coding
task latency.

Frontier-token savings are **N/A**, with zero frontier calls and zero eligible
matched usage pairs. No tokens were saved or spent in a downstream workflow;
this measurement cannot provide a savings percentage or a per-task savings
average.

## Identity and accounting

- Preregistration: [protocol 02](../../evals/wrench-local-acceptability/deterministic-execution-protocol-02.md).
- Repository revision: `dc663de7fc1e549a4a85de2c4ba3f63e0c27ee4b`.
- Fixture manifest SHA-256:
  `871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`.
- Fixture review receipt SHA-256:
  `b5c32928841b66aa679eccdbd7d88a4bffad4075b07f794f2a42d380961c1b2f`.
- Receipt:
  `C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-exec-acceptability-20260925-02.json`.
- Receipt SHA-256:
  `6b3ea4dfd9653e12f8e2bb3a01c5a098825738634e07ae95f85bae8b37af2db5`
  (11,300 bytes). The receipt records the parser, snapshot, route, executor,
  admission, and measurement-runner hashes plus per-case evidence digests.
- Training, model inference, client execution, provider calls, and source
  mutation: none.

At the post-run storage check, Wrench artifacts totaled 10,095,531,867 bytes;
including active reservations, projected use was 10,141,634,867 bytes, below
the 50 GB limit. C: had 174.2 GB free. Pre/post samples showed 51.73%/52.88%
free RAM and 15,505/15,525 MiB free of 16,311 MiB VRAM. This short deterministic
run did not use the GPU; samples were point-in-time checks, not continuous
monitoring.

## Decision

The evidence supports one narrow local operating envelope: deterministic,
bounded exact file reads and literal searches on an explicit supplied
snapshot, with correct abstention on missing, stale, or ambiguous evidence.
This is a synthetic mechanics pass for the operation path only. It does not
establish acceptable local coding-agent task completion or generalization.
Keep training stopped until a specific decision has evidence and a separately
admitted holdout. Real-work acceptability requires consented, repository-
authorized tasks and independent outcome oracles. Frontier savings still
require complete matched downstream usage receipts.

Independent static review of the saved receipt and report passed. The reviewer
recomputed the receipt hash, case counts, five pair summaries, identity joins,
and abstention/executor boundaries; no material findings remained. The review
did not rerun the measurement and is recorded at
[evaluation review 02](../../evals/wrench-local-acceptability/local-exec-acceptability-02.md).
