# Phase 75: bundled mechanical runtime

Status: `BUNDLED_RUNTIME_PASS_DIAGNOSTIC_QUALITY_GATE_OPEN`

The portable model directory now includes the custom tokenizer hook,
mechanical prefill, and high-confidence mechanical router. A local
Transformers dynamic-module load succeeded with `AutoTokenizer`,
`trust_remote_code=True`, and `local_files_only=True`. The loaded class was
`WrenchTokenizer`, `model_max_length` was 4,000,000, and its embedded route
returned a valid bounded proposal without a model call.

The original v7 Safety checkpoint plus the mechanical fast path was replayed on
all 220 historical cases: 156/220 correct outcomes, 80/120 exact eligible
accepts, zero prohibited accepts, zero transport failures, and 137 mechanical
fast-path requests. This is a meaningful diagnostic improvement over the
historical pure-model 90/220 receipt, but it is not the final MiniMax matched
workflow gate.

Receipts:

- `phase-75-portable-mechanical-runtime-validation.json`
- `phase-75-portable-mechanical-runtime-eval-220.json`
