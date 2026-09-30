# Iteration 205 local run report

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER205-20260929-01`  
Nonce: `bd261641-cb41-48c1-bd3f-fdb6cc44e46f`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Result

**Blocked before model loading. No task cases ran.** The runner failed its
offline runtime imports with `ModuleNotFoundError`, wrote the bounded failure
receipt, and exited nonzero. It made zero Frontier calls and spent `$0`.
Frontier token and all-in cost savings are `null`; no local effectiveness or
token reduction result was produced.

Failure receipt: 753 bytes, SHA-256
`1E94106C4B431CC9852EB758F4BA1DE3F0A3EDC7FEFCF089E807038493A350C3`, at
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iteration-205-qwen35-4b-lora-context-pair.json`.
It records phase `preflight`, status `failed_before_or_during_run`, the expected
repository and goal identities, zero calls/spend, and no held-out access. The
runner currently suppresses the module name in its failure receipt; separate
read-only package discovery identified the selected Python 3.13.15 interpreter
as missing `torch`, `transformers`, and `peft`.

No compatible existing environment was found among the inspected candidates:

- Global Python 3.13.15: all three packages absent.
- Repository `.venv`: Python 3.11.16; all three packages absent.
- FreeToken environment: Python 3.12.14 with Torch `2.11.0+cu130`, Transformers
  `5.16.1`, and no PEFT. It fails the pinned Python/package identity and was
  not used.

The local host remained above the 10% resource floors after the failure: RAM
available was 10,257,113,088 / 34,290,302,976 bytes (29.9%); VRAM was
15,213 / 16,311 MiB free. The run's existing 100,000,000-byte storage
reservation remained active at report time. Storage status included the
approved data root, repository/worktrees, hourly automation directory, and
Docker model volume and was `WITHIN_LIMIT` at 29,509,818,447 actual bytes plus
136,103,000 reserved bytes. No model files or adapter files were changed.

## Identity and review

- Runner SHA-256:
  `0C51975A827A2C68E57A5E521133DA1782407AD0DC10EB27FF034942EC770B0E`
- Protocol SHA-256:
  `3B81C4C5C7EB508EA2C2CC2E45DD977C293781AAFCC742F9D38D2D90407BE0F0`
- Static package review 3 passed after confirming GPU identity is checked
  before snapshot hashing and model loading. Earlier review findings were
  fixed: strict output equality, complete-pair ratio gating, runtime identity
  gates/fields, early failure receipts, and atomic no-clobber output creation.
- The failure receipt confirms local-only execution boundaries, but this
  failed attempt is not evidence that the boundary was probed during inference.

## Next decision

Prepare a separate pinned Python 3.13 environment under the approved Wrench
data root. Before any package download or install, inventory the exact Windows
wheel and dependency sizes, set cache paths inside the approved root, reserve
the bounded peak, and check C: free space. Then create a new one-shot experiment
identity and output path; Iteration 205 is sealed and must not be overwritten.
Do not weaken the runtime pins to reuse the unrelated Python 3.12 environment.

The official PyTorch 2.14 release and its `cu132` wheel index provide a
potential compatible Torch distribution, but this report does not establish
that the complete pinned Transformers/PEFT runtime installs or runs on this
host: [PyTorch 2.14 release](https://pytorch.org/blog/pytorch-2-14-release-blog/),
[official CUDA 13.2 wheel index](https://download.pytorch.org/whl/cu132/torch/).
