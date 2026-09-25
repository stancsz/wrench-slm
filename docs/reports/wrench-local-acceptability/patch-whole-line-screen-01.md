# Local whole-line removal screen 01

Date: 2026-09-25 (America/Edmonton)

## Result

**PASS for narrow, open-development draft mechanics.** The deterministic route produced exact review-only whole-line removal diffs for all 3/3 positive synthetic cases. The screen-local independent applier reproduced all 3/3 frozen targets. All 6/6 boundaries abstained with the expected route reason. Every fixture tree remained unchanged.

This accepts only requests that explicitly say to remove the entire line containing one quoted marker, from a uniquely matching, UTF-8 LF-terminated synthetic file. The operation is a proposal: `review_only=true`, `applied=false`. Cases cover first, middle, and final line positions. The screen does not accept generic patch drafting, completed coding work, a local SLM task class, real-work utility, or frontier-token savings. The operation was exposed during screen 02 development, so this is not holdout or generalization evidence.

## Identity and accounting

- Frozen protocol: [whole-line screen 01](../../evals/wrench-local-acceptability/patch-whole-line-screen-01-protocol.md), SHA-256 `04026a0cbada505736c80931b5ff05fad3aecf284587c03f4dbde678048545ee`.
- Job ID: `LOCAL-PATCH-WHOLE-LINE-SCREEN-20260925-01`; nonce: `PWL01-91D7`.
- Committed source, tests, runner, protocol, and proposal report: `ae1beb969666429f06785b7409f571f55f230c22`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\patch-whole-line-screen-01.json` (13,505 bytes), SHA-256 `0f58c7633d4fce22e03fee2a67963aa4dc92a55b2fc63288163a9b49e5506bbb`.
- Receipt pins for protocol, runner, and route match the committed files; independent receipt review found all nine observations consistent with the frozen rule.
- Independent evaluation: [whole-line screen 01 review](../../evals/wrench-local-acceptability/patch-whole-line-screen-01.md).
- Model/tokenizer loads: 0; provider/client calls: 0; fixture mutations: 0; frontier-token savings: null.
- Pre-run host check: C: free 172,960,358,400 bytes; available RAM 16,219 MiB; VRAM 15,535/16,311 MiB free. Storage was `WITHIN_LIMIT`; the receipt was included in the post-run inventory before the 8,000,000-byte reservation was released.
- `git diff --check` and in-memory AST syntax parsing of the route, focused fixture test, and runner passed before commit. No pytest run was made.

## Relation to screen 02

Screen 02 remains a failure: 3/4 positive drafts matched its frozen exact diff oracle and all six boundaries passed, but its removal case did not match the target tree. Review found the whole-line interpretation defensible for a settings record. The new route supports that intent only when the prompt explicitly requests removal of the entire line. The full generic patch-draft family remains unaccepted; this narrower result cannot turn screen 02 into a pass.
