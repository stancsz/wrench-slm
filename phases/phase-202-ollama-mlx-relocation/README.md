# Phase 202: Relocatable Ollama MLX runtime experiment

Date: 2026-09-20

## Result

`tools/patch_ollama_mlx_windows_runtime.py` created a copy of the Ollama
0.34.2 MLX runtime and replaced the two compiled-in CUDA and cuDNN directory
strings in the copied `mlx.dll` with `.`. The original runtime was not
modified. The patched server was started with its working directory set to
the bundled `mlx_cuda_v13` directory.

The patched runtime then completed real GPU inference for the imported v81
model. A short request loaded the model, processed 16 prompt tokens, and
generated 8 tokens in 11.569 seconds, including a 4.207 second model load.
A warmed request completed in 2.313 seconds for 20 prompt tokens and 16
generated tokens. The runner no longer panicked on the missing system cuDNN
directory. The visible generated text was malformed JSON-like token output,
so this is backend execution evidence, not a model-quality pass.

## Native 2M stress result

A direct Ollama `/api/generate` request used `options.num_ctx=2000000` and a
raw prompt that tokenized to 2,000,018 tokens. The request reached the MLX
runner directly and began prefill with no gateway truncation. It processed
26,624 tokens in 88 seconds before being canceled because the observed rate
would have made the complete prefill take more than an hour. GPU utilization
was 100 percent during the run. The request did not complete and is not a
2M quality or latency pass.

## Decision

This proves that the Wrench weights can execute through an Ollama-compatible
MLX runtime after relocation, but dense native attention over the full raw
sequence is not the fast product path. The hybrid model-local MapReduce,
retrieval, and bounded working-context route remains necessary for practical
2M/4M intake. The relocation tool is an experimental diagnostic and does not
turn stock Ollama into an officially supported portable Wrench runtime.
