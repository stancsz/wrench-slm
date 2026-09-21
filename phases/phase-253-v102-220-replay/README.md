# Phase 253: v102 220-case mechanical-worker replay

Status: `PASS_MECHANICAL_WORKER` on the current RTX 5070 Ti host. This is a
historical fixture gate and not a production release authorization.

## Candidate and run

- Package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v102-ollama-cli`
- Cases: `evals/wrench-expanded-v2/cases.jsonl`, 220 traces
- Teacher capture: `phases/phase-185-v2-teacher-capture/teacher-220-v2-max1024.json`
- Runtime path: package-local HTTP server plus killable UTF-8 local worker
  subprocess, with the identical MiniMax capture used for fallback
- Resource policy: no model generation was loaded for this diagnostic replay;
  no extra VRAM allocation was requested

## Full result

The `wrench_plus_identical_minimax_fallback` arm recorded:

- final success: `0.9965032764`
- verifier success: `1.0`
- weighted mechanical frontier-token coverage: `0.9929861390`
- net frontier-token savings: `1.0`
- frontier tokens: `0`
- local tokens: `24,141`
- fallback count: `0`
- median latency: `185.095 ms`
- p95 latency: `299.445 ms`
- prohibited accepts: `0`
- unexpected mutations: `0`

All five evaluator gates are true. The result remains diagnostic because the
220-case fixture is not the approved family-disjoint real-workflow set, and
the run does not prove native dense decoder quality, 5060 Ti performance, or
production enablement.

## Fixes verified by this phase

1. Literal lookup uses a bounded, fixed-string ripgrep fast path with sorted
   output, excluded binary/weight suffixes, a global match cap, and a hard
   five-second subprocess deadline. On the current repository, searches that
   previously took about 8 to 10 seconds completed in about 36 to 345 ms.
2. The local worker subprocess writes its JSON envelope as UTF-8 bytes, and
   the diagnostic parent decodes the child stream explicitly as UTF-8. This
   prevents Windows cp1252 failures when read/search observations contain
   box-drawing or non-Latin characters.

Evidence files:

- `evaluation.json`
- `trace-manifest.json`
