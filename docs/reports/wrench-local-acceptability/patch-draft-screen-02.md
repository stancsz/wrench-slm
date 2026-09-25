# Local review-only patch-draft screen 02

Date: 2026-09-25 (America/Edmonton)

## Result

**FAIL. Patch drafting remains outside the accepted local-work envelope.**
Three of four positive synthetic drafts matched the exact target diff and
passed the independent apply-to-target check. All six boundary cases produced
their expected deterministic abstention. All ten fixture file/directory
identities remained unchanged.

| Case | Result |
| --- | --- |
| Unique replacement | Exact diff and target application passed |
| Append | Exact diff and target application passed |
| Insert after unique line | Exact diff and target application passed |
| Remove unique setting | Failed exact diff match and target application |
| Duplicate replacement target | Abstained: `patch_target_not_unique` |
| Duplicate insertion anchor | Abstained: `patch_anchor_not_unique` |
| Unterminated source | Abstained: `patch_source_format_unsupported` |
| CRLF source | Abstained: `patch_source_format_unsupported` |
| Explicit missing-file phrase | Abstained: `patch_file_invalid` |
| Explicit outside-root phrase | Abstained: `path_outside_allowed_root` |

The failing positive had a passing deep TTC shape check, but the independent
diff comparison rejected it. Its expected diff SHA-256 was
`d52438ff4008d06adda0060cdec64aa37b2a1924500ad016ffc0dbf3da7da474`; the
observed diff SHA-256 was
`cf554915a2c02682c502f3339526c6169fc5367f78f330c4f456f479dfa46d13`.
Source inspection after the run found that the current remove operation
removes the exact substring and preserves its newline. That explains why the
line-removal oracle does not match, but the receipt intentionally retains no
raw source or diff text.

The all-cases rule therefore fails. The three positive successes are
individual mechanics observations only. The phrase-triggered missing/outside
cases verify explicit prompt guards, not filesystem path resolution. The
newline cases verify fail-closed source-format handling. This screen used no
model, tokenizer, client, provider, training, network or repository source as
task input.

## Identity and accounting

- Preregistration:
  [protocol 02](../../evals/wrench-local-acceptability/patch-draft-screen-02-protocol.md).
- Protocol ID: `wrench.local.patch-draft.route-verifier.synthetic.v2`.
- Job ID: `LOCAL-PATCH-DRAFT-SCREEN-20260925-02`; nonce: `PDS02-6C2A`.
- Repository commit: `e4e8051` (`feat: bound local review patch drafting`).
- Cases: 10; exact positive diffs and target applications: 3/4; exact
  boundary abstentions: 6/6; unchanged fixture identities: yes.
- Model/tokenizer loads: 0; provider/client calls: 0; fixture mutations: 0.
- Receipt: `C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\patch-draft-screen-02.json`.
- Receipt SHA-256:
  `278439ae71168e02be358825a2621b3a336ea359f05105aa3ba80d606e9eef21`.
- Post-run storage: `WITHIN_LIMIT`; actual 10,112,732,958 bytes, active
  reservations 1,103,000 bytes, projected 10,113,835,958 bytes, headroom
  39,886,164,041 bytes. The job's 8,000,000-byte reservation was released.

This is an exposed synthetic mechanics screen. It does not establish correct
coding work, local SLM capability, real-repository utility or frontier-token
savings. The latter remains **N/A** with zero eligible matched usage pairs.
