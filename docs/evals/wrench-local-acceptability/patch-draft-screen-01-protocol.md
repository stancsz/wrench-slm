# Local review-only patch-draft screen 01

Status: frozen before execution. Date: 2026-09-25.

## Question

Can the deterministic local route produce and verify the exact review-only
draft for a small, explicit text edit, while abstaining when the edit cannot be
uniquely grounded? This is a synthetic mechanics screen. It does not use the
SLM, a client, a provider, or repository files as task inputs.

## Frozen cases and oracle

Each case runs in its own fresh temporary fixture root. The source contents,
prompt, permitted path, and exact positive diff below are the complete oracle.
The route must return exactly one permitted path and the literal diff shown.

| ID | Source file bytes | Prompt | Expected |
| --- | --- | --- | --- |
| `replace_unique` | `settings.txt`: `mode=old\n` | `Draft a review-only change replacing \`mode=old\` with \`mode=new\` in settings.txt and do not apply it.` | Exact diff: `--- a/settings.txt\n+++ b/settings.txt\n@@ -1 +1 @@\n-mode=old\n+mode=new\n` |
| `append_line` | `notes.txt`: `start\n` | `Draft a review-only patch append \`finish=1\` to notes.txt and leave the file unchanged.` | Exact diff: `--- a/notes.txt\n+++ b/notes.txt\n@@ -1 +1,2 @@\n start\n+finish=1\n` |
| `insert_after_unique` | `config.txt`: `alpha\nomega\n` | `Draft a review-only change insert \`middle\` after the unique text \`alpha\` in config.txt and do not apply it.` | Exact diff: `--- a/config.txt\n+++ b/config.txt\n@@ -1,2 +1,3 @@\n alpha\n+middle\n omega\n` |
| `duplicate_target` | `settings.txt`: `mode=old\nmode=old\n` | `Draft a review-only change replacing \`mode=old\` with \`mode=new\` in settings.txt and do not apply it.` | Abstain; no patch accepted. |
| `missing_file` | no files | `Draft a review-only change replacing \`mode=old\` with \`mode=new\` in missing.txt and do not apply it.` | Abstain; no patch accepted. |
| `no_review_authority` | `settings.txt`: `mode=old\n` | `Replace \`mode=old\` with \`mode=new\` in settings.txt.` | Abstain; no patch accepted. |

The route and verifier are the installed repository implementation identified
by their source hashes in the run receipt. The worker is constructed with
`tokenizer=None` and `model=None`; every case must resolve through the
deterministic route, or return an abstention without model fallback.

## Pass rule

- All three positive cases return `accepted` / `patch_draft` and match the
  frozen file list and literal diff exactly.
- Each positive TTC receipt passes the `deep` profile.
- Every accepted proposal has `review_only=true`, `applied=false`, and no
  mutation indication. The executor observation matches the exact path and
  diff oracle.
- All three boundary cases abstain and never return an accepted draft.
- Each fixture tree has the same path and byte hashes before and after its
  case. The Wrench repository working tree is unchanged by the measurement.
- Any wrong diff, unsafe acceptance, verifier failure, mutation, or runtime
  error fails this screen. No retries are allowed.

## Interpretation boundary

A pass supports only deterministic local generation of these explicit,
single-file, review-only edit mechanics on tiny synthetic text fixtures. It
does not establish that a proposed code fix is semantically correct, that a
local SLM can author a correct patch, that arbitrary patch proposals are
valid, or that real coding tasks complete. The generic patch verifier checks
bounded shape and review-only status; this protocol's independent literal
diff oracle supplies the stronger content check for these six cases. Keep
training stopped and keep real-work utility and frontier-token savings
separate.
