# Local SLM acceptability run 01

Date: 2026-09-24 (America/Edmonton)

## Result

**Invalid as model-quality evidence.** The pinned runtime and Qwen model loaded,
but the runner stopped on the first case before calling `model.generate`. The
tokenizer returned a `BatchEncoding`; the runner treated it as a flat tensor
and attempted to convert the key `input_ids` to an integer. A separate
tokenizer-only reproduction on the same frozen prompt produced:

```text
ValueError: invalid literal for int() with base 10: 'input_ids'
```

The runner output retained one failed case and nine `not_run` rows. It recorded
zero model calls, zero prompt/completion tokens, no tool attempts, and no task
answers. All five task classes remain **unmeasured**, not unacceptable. This is
a harness defect, not a capability failure.

The durable runner receipt is
`C:\wrench-slm-data\artifacts\wrench-local-acceptability\qwen35-0.8b-synthetic-20260925-01.json`,
SHA-256 `7169861498761d6d0627d0055c3c1b34f89e7ee8d8ef4203689ee86f1140f962`.
It used runner commit `46aaa12`, fixture SHA-256
`871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`, model
revision `2fc06364715b967f1860aea9cf38778875588b17`, and runtime lock SHA-256
`0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420`.

## Runtime and resource observations

- Python 3.13.15, Transformers 5.17.0, Tokenizers 0.23.2, Hugging Face Hub
  1.33.0, Torch 2.14.0+cu132, CUDA 13.2; the report confirms all 35 pinned
  distributions.
- Model/config classes: `Qwen3_5ForCausalLM` and `Qwen3_5TextConfig`; verified
  tokenizer template SHA-256 `273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80`.
- During loading, 22 resource samples observed minima of 45.18% free RAM and
  86.99% free VRAM. The largest sampled interval was 1.875 seconds. After load,
  one sample showed 48.59% free RAM and 85.17% free VRAM.
- No reserve breach occurred. These samples cannot rule out shorter transient
  dips.

## Token and utility status

Frontier-token savings remain **N/A**, with zero matched frontier usage pairs.
No generated local token counts or completed task outcomes exist. Do not enter
this run into a model-quality, utility, customer, training, or production
aggregate.

## Follow-up

The runner now unwraps `BatchEncoding["input_ids"]` before token counting and
generation. One separately preregistered run 02 is recorded in the protocol;
run 01 remains unchanged and will not be retried or combined with it.
