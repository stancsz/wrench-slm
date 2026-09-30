# Iteration 192: return the prompt-manifest hash from the projection loader

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Change

Iteration 191 found that `load_prompt_projection()` verified the pinned
manifest file but returned the prompt payload hash. The caller stored that
return value in `prompt_manifest_sha256`, while score admission compared that
field with the manifest-file hash. The loader now returns
`sha_bytes(manifest_bytes)` after verifying it against `PROMPT_MANIFEST_SHA`.
The payload identity remains separately represented by
`prompt_projection_sha256`.

This closes a second receipt mismatch. The successful preflight 09 receipt is
stale because it binds the previous scorer SHA; do not reuse it for score mode.
The corrected fit-manifest and training-protocol bindings from Iteration 186
remain in place, and the score gate directly checks both fields.

## Exact identities and no-run boundary

| Item | SHA-256 / identity |
|---|---|
| Repository HEAD | `af01304824f079a64b6c3902397a2034b843511a` |
| Updated scorer | `4E2E69E1AE89B553470FE3ABE9EE5776C70D35942B99E8B4509C7FA71F159E85` |
| Evaluation protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Iteration 191 HOLD report | `49A17FD073F0BAC721BE050C5A6DA0A0F6F54B5B764D5E4008ABAFBF97C5B6D2` |
| Prior successful preflight 09 receipt (stale scorer identity) | `5F2F875404B8531BDA0B9A09C02332DC213E69A4814C9DE1A23426CA3476E9DD` |

The updated scorer has not been independently reviewed or executed. No tests,
inference, provider calls, or held-out access followed this edit. `git diff
--check` found no whitespace errors and printed only the existing repository
line-ending notices.

## Next gate

Obtain a fresh exact-hash review of the updated scorer for a one-prompt
preflight. If it passes, run a new preflight with its own storage reservation
and fresh resource admission. The resulting receipt must contain the scorer
SHA, prompt-manifest SHA, prompt-payload SHA, fit-manifest SHA, and
training-protocol SHA in their distinct fields. Review that exact receipt and
the updated scorer again before a separately reserved 64-row score. Keep the
held-out split sealed.
