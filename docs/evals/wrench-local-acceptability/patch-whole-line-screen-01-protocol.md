# Local whole-line removal screen 01

Status: preregistration; execute only from the committed revision. Date: 2026-09-25.

## Question and claim

Can the deterministic route draft an exact, unapplied diff when a review-only
request explicitly says to remove the entire line containing one quoted
setting, and abstain on duplicate, missing, malformed, or inaccessible inputs?

This is exposed open-development mechanics evidence only. Screen 02 raised the
whole-line behavior during development, so these new cases are not a holdout
and cannot establish generalization. A pass supports only the explicitly
worded whole-line operation on these small synthetic LF files. It does not
accept generic patch drafting, establish a semantically correct code fix,
complete a coding task, establish local SLM capability or real-task utility, or
measure frontier-token savings.

## Frozen cases and exact target trees

The nine cases and expected target bytes are frozen in
`tools/measure_local_whole_line_patch_screen_01.py`. Three positives remove a
unique entire line from a new synthetic file: a middle line, final line, and
first line. The middle-line case leaves `cache=warm\nretry=2\n`; the final-line
case leaves `MODE=safe\nRETRY=3\n`; the first-line case leaves
`locale=en-CA\n`. Each expected target therefore ends in exactly one LF. Each
prompt names the complete-line operation with the exact verb `remove`, a
quoted marker, a relative path and review-only/no-apply intent. Every input is
UTF-8, LF-only, and newline-terminated. Each expected target preserves all
remaining bytes exactly, including its final newline.

Six boundaries cover two matching lines, no matching line, an unterminated
source, CRLF source, an explicitly missing-file request, and an explicit
outside-root request. Every boundary must be intercepted by the deterministic
route with its exact expected reason and no action. A model-not-loaded
abstention does not pass. No retry is allowed.

## Acceptance rule

- All three positives return `accepted` / `patch_draft` with exactly one
  expected relative path, the exact unified diff to the frozen target, a deep
  TTC pass, `review_only=true`, and `applied=false`.
- A screen-local independent parser validates the single-file diff header,
  hunk position and line counts, applies it to the original bytes, and requires
  byte-for-byte equality with the frozen target.
- All six boundaries return the exact frozen route reason without an action.
- All fixture file and directory identities are unchanged after routing.
- Any incorrect diff, target application, boundary result, fixture mutation,
  verifier failure, or runtime error fails the screen.
- The receipt records hashes and outcomes without source text or raw diffs.

## Measurement identity and limits

- Job ID: `LOCAL-PATCH-WHOLE-LINE-SCREEN-20260925-01`
- Nonce: `PWL01-91D7`
- Protocol ID: `wrench.local.patch-whole-line.route-verifier.synthetic.v1`
- Runner: `tools/measure_local_whole_line_patch_screen_01.py`
- Pin the protocol, runner, mechanical route, worker, core verifier, TTC
  verifier and toolbelt hashes in the receipt.
- No model/tokenizer load, inference, training, client, provider, network, or
  model weights.
- Frontier savings remain null; there are no provider usage arms.

## Resource admission and command

Before execution, run `status`, then create a fresh reservation under this
screen's unique job ID for the accounted peak bytes. Check C: free space and
confirm at least 10% RAM and VRAM free. The route is CPU-only; VRAM is a
point-in-time reserve check. Use a new empty temporary directory and a
nonexisting receipt path under
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability`. Recheck storage
after execution. Release the reservation only after the job stops and the
receipt is accounted for.

```powershell
python tools/check_wrench_storage_budget.py status
python tools/check_wrench_storage_budget.py reserve --job-id LOCAL-PATCH-WHOLE-LINE-SCREEN-20260925-01 --reserve-bytes 8000000
python tools/measure_local_whole_line_patch_screen_01.py --output C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\patch-whole-line-screen-01.json --work-root C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\tmp\\patch-whole-line-screen-01
```
