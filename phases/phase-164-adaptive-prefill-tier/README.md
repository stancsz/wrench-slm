# Phase 164: adaptive prefill tier

This phase adds a deterministic working-context tier to the MapReduce path.
The default remains 64K. A long payload can promote to 128K only when the
latest intent contains an explicit context-sensitive marker such as `compare`
or `root cause`. The promotion is bounded by
`WRENCH_MODEL_PREFILL_MAX_BUDGET` and is recorded in the dynamic-prefill
receipt.

This is hybrid working-context evidence. It is not dense native 2M/4M
attention evidence, and it does not authorize a production quality claim.

## Verification

- `pytest -q`: 152 passed, 14 warnings.
- `pytest -q tests/test_embedded_worker.py tests/test_prefill.py`: 22 passed.
- deterministic route replay: 220/220 mechanical fast path, 200/220 strict
  fixture outcome matches, 0 prohibited accepts, 7.503 ms total on the local
  replay process.
- the route evaluator now passes its declared `--root` into the mechanical
  parser. Rebuilding the prompt-complete derived contract and replaying all
  220 cases against its fixture produced 220/220 mechanical fast paths,
  220/220 strict outcome matches, 0 prohibited accepts, and 16.471 ms total.
  The historical sealed fixture remains unchanged and still reports its
  under-specified generic patch cases separately.
- adaptive smoke: a 1,100,046-character old trace plus `Compare ... find the
  root cause` selected 128,000 tokens, produced a 33-token staged prompt in
  the compact-card case, and retained one reference card.
- portable package v67 materialized from the v66 weight source passed
  `PASS_STRUCTURAL_PACKAGE`; its package-local worker accepted the bounded
  mechanical read and emitted the same 128K adaptive receipt.
- the bundled runtime was published to Hugging Face at revision
  `842c42e64bf0a3ec89cb458eba90c403f5f19c61`. A fresh download of
  `wrench_runtime/worker.py`, `wrench_runtime/mechanical.py`,
  `wrench-package.json`, and `wrench-runtime.json` matched the local package
  hashes; the remote worker contains `_adaptive_prefill_budget`.
- simple long-context behavior remains on the base tier. The existing worker
  test with a generic review sentence continues to assert the 64K ceiling.

The 20 strict fixture mismatches are the pre-existing generic patch cases whose
targets contain invented diff bodies absent from their prompts. The worker
continues to abstain with `patch_content_missing`; this phase does not weaken
that safety rule.

## Hashes

- `src/wrench_harness/worker.py`: `2d4e0ba69dba1dff6f235e9fab36ee0c9f1af154643c0d67f5ce1de851632f19`
- `tests/test_embedded_worker.py`: `e04b98360582c6854adc103d843f29f77d4515eb663d5b916697edebcc10e4d1`
- `docs/WRENCH_MODEL_TOOLBELT.md`: `b7012a4cfcd65d7ddde72e0741ea27fac444578b5072c6f179f691d070ac6857`
- `tools/evaluate_mechanical_route.py`: `657337dbe1c609d69043bb9211b9f9c1f762c9b780a1e37a26aaf95803350b72`
- `tests/test_evaluate_mechanical_route.py`: `9e7e142f6cc29aa0fddf885e50529a15a912181f3286ddb393936004badf374e`
- case fixture `evals/wrench-expanded-v1/cases.jsonl`: `54d06dff69c2a330fbba5ed13ba22817c287cb7ec384a59458eb4f5e291bb45a`

`quality_claim`, `native_attention_claim`, and `production_enablement` remain
false.
