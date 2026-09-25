# Local patch-operations screen 01

Date: 2026-09-25 (America/Edmonton)

## Result

**PASS_OPEN_DEVELOPMENT_MECHANICS_ONLY.** All 12 positive cases matched their
frozen unified diff, and the independent screen-local applier reproduced all
12 exact target byte strings. All 9 boundaries produced the frozen
deterministic abstention, with no proposal fields or action. All 21 synthetic
fixture trees were unchanged. The screen had zero runtime errors and zero
retries.

| Draft operation | Exact diffs and independent applications |
| --- | ---: |
| Replacement | 3/3 |
| Append with one final LF | 3/3 |
| Insert after a unique single-line anchor | 3/3 |
| Explicit whole-line removal | 3/3 |

Boundary abstentions: 4 `patch_target_not_unique`, 1
`patch_anchor_not_unique`, 2 `patch_source_format_unsupported`, 1
`path_outside_allowed_root`, and 1 `patch_draft_requires_review_only`.
Every boundary route result parsed as JSON, carried the exact frozen
abstention status and reason, and contained no proposal fields.

## Measurement identity and evidence

- Job ID: `W2-LOCAL-PATCH-OPERATIONS-20260925-01`
- Nonce: `LPO01-SUPV-86C1`
- Protocol ID: `wrench.local.patch-operations.route-verifier.synthetic.v1`
- Frozen repository revision: `9a05ec7b774310a55b8f58329e06e8c5c108ec19`
- Protocol SHA-256: `5f7b0b8ad2ff73a5932abeb58b7dcab6e60ff658b2dbe13171ed61715e7d0551`
- Runner SHA-256: `53ae02a66288de8b47581186a7037e9a6048477795138f1736d2885245530e26`
- Receipt: `C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\patch-operations-screen-01.json`
- Receipt SHA-256: `18c7e2da64df8506be7aaddc4801ae04b39d859cf3fd685a01a50b90d53cfedb`
- Receipt size: 36,320 bytes; it contains no raw prompt, source or diff text.
- Frontier-token savings: null; there were no provider usage arms.

The source route, worker, core verifier, TTC verifier, toolbelt, Python
runtime, per-case hashes and results are pinned in the receipt. No model or
tokenizer was loaded, and there were no client or provider calls.

## Resource and command record

The run used the existing 15,000,000-byte reservation. Immediately before
execution, storage was `WITHIN_LIMIT`, C: had 172,973,494,272 bytes free,
available RAM was 16,649,688 of 33,486,624 KiB, and VRAM was 15,525 of 16,311
MiB free. Immediately afterward, storage remained `WITHIN_LIMIT`: actual use
was 10,112,943,296 bytes, active reservations were 16,103,000 bytes, projected
use was 10,129,046,296 bytes, and headroom was 39,870,953,703 bytes.

The screen command ran once and exited 0:

```powershell
python tools/measure_local_patch_operations_screen_01.py --output C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\patch-operations-screen-01.json --work-root C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\tmp\\patch-operations-screen-01
```

The stdout reported 21 cases, 12/12 positive exact oracles, 12/12 independent
applications, 9/9 boundary abstentions, unchanged fixture trees, null frontier
savings, and `PASS_OPEN_DEVELOPMENT_MECHANICS_ONLY`.

This one-shot run was invoked once under the frozen preregistration. The runner
refuses to overwrite its receipt path but does not globally block reuse of the
same job ID with a different output path. Any future invocation must use a new
preregistered measurement identity and must not be treated as a retry of this
screen.

## Limits

This accepts only the measured deterministic draft mechanics on small,
Wrench-authored UTF-8 LF fixtures with explicit bounded instructions. It does
not show that a patch is a semantically correct repair, complete coding work,
prove local SLM capability, establish real-task utility, or measure savings.
Generic multi-file or open-ended patch requests remain outside this result.
Training remains stopped.
