# Selective offload revision 1

Updated: 2026-09-10

The first frozen `eligible` policy passed development but failed its fresh
held-out gate. It accepted 347/600 requests, completed 333 correctly, and
accepted 14 wrong local actions. Nine of those accepted actions were on
unsupported requests. The complete receipt is
`artifacts/selective-offload/evaluation-eligible/summary.json`.

## Observed failure

The original policy verified that a command was structurally safe and used a
visible resource, but did not verify that the command matched the public
request. Examples included `git status --short` for a Git-log request and a
visible configuration read for unsupported work. This is a policy defect, not
a model-quality pass.

## Bounded revision

`wrench/selective_policy.py` now exposes revision `intent-v2`. It preserves the
original visible-resource and command allowlists and adds public request-intent
checks:

- line reads require public line or range language;
- configuration reads require public configuration or region language;
- Git status requires public status or dirty-worktree language;
- Git log requires public commit, HEAD, history, subject, or title language;
- literal search requires public search, marker, file, or path language;
- health requests require public health or service-status language;
- drafts require public write, proposal, review, or draft language.

The revision never reads private task kind, fixture contents, or expected
answers. It is one bounded selector revision. No model weights or held-out V1
rows are changed.

## New data and measurement

The revision must use a new campaign and new family IDs:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\build_selective_offload_v1.py `
  --campaign selective-offload-revision1 `
  --output data\pilots\selective-offload-revision1
```

Run development with `--revision intent-v2`, freeze only after the same
nonempty, zero-wrong-accepted, zero-ineligible-acceptance, zero-mutation gate,
then run all 600 new evaluation tasks. Report accepted coverage, correct local
completions over all requests, accepted precision, wrong accepted actions,
unnecessary fallbacks, kind/language slices, and family-clustered uncertainty.

If the revision fails the fresh gate, stop selector expansion and report
`NO MEASURED BENEFIT` for the bounded local policy study. Do not tune against
the revision evaluation rows or start training.
