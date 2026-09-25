# Patch-operations screen 01 evaluation

Status: **PASS_OPEN_DEVELOPMENT_MECHANICS_ONLY**. Screen date: 2026-09-25.

## Frozen criteria and results

All-case acceptance was required. The 12 positives each required the exact
frozen diff, exact target bytes after independent application, `patch_draft`,
deep TTC pass, and review-only/unapplied observation. Every boundary required
the exact route abstention and a parsed raw abstention object with no proposal
fields. Fixture trees had to remain unchanged; any runtime error failed.

| Case group | Cases | Exact positive/boundary result | Independent applications |
| --- | ---: | ---: | ---: |
| Replace | 3 | 3/3 | 3/3 |
| Append, final LF | 3 | 3/3 | 3/3 |
| Insert after unique anchor | 3 | 3/3 | 3/3 |
| Explicit whole-line removal | 3 | 3/3 | 3/3 |
| Duplicate/missing targets | 5 | 5/5 abstained | n/a |
| Unsupported source format | 2 | 2/2 abstained | n/a |
| Outside-root path | 1 | 1/1 abstained | n/a |
| Missing review-only intent | 1 | 1/1 abstained | n/a |

Total: 21/21 cases; 12/12 positives; 9/9 boundaries; 21/21 unchanged fixture
trees; 0 runtime errors; 0 retries. Boundary abstention counts by reason:
`patch_target_not_unique` 4, `patch_anchor_not_unique` 1,
`patch_source_format_unsupported` 2, `path_outside_allowed_root` 1,
`patch_draft_requires_review_only` 1.

## Receipt identity

- Job ID: `W2-LOCAL-PATCH-OPERATIONS-20260925-01`
- Nonce: `LPO01-SUPV-86C1`
- Protocol SHA-256: `5f7b0b8ad2ff73a5932abeb58b7dcab6e60ff658b2dbe13171ed61715e7d0551`
- Runner SHA-256: `53ae02a66288de8b47581186a7037e9a6048477795138f1736d2885245530e26`
- Receipt SHA-256: `18c7e2da64df8506be7aaddc4801ae04b39d859cf3fd685a01a50b90d53cfedb`
- Frontier-token savings: null.

The receipt is stored at
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\patch-operations-screen-01.json`.
It records case identities, content hashes, outcomes and resource-safe runtime
metadata without raw prompts, fixture text or diffs.

The runner was invoked exactly once for this preregistration. It prevents
overwriting the frozen receipt path, but it does not globally block reuse of
the job ID with another output path. Future measurement must use a new frozen
identity; no second run is part of this result.

## Decision scope

Accept these four operation mechanics only for the frozen, small UTF-8 LF
synthetic cases and prompt forms. This result does not accept open-ended or
multi-file patch work, semantic repair correctness, completed coding tasks,
SLM task capability, real-work utility, or frontier-token savings. No model,
tokenizer, client, provider, or network was used; training remains stopped.
