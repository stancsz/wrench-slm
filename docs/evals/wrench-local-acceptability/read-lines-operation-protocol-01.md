# Deterministic line-range operation screen 01

Status: preregistered offline mechanics measurement; no model call.
Job id: `LOCAL-READLINES-ACCEPT-20260925-01`

## Question and claim boundary

Can the current no-model route read an explicitly named, bounded line range
from its supplied source snapshot, can the independent core executor return
the exact same lines, and does E0 abstain on absent, stale, ambiguous, and
out-of-range evidence?

This is a six-case Wrench-authored fixture mechanics screen. It does not
measure natural-language coding-task completion, held-out generalization,
local SLM capability, real-work utility, production readiness, or frontier
token savings. The fixture is open development data and cannot be used for
training or tuning.

## Frozen fixture and scoring

- The runner embeds six explicit read-lines prompts and tiny synthetic file
  contents. Two successful cases use the same exact prompt against two files
  that differ only in the requested line range's source lines. The other four
  cases exercise a missing path, a source changed after snapshot creation, an
  end line beyond EOF, and a prompt without an exact path.
- Derive every proposal solely from its literal prompt using
  `mechanical_route`. Never seed a proposal from the expected observation.
- Run each prompt through `run_e0_rule_route` using a fresh exact-source
  snapshot. Require the frozen route status, action, reason and complete
  expected line observation. Only the two completed `read_lines` proposals
  reach `execute_model_output`; pass the proposal derived from that prompt to
  the independent executor against the isolated case root. Compare normalized
  relative path, start, end and all returned lines to the independently frozen
  oracle.
- Hash the complete case-root file inventory immediately before and after
  route/executor work. Any unexpected file, content or inventory change fails
  the run. The intentional stale-source mutation occurs before the pre-run
  inventory and after snapshot creation.
- Report each case and aggregate routes, exact executor observations,
  abstentions, false abstentions, unresolved results, unsafe dispatches,
  mutations and runtime errors. There is no retry.

## Scope and safety

Only `read_lines` can reach the core executor. The run uses no model inference,
training, client, provider, network, shell action from Wrench, or source
mutation. All temporary roots and the content-free JSON receipt stay under
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability`.

Immediately before the run, check the aggregate storage budget and reserve
5,000,000 peak additional bytes for this unique job. Confirm C: free space and
at least 10% free system RAM and VRAM. Check storage again after the run and
release this reservation only after the output is accounted for.

## Frozen command

```powershell
python tools/measure_read_lines_acceptability.py --output C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\read-lines-acceptability-20260925-01.json
```
