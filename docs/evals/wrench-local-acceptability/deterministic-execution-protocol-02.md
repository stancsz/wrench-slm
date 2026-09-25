# Deterministic local operation execution screen 02

Status: preregistered corrected open-development mechanics measurement; no model call.
Date: 2026-09-25 (America/Edmonton)
Job id: `LOCAL-EXEC-ACCEPT-20260925-02`
Nonce: `LEA02-6F3C`

## Purpose and prior-run correction

Protocol 01 stopped as scorer-invalid because its oracle comparison omitted the
UTF-8 `bytes` field returned for `read_file`. The existing fixture mechanics
test derives that field from the source bytes before equality comparison. This
protocol freezes the same derivation in the measurement runner. It also scores
the five manifest pairs (`pair_id`) separately; the previous receipt grouped
the two evidence pairs together. No router or executor behavior is changed.

## Question and claim boundary

Can the current no-model route produce an exact bounded read or literal-search
proposal, can the independent core executor return the exact expected
observation, and does snapshot-bound E0 abstain on missing, stale, or ambiguous
evidence?

This measures bounded local operations on the exposed synthetic development
fixture. It does not measure natural-language coding-task completion, held-out
generalization, SLM capability, utility, production readiness, or frontier
token savings.

## Frozen measurement

- Input: the already admitted `wrench.synthetic-matched-tasks.v2` fixture,
  exactly ten manifest cases, pinned canonical manifest SHA-256
  `871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`, and
  its hash-bound review receipt. Revalidate admission before execution.
- Derive every proposal from the literal operation prompt in each case via
  `mechanical_route`. Never seed arguments from expected mechanics, answer
  rules, test outputs, or prior receipt results.
- Run `run_e0_rule_route` against an exact-source snapshot for all cases.
  Require exact status/action/reason and the complete expected observation.
  For read-file cases, derive expected `bytes` as the UTF-8 encoded length of
  the hash-verified fixture source, matching the existing mechanics test.
- For the seven cases expected to complete, permit only `read_file` and
  `literal_search`, then pass the independently parsed proposal through
  `execute_model_output` against that case's isolated temporary root. Compare
  status/action and every returned observation field to the fixture expectation
  (including UTF-8 byte count; omit only E0's snapshot-scope metadata, which
  the core executor does not return).
- For the three missing/stale/ambiguous cases, require the exact E0 abstention
  and do not call the core executor. Check the complete temporary file
  inventory and hashes before and after each operation. Any changed or added
  file fails the run.
- Score each pair separately: `loc-function-name`, `triage-error-type`,
  `context-literal-boundary`, `evidence-availability`, and
  `evidence-specificity`. Each pair passes only if every case has an exact
  route outcome and every completed case also has an exact executor outcome,
  with zero unexpected mutations, unsafe dispatches, or runtime errors.
- Report route and executor time, exact operations, correct abstentions,
  false abstentions, unresolved cases, and all safety failures per pair.
  Preserve the protocol-01 receipt and classify it as scorer-invalid; do not
  combine its counts with protocol 02.

## Boundaries, resources, and artifacts

Only `read_file` and `literal_search` may reach the core executor. Git, health,
HTTP/network, patches, writes, shell, model, client, and provider calls remain
out of scope. Literal search uses the existing bounded `rg` accelerator only
inside a synthetic temporary root. Temporary files and the content-free JSON
receipt remain under `C:\wrench-slm-data\artifacts\wrench-local-acceptability`.
The receipt includes the current source hashes, repo commit, fixture identities,
counts, per-case statuses/reasons and evidence digests; it stores no prompts,
source text, observations, answers, or token sequences.

Immediately before the run: recheck storage status, hold a new 5,000,000-byte
reservation for this job, check C: free space and confirm at least 10% RAM and
VRAM free. Stop on any fixture identity/admission mismatch, proposal outside
the allowlist, mismatch after byte-count normalization, tree mutation, runtime
exception, storage overage, or reserve breach. No further attempt is allowed
on this fixture for this measurement. Do not train or tune on it.

Frontier-token savings remain N/A; this diagnostic issues zero frontier calls.

## Frozen command

```powershell
python tools/measure_local_task_acceptability.py --output C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-exec-acceptability-20260925-02.json
```
