# Iteration 207 package review

Review job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER207-REVIEW-20260929-01`  
Nonce: `80d8a608-82bf-4544-bc70-a4f548d86c6f`  
Verdict: **PASS for static package admission; fresh run admission remains separate.**

## Identity

HEAD before/after: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256 before/after: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`  
Runner SHA-256 before/after: `8deb4c80a1394c9b83616165101013c21d7a3e4e6a284a3676d37698d8e96144`  
Protocol SHA-256 before/after: `16ccef663c320a3e69e5d9f16216a1316d91487285da5275791b2f2ce8dd5676`  
Trainer SHA-256 before/after: `1d7ccbb42af72c41066d52a4cb6448d000c07d395657cae475daaa79363b49b5`

## Findings

- Runner uses `AutoModelForImageTextToText`, matching the screen-03 trainer's base loader, with the same pinned model directory, BF16, offline/local-only loading. It attaches the frozen adapter with `PeftModel.from_pretrained(..., is_trainable=False)` and never activates or mutates it.
- Before generation, it rejects recognized PEFT adapter-key warnings and opens the pinned safetensors on CPU. For every saved key it derives the module path and LoRA A/B parameter, requires the attached parameter to exist, and checks shape plus `torch.equal` against the saved tensor; it requires exactly 64 checked tensors and records count/key hash. Any key-path or equality failure aborts before generation and is routed to a failure receipt. This is a fail-closed static mapping review; the actual attached module paths and tensor equality were not runtime-verified here.
- Raw decoded answers are preserved. The declared normalization trims only surrounding ASCII space, tab, CR, and LF, then compares exactly with expected text, matching the protocol's correction for the prior trailing newline.
- Iteration 207 has a distinct job ID, nonce, and output path. Existing output is refused; receipt creation uses an exclusive temporary file followed by a no-clobber hard link. The three reused development cases are explicitly not held out. Pair completeness gates token ratios. Provider/network claims are bounded to local-only model flags and Python socket-connect blocking, explicitly not OS isolation. No held-out read, activation, provider call, or training is in the runner.
- Resource checks enforce 10% free RAM/VRAM before model loading and use the helper resource sampler/stopping criteria through generation. Protocol still requires fresh storage, disk-space, process, and resource admission before any run; this review does not establish those run-time conditions.

No material static blocker found for a later separately admitted run.

## Scope and evidence

Static review only. Commands used: `git rev-parse HEAD`; `Get-FileHash -LiteralPath` for the runner, protocol, active goal, and trainer; scoped `rg -n -C` and `Get-Content -LiteralPath` reads of the runner, protocol, trainer, and named Iteration 206 report; `Get-CimInstance Win32_OperatingSystem`; and `nvidia-smi --query-gpu=name,memory.free,memory.total --format=csv,noheader`. No tests, Python execution, runtime/model loading, inference, network/provider/SubRoute access, credentials, held-out payload, or training.

Resource samples: before review, RAM free `10,268,176,384 / 34,290,302,976` bytes (29.94%); VRAM free `15,227 / 16,311` MiB (93.35%). After review, RAM free `10,256,199,680 / 34,290,302,976` bytes (29.91%); VRAM free `15,226 / 16,311` MiB (93.34%). Both stayed above 10%.

Only this requested review report was written; the assigned source/protocol/goal/trainer hashes were unchanged.
