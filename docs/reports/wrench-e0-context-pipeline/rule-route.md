# Snapshot-bound deterministic rule route

Job: `W2-NS-E0-ROUTE-IMPL-20260924`  
Nonce: `RTE-9A33`  
Baseline inspected: `1aca758ac298985c4e8f0fad055566c874a2418a`

## Contract

`src/wrench_harness/e0_rule_route.py` adds `run_e0_rule_route(prompt,
root_binding, snapshot)` as a provider-free W4 component. It uses
`mechanical_route` only as a proposal parser. It never passes that proposal to
`execute_model_output`, `execute_proposal`, a worker/client, subprocess, model,
provider, socket, or HTTP call. For each accepted source it calls
`retrieve_exact(root_binding, snapshot, path)` and returns the resulting UTF-8
text or literal matches with content-free path/hash/size evidence.

Only `read_file`, `read_lines`, and literal `literal_search` proposals are
supported. Requested file paths must be snapshot members. A search root may
select snapshot member paths beneath that relative root; the result states
`scope=supplied_snapshot_sources`, so a match or no-match result makes no claim
about unsnapshotted files. The source manifest is passed through the existing
complete `_validate_snapshot` check before route parsing or route-specific
iteration, and is traversed only after its 256-file/4 MiB snapshot caps pass.

The route imposes these local limits:

- Prompt: 16,000 characters.
- Read: 256 KiB per file.
- Search: 16 files and 512 KiB total source bytes.
- Line range: at most 500 lines.
- Search literal and returned line: at most 4,096 characters each.
- Search results: at most 200 matches; reaching the cap reports a partial
  result and unknown evidence.

Before retrieval, a conservative intent gate rejects explicit negation,
contradictory requests, output-only restrictions, and consent/authorization
markers whenever a read/search action appears. ASCII and curly apostrophes are
normalized for this decision. This reduces known accidental-disclosure cases;
it is not a general natural-language policy oracle. Unsupported actions,
ambiguous requests, bad manifests, stale/changed/missing sources, non-text
bytes, and exceeded limits abstain with reason and unknown-evidence records.

The result is an in-memory deterministic route result with `route=none`,
exact-read attempt/success/byte counters, hashes for successfully read sources,
and no user outcome claim. It does not join to `PreparationResult`, finalize
the E0 outcome receipt, establish complete request accounting, authenticate
the caller, prove task intent, or enforce a client dispatch veto. This work is
component evidence only, not E0 acceptance or OpenCode integration.

## Verification

Focused verification on Windows, Python 3.11.16, pytest 8.3.5:

```powershell
$env:UV_CACHE_DIR='C:\wrench-slm-data\cache\w2-root-route-uv'
$env:TEMP='C:\wrench-slm-data\cache\w2-root-route-temp'
$env:TMP=$env:TEMP
$env:PYTHONDONTWRITEBYTECODE='1'
uv run --no-project --python 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' `
  --with pytest==8.3.5 pytest -p no:cacheprovider tests/test_e0_rule_route.py
```

Result: `31 passed`. The fixtures cover exact file/line reads, snapshot-scoped
literal search, match-limit partials, negated/contradictory/output-restricted
and consent/authorization-marked intent including curly apostrophes and quoted
output-only restrictions, unknown paths, non-text and stale sources, changed
root identity, malformed/over-cap
manifests, file/byte/line caps, supported `no more than` bounds, `not found`
search wording, authorization-related/output-like search literals, unsupported
Git-status actions, and tripwires
for the live executor and subprocess. `git diff --check` passed. No client or
provider was installed or run. Cache and temporary paths were under
`C:\wrench-slm-data\cache`; the scoped storage reservation was
`10,000,000` bytes.

Independent source/test review initially found and drove repairs for negated
read intent and unbounded caller-constructed manifests. The final review
result is recorded in the [evaluation](../../evals/wrench-e0-context-pipeline/rule-route.md).
