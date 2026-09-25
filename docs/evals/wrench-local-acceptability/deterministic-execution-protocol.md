# Deterministic local operation execution screen

Status: preregistered open-development mechanics measurement; no model call.
Date: 2026-09-25 (America/Edmonton)

## Question and claim boundary

Can the current no-model route produce an exact bounded read or literal-search
proposal, can Wrench's independent core executor return the expected exact
observation, and does the snapshot-bound E0 path abstain on missing, stale, or
ambiguous evidence?

This measures bounded local **operations**, not completion of natural-language
coding tasks. The route does not answer the semantic questions represented by
the fixture's separate answer oracles. A pass is open-development fixture
mechanics only; it is not held-out generalization, task utility, SLM
acceptability, production readiness, or frontier-token savings.

## Frozen inputs and action boundary

- Use only the already admitted, Wrench-authored
  `tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json` with its pinned
  canonical SHA-256 and review receipt. Revalidate admission at startup.
- Run all ten manifest cases as authored, including the post-snapshot stale
  mutation. Never read a `final` split or source expected targets from another
  evaluation set.
- Derive the proposal only by calling `mechanical_route` on the manifest's
  actual operation prompt. Never seed action arguments from expected
  mechanics, hidden answer rules, or expected tool flows.
- Allow only `read_file` and `literal_search` through
  `execute_model_output`; expected abstentions do not reach the core executor.
  This excludes Git, health/HTTP, patch proposals, writes, shell, model, client,
  and provider operations. The literal-search handler may use the existing
  bounded `rg` accelerator against the isolated fixture root.
- Materialize only the manifest's synthetic files under a unique temporary
  directory below `C:\wrench-slm-data\artifacts\wrench-local-acceptability`.
  No repository, user project, network, or external endpoint is read.
- Run `run_e0_rule_route` against a hash-bound snapshot. For expected completed
  cases, also execute the independently parsed proposal against the same
  synthetic root with `execute_model_output`. For missing, stale and ambiguous
  cases, require the exact frozen E0 abstention and make no executor call.
- Normalize only absolute paths under the isolated root to fixture-relative
  paths. Compare full status, action, abstention reason, byte count, exact text,
  search matches, and truncation state to the frozen `expected_mechanics`.
  Check the filesystem contents before and after each executor call; unexpected
  mutations fail the safety gate.

## Scoring

Report all ten per-case outcomes, grouped by the manifest's five groups.
An operation family passes this diagnostic only if every case in the group
matches the exact route and executor/oracle expectations, every required
abstention has the exact status/reason/action, and there are zero unexpected
mutations, unsafe dispatches, or runtime errors. Keep accepted operations,
correct abstentions, false abstentions, unresolved cases, and execution errors
separate. Record route and executor latency separately. Exclude answer-oracle
fields from scoring because the task is operation execution, not semantic
answer generation.

## Identity, artifacts, and stop conditions

The receipt records the repository commit, fixture manifest and review hashes,
source hashes for the route/parser/snapshot/core/admission modules, per-case
status/action/reason and content hashes, counts, elapsed time, and zero/unknown
frontier savings. It must not store prompts, source text, search-result text,
answers, or token sequences. The only durable output is one JSON receipt under
the approved artifact root; temporary fixture roots are removed on exit.

Before the run, run storage `status` and reserve a unique peak estimate, check
volume free space, and confirm at least 10% RAM and VRAM free. Stop on fixture
admission/hash mismatch, unexpected proposal action, oracle mismatch, mutation,
runtime exception, storage overage, or resource-reserve breach. Do not retry,
train, tune, or modify the router based on this exposed fixture. Frontier-token
savings remain N/A because neither arm calls a frontier model.

## Frozen command

```powershell
python tools/measure_local_task_acceptability.py --output C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-exec-acceptability-20260925-01.json
```
