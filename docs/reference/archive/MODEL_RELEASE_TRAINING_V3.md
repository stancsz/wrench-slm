# Pro training V3 correction budget

Prepared 2026-09-09 after completed V2 development comparisons. All quality gates
remain unchanged. No sealed or challenge model evaluation has run.

V2 selected step 400 with 173/176 exact predictions. Its failures are two quoted
draft bodies and one zero-based line request. The final step-600 checkpoint
regressed on unsupported Chinese requests. This motivates a lower learning rate
and more varied training examples rather than further training at the old rate.

## Data

data/pilots/release-literal-v3 has 4,548 training records in 56 training families.
It retains all 3,076 V2 records and adds 768 complete-literal draft examples,
256 valid/invalid low-boundary examples, and explicit-path examples with stale
prior selections. Additional literal values, paths, and wording are authored
training variations. No development or challenge row is copied into training.
The existing development and sealed evaluation files remain byte-identical.

The preflight must pass schema, target-length, input/family separation, and label
conflict checks. Preserve all old data and candidate artifacts.

## Run and selection

- Initialize the adapter from the selected V2 step-400 weights, SHA-256
  f45cb39c14c2481839a0c3a15d2aea84487c48bc50137f301f27591d2bdbec37.
- Keep the pinned Qwen base, tokenizer, prompt formatter, and LoRA configuration.
  Verify initializer identity and tokenizer/formatter contract. Reset optimizer
  state explicitly; this is a new training phase, not a resume across datasets.
- First run a one-step warm-start machinery diagnostic, at most 16 example
  presentations, in a separate output directory. It is not a selected candidate.
- Main run: at most 300 optimizer steps, microbatch 2, accumulation 8, constant
  learning rate 0.00002, seed 42, BF16, maximum sequence length 1536. This permits
  at most 4,800 example presentations. Zero cloud calls, no automatic retry.
- Limit the PyTorch CUDA allocator to 55% of device memory. Reserve at most
  60 minutes including validation and checkpoint writes.
- Save and compare steps 100, 200, and 300 on the unchanged 176-case development
  set. Select highest exact-call rate, then lowest validation loss, then earliest
  step. Run the 37 additional development context probes on the selected model,
  requiring at least 95% exact predictions and a passing packaged quickstart.
- Only a candidate passing the unchanged gates proceeds to the frozen 66-case
  independent challenge and 440-case release evaluation. All assigned cases and
  failures remain in their denominators. Further changes require a fresh budget,
  and any scored evaluation used to guide changes must be retired from testing.

Success means measured model improvement and a release-ready weight artifact.
Completing this training phase alone does not complete goal.md.
