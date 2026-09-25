# Local review-only patch-draft screen 01

Date: 2026-09-25 (America/Edmonton)

## Result

**FAIL. No patch-draft work family is accepted.** The frozen six-case
synthetic screen returned one exact review-only draft out of three positive
cases. All three boundary cases abstained. Every fixture tree was unchanged.

| Case | Result | Evidence |
| --- | --- | --- |
| Unique replacement | Abstained (`patch_content_missing`) | The prompt used “replacing”; the deterministic parser did not recognize the request. |
| Append line | Exact accepted draft | Exact file list and diff matched; deep TTC passed; `review_only=true`; `applied=false`. |
| Insert after unique text | Accepted, oracle mismatch | The generated diff inserted an extra blank line. Deep TTC passed, showing that its current proposal-only diff gate does not compare the draft against the independent target. |
| Duplicate target | Abstained (`patch_content_missing`) | Correct fail-closed boundary behavior. |
| Missing file | Abstained (`patch_content_missing`) | Correct fail-closed boundary behavior. |
| No review-only authority | Abstained (`model_not_loaded`) | Correct fail-closed boundary behavior; no model was available or called. |

The all-cases rule in the frozen [protocol](../../evals/wrench-local-acceptability/patch-draft-screen-01-protocol.md)
requires every positive oracle to match. The two positive failures therefore
fail the screen, even though the route abstained safely on the boundary cases.
The accepted append is a case result, not an accepted work category.

## Identity and accounting

- Protocol ID: `wrench.local.patch-draft.route-verifier.synthetic.v1`
- Protocol SHA-256: `5840b83335ef37ea4462091aafb56591735b3a28c7980c156566867ec38f0d65`
- Runner SHA-256: `b5808d22849463a992649338953851aef480bd1f754a22f9a06f41e18757de3e`
- Mechanical route SHA-256: `96cabc916d18814aa70b8ba462d43f0eba29b4c9b1ce5c117230c290b25c3d8a`
- Core verifier SHA-256: `b51ec5251f881ccff92577e5385fdfafb4e29390a57f438d909496cd1eadcffd`
- Worker SHA-256: `9149c10fbbb0c34c82817ca0f1945919ac0f005e508c08960220ef05661aa851`
- Runtime: CPython 3.11.16, Windows x86-64
- Model and tokenizer loaded: no; model calls: 0; provider and client calls: 0
- Cases: 6; exact positive oracles: 1/3; boundary abstentions: 3/3
- Fixture trees unchanged: yes; elapsed time: 109.426 ms
- Receipt: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\patch-draft-screen-01.json`
- Receipt SHA-256: `D69AB3F79D26E5EF8FE6910FA4832BBD6DFEA869A3E3794AC4BAEFC6C0022FB1`

This is an open-development synthetic mechanics diagnostic. It is not a
real-task success rate, a local SLM result, or evidence of frontier-token
savings. The TTC pass on the wrong insert diff exposes a verifier limitation:
the generic patch-draft executor does not establish that a diff's hunk is the
expected change to the selected source. The deterministic route's generated
diff must still match an independent task oracle before it can be accepted.

## Decision

Keep review-only patch drafting outside the accepted local-work envelope.
Retain the existing narrow exact-read, line-read, and literal-search scope.
Training remains stopped. A future development screen may follow a parser or
diff-generation fix, but it must use a new frozen protocol and clearly remain
diagnostic if the fixture families have already informed implementation.
