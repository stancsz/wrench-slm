# Phase 368: Ollama BF16 to NVFP4 experiment

Date: 2026-09-21

Status: `FAIL_OLLAMA_MLX_QUANTIZER_WINDOWS`

After upgrading Ollama from `0.32.13` to `0.34.2`, a controlled import was
attempted from the same Wrench 8E BF16 source at
`D:\models\Wrench-Qwen3.6-8expert-BF16` (7.37GB) with `-q nvfp4 --force`.
Ollama recognized the source and reached `1045 tensors, quantizing to nvfp4`,
but failed on `lm_head.weight` because the MLX dynamic library is unavailable
on Windows.

This rules out a simple current-NVFP4 metadata-only explanation for stock
Ollama on this host. The source package and existing Ollama models were not
modified. The bundled Wrench runtime remains the only verified Windows path.
