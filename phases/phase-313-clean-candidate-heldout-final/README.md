# Phase 313: clean candidate held-out final split

This is a fresh, no-training, held-out diagnostic against the current
`evals/wrench-expanded-v2/final.jsonl` split. The teacher capture was made
against the current final split because older final receipts used a different
input hash.

## Controls

- Candidate package: `D:\models\_wrench-release-candidate-20260921`
- Clean source commit used to materialize the package:
  `e83a454f85be6881e989c9453291ef35d0b97429`
- Final cases hash:
  `3e24ba47b78a99b1ef81bb8ea269e4377ca45097186812ce71aa99bb2c2f222b`
- Teacher capture: external temporary file only, not committed because it
  contains raw workflow prompts and responses.
- Teacher requests: `44/44`, zero transport failures, zero invalid responses.
- Client mechanical fast path was bypassed and the allowlisted health fixture
  was enabled.

## Result

- Wrench plus identical MiniMax fallback weighted final success: `1.0`
- Wrench verifier success: `1.0`
- Weighted mechanical frontier-token coverage: `1.0`
- Net frontier-token savings: `1.0`
- Wrench frontier tokens: `0`
- Wrench local tokens: `4,805`
- Wrench median / p95 latency: `183.104 ms` / `297.706 ms`
- Prohibited accepts: `0`
- Unexpected mutations: `0`
- Paired final-success difference CI: `[0.0, 0.1136364]`

The teacher-only arm scored `0.9488988` weighted final success and had two
prohibited accepts. This is not a claim that Wrench generally outperforms
MiniMax. The evaluation manifest remains `DRAFT_PENDING_HUMAN_APPROVAL`, so
this is sealed-split diagnostic evidence, not final family-disjoint approval,
production readiness, native dense 4M quality, or independent 5060 Ti proof.
