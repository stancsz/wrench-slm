# Local review-only patch-draft screen 02

Status: frozen before execution. Date: 2026-09-25.

## Question and claim

Can the deterministic local route produce exact review-only diffs for four
explicit edits on new, tiny synthetic files, independently apply each diff to
the source bytes, and abstain on six frozen boundaries?

This is exposed open-development mechanics evidence. The prior screen exposed
parser and formatting defects that informed implementation; these new inputs
do not establish holdout generalization. A pass supports only the tested
deterministic draft mechanics. It does not establish semantic code fixes,
model-authored patches, completed coding tasks, real-repository utility or
frontier-token savings. The worker uses no model or tokenizer.

## Frozen cases and exact target trees

Every case runs under a separate temporary root outside the repository. The
four positive expected target trees are frozen in
`tools/measure_local_patch_draft_screen_02.py`. Positive operations are one
unique replacement, append, insert after a unique final line, and remove one
unique setting. All four source files use UTF-8, LF line endings, and a final
newline. The expected changed path and full target bytes form the independent
oracle.

The six boundaries are duplicate replacement target, duplicate insertion
anchor, unterminated and CRLF source formats, an explicitly described missing
file and an explicitly described outside-root path. The two newline cases
must abstain with `patch_source_format_unsupported`. The last two exercise
deterministic prompt-phrase guards; they do not test filesystem path
resolution. Each must
be intercepted by the deterministic route (`mechanical_fast_path=true`) with
its frozen reason (`patch_target_not_unique`, `patch_anchor_not_unique`,
`patch_source_format_unsupported`, `patch_file_invalid`, or
`path_outside_allowed_root`) and no action. An
abstention from `model_not_loaded` does not pass. No retry is allowed.

## Acceptance rule

- All four positive cases return `accepted` / `patch_draft` with exactly one
  expected relative path, the exact independent unified diff, and a deep TTC
  pass. Every observation has `review_only=true` and `applied=false`.
- An independent screen-local parser checks the diff header paths, hunk
  location and line counts, applies the hunk to the original fixture bytes,
  and requires byte-for-byte equality with the frozen target file.
- All six boundaries return their exact route reason without an action.
- Every fixture tree has identical file and directory paths plus file hashes
  before and after its route. A wrong diff, incorrect target application,
  unsafe acceptance, verifier failure, fixture mutation or runtime error
  fails the screen.
- The receipt contains no source text or raw diff. It records only prompt,
  proposal, target-file/tree and fixture-tree hashes plus outcomes and case
  identities.

## Measurement identity and limits

- Job ID: `LOCAL-PATCH-DRAFT-SCREEN-20260925-02`
- Nonce: `PDS02-6C2A`
- Protocol ID: `wrench.local.patch-draft.route-verifier.synthetic.v2`
- Runner: `tools/measure_local_patch_draft_screen_02.py`
- The receipt pins the mechanical route, worker, core verifier, TTC verifier
  and toolbelt hashes.
- No local SLM inference, training, client, provider, network or model weights.
- Keep frontier savings unavailable; this screen has no provider usage arms.

## Resource admission and command

Before execution, run the storage checker `status` and reserve 8,000,000 peak
additional bytes under this unique job ID. Check C: free space and confirm at
least 10% RAM and VRAM free. The route itself is CPU-only; any VRAM measurement
is a point-in-time host-reserve check, not workload use. Use a new, empty
temporary work root and a nonexisting output path under
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability`. Recheck storage
afterward and release the reservation only after accounting for the receipt.

```powershell
python tools/check_wrench_storage_budget.py status
python tools/check_wrench_storage_budget.py reserve --job-id LOCAL-PATCH-DRAFT-SCREEN-20260925-02 --reserve-bytes 8000000
python tools/measure_local_patch_draft_screen_02.py --output C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\patch-draft-screen-02.json --work-root C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\tmp\\patch-draft-screen-02
```
