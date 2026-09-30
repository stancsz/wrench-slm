# Iteration 206 runtime environment report

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-QWEN35-PY313-CU132-RUNTIME-ITER206-20260929-01`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Result

Created a dedicated runtime at
`C:\wrench-slm-data\envs\wrench-gateway-py313-cu132-iter206` after the
Iteration 205 attempt found the configured global Python 3.13 environment
missing `torch`, `transformers`, and `peft`. Installed 38 packages with `uv`
from the official PyTorch CUDA wheel and PyPI. No model weights or adapters
were downloaded, copied, or modified.

The exact required runtime imports successfully and discovers the pinned GPU:

- Python 3.13.15
- Torch `2.14.0+cu132`, CUDA runtime `13.2`
- Transformers `5.17.0`
- PEFT `0.21.0`
- `torch.cuda.is_available()`: `true`
- Device: `NVIDIA GeForce RTX 5060 Ti`
- `nvidia-smi` UUID checked separately by the reviewed runner:
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`

The CUDA check imported the runtime and queried the device only. It did not
load the model, generate tokens, access the provider, or open held-out data.
Thus Iteration 205 remains a failed one-shot attempt; it was not rerun or
rewritten. A fresh Iteration 206 identity and receipt are required for the
paired model inference.

## Storage and resource accounting

- The downloaded Torch CUDA wheel is 1,993,705,088 bytes (about 1.86 GiB), as
  reported by the official wheel fetch. The full installed environment tree is
  3,198,541,293 bytes.
- The package manifest is 734 bytes, SHA-256
  `46576C195C4A131D063D952C10175C5D54C0F4079CDFF54815BF50C9594D4687`, at
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iter206-python-runtime-packages.txt`.
- The job's 10,000,000,000-byte reservation covers wheel download, extraction,
  dependencies, environment, cache, and temporary growth. The final storage
  status including repository worktrees, automation directory, and Docker
  model volume was `WITHIN_LIMIT`: 32,708,364,163 actual bytes plus
  10,036,103,000 reserved, or 42,744,467,163 projected under the 50 GB limit.
- C: had 125,867,200,512 bytes free. Final resource sample: RAM
  9,955,110,912 / 34,290,302,976 bytes free (29.0%); VRAM
  15,229 / 16,311 MiB free (93.4%). Both exceed the 10% floor.

The exact package pins are in the package manifest. The Torch CUDA wheel is
from the official PyTorch `cu132` index; Transformers and PEFT were pinned to
`5.17.0` and `0.21.0` respectively. The official distribution index confirms
the CPython 3.13 Windows wheel is available and reports its downloaded size:
[PyTorch CUDA 13.2 wheel index](https://download.pytorch.org/whl/cu132/torch/).

## Next step

Prepare, statically review, and run a new one-shot Iteration 206 copy of the
paired 4B base/LoRA context screen using this isolated interpreter. Keep its
candidate inactive, its three cases labeled reused synthetic development
data, and its local tokenizer counts labeled as Frontier proxies only. The
95% completion, 5% Frontier-call, Frontier-token, all-in-cost, and sustained
engineering claims remain unproven.
