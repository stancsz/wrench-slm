# Phase 234: standard Hugging Face hybrid load

Status: `PASS_STANDARD_HF_CONFIG_TOKENIZER_HYBRID`

The pinned BF16 Safetensors candidate was loaded with the dedicated
Transformers 5.17.0 runtime through the standard `AutoConfig`,
`AutoTokenizer`, and `AutoModelForImageTextToText` paths. Full weight loading
completed successfully.

Receipt facts:

- model class: `Qwen3_5MoeForConditionalGeneration`;
- model type: `qwen3_5_moe`;
- loaded parameter count: `3,881,244,016`;
- tokenizer model max length: `262,144`;
- declared logical raw input limit: `4,000,000`;
- declared effective working context: `64,000`;
- full-weight load: verified;
- weight-load elapsed: `10,170.521 ms`.

The tokenizer does not advertise a native 4M dense sequence, and the receipt
records that fact explicitly. The supported product contract is hybrid:
model-local raw intake accepts the 4M payload, the embedded first-layer gate
reduces it, and standard HF generation receives the bounded working context.
This is not a dense-native 4M quality claim.

Evidence: `receipt.json`.
