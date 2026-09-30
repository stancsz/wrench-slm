# Iteration 207: corrected local run report

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER207-20260929-01`  
Nonce: `bb6a95d6-20fb-41af-9d4e-353522f36537`  
Protocol: [Iteration 207 protocol](iteration-207-qwen35-4b-lora-context-pair-protocol-20260929.md), SHA-256 `16CCEF663C320A3E69E5D9F16216A1316D91487285DA5275791B2F2CE8DD5676`  
Runner SHA-256: `8DEB4C80A1394C9B83616165101013C21D7A3E4E6A284A3676D37698D8E96144`  
Static review: [Iteration 207 package review](iteration-207-package-review-20260929.md), SHA-256 `3FBAEC4ED4C3739758D907819A5F76F1012F6D096162DBFA68A285D14FB37418`  
Required repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Result

The corrected pinned run completed on the RTX 5060 Ti. The receipt is
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iteration-207-qwen35-4b-lora-context-pair.json`, 11,133 bytes, SHA-256 `012369D65CEEF36575456385680CA51DDB03BB368103D2B156CA922CF9F2BA9C`.

| Model arm | Full-context verified | Wrench-context verified | Full input tokens | Wrench input tokens | Local input reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3.5-4B base | 3/3 | 3/3 | 26,244 | 521 | 98.0148% |
| Qwen3.5-4B + inactive screen-03 LoRA | 3/3 | 3/3 | 26,244 | 521 | 98.0148% |

Each row preserves the raw decoded answer, including its trailing newline, and
the answer after trimming only outer ASCII space, tab, CR, and LF. The
preregistered verifier scored the normalized output exactly against the
expected answer. Input reduction uses the local Qwen tokenizer. Including the
same 25 answer tokens per arm, total local tokens fell from 26,269 to 546,
97.9215%.

The 64 saved LoRA tensors attached and matched their checkpoint values exactly
before generation. The verified key-list hash is
`da49c7c11d9de18ba5fc2a1f2db0ef2c1c02b813ced9cf7706e6af26b8bcf4cc`. This
resolves the Iteration 206 adapter-loader defect for this pinned adapter and
runtime path.

These are three previously exercised authored synthetic lookup cases, not
held-out or representative engineering work. The run made zero Frontier
calls, so Frontier token savings and all-in cost savings remain `null`. The
98.0148% figure is local prompt-token reduction on these fixtures, not measured
API usage, route reduction, task coverage, or evidence for the 95/5/95 target.
It does not show that the LoRA improved these three answers over the base, or
that either arm can code all day.

## Runtime and resources

- Base: `Qwen/Qwen3.5-4B`, revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, pinned 14-file snapshot
  totaling 9,342,907,469 bytes.
- Adapter: screen-03 fit-01, evaluated inactive; weights SHA-256
  `051a942cc306d15ff22ad300d6256cc4b8e6335b9c6263b65696353b04938e5c`,
  config SHA-256
  `f77ecf3c2e87b2586563f3ca6017b74f62b180c31f67260a590ccff85453531f`.
- Model loader: `AutoModelForImageTextToText`, matching the screen-03 trainer.
- Python 3.13.15, Torch `2.14.0+cu132`, Transformers `5.17.0`, PEFT
  `0.21.0`, CUDA `13.2`; exact isolated environment/package identity is in
  the receipt.
- Model load: 29.3872 s. Total generation: 75.4867 s. Full run: 76.5181 s.
- Peak CUDA allocated/reserved: 11,590,222,336 / 12,643,729,408 bytes.
- Lowest sampled free RAM: 23.54%; lowest sampled free VRAM: 18.36%.
  Both stayed above the 10% floor.
- Frontier calls: 0. Provider spend: `$0`. Held-out split accessed: `false`.
- The adapter remains inactive. No repository mutation by the model occurred.
- Transformers used reference PyTorch implementations for missing
  `causal_conv1d` and `flash-linear-attention` kernels. This is correct but
  slower; generation latency is specific to this environment.

The Iteration 207 run stopped and its bounded output was counted. Its storage
reservation can now be released. Keep the receipt, report, protocol, and
negative Iteration 206 evidence immutable.
