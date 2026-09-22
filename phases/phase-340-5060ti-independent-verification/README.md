# Phase 340: independent verification record

Captured on 2026-09-21 from source commit `55c0fb0165faa18c5d222e3ff4d7b8cc776a1f4d`.

## Status

| Check | Status | Evidence and boundary |
| --- | --- | --- |
| Requested RTX 5060 Ti identity | `FAIL_IDENTITY_MISMATCH` | Host is RTX 5070 Ti, so this phase is not independent 5060 Ti evidence. |
| Exact package present | `PASS` | `D:\models\_wrench-release-candidate-bbc680f`, manifest SHA-256 `27801ca54134e28e083d9b9571f902d2fe74852c8551908b3e335fb5467b4641`. |
| Package validation | `PASS_STRUCTURAL_PACKAGE` | `package-validation.json`, no errors, two safetensors shards, config position limit 4,000,000. Structural only. |
| Exact 2M/4M retrieval probe | `PASS_PACKAGE_RETRIEVAL_2M_4M` | Fresh run, 6/6 beginning/middle/end cases, exact proposals, zero model calls, hash-bound first-layer receipts. This is deterministic embedded retrieval evidence, not dense-native quality. |
| Full 220-case diagnostic replay | `PASS_MECHANICAL_WORKER` | 220/220 rows. Weighted eligible success `1.0`, verifier success `1.0`, coverage `1.0`, net frontier-token savings `1.0`, Wrench plus fallback frontier tokens `310`, local tokens `24045`, p50/p95 `218.578 / 350.519 ms`, prohibited accepts `0`, unexpected mutations `0`. |
| Sealed 44-row diagnostic slice | `PASS_MECHANICAL_WORKER` | 44/44 rows. Weighted success `1.0`, verifier success `1.0`, coverage `1.0`, net savings `1.0`, frontier tokens `0`, local tokens `4805`, p50/p95 `197.635 / 309.755 ms`, prohibited accepts `0`, unexpected mutations `0`. The fixture is pending human approval and remains diagnostic. |
| OpenCode and DeepSeek Harness smokes | `PASS` | Both exit `0`, structured reads observed, 3 trace rows, zero model calls, no mutation claim. Raw client stdout sizes: 445 and 46 bytes. |
| Claude Code smoke | `PASS` | Exit `0`, 2 structured Anthropic trace rows, zero model calls, raw input sizes 2077 and 2091 chars, no mutation executed. One unrecognized model warning was emitted. |
| Native backend load/generation smoke | `PASS_LOAD_GENERATION_ONLY` | FreeToken ModelOpt NVFP4 backend loaded weights and generated an HTTP 200 response. 4M capacity configured, but direct raw-context verification failed and dense-native quality is not established. GPU free fraction stayed above 10 percent. |
| Production approval | `NOT RUN` | These receipts do not authorize production enablement, learned routing, dense-native quality, or MiniMax parity. |

## Commands

```powershell
python -X utf8 tools/validate_wrench_package.py --model-dir D:\models\_wrench-release-candidate-bbc680f --output phases\phase-340-5060ti-independent-verification\package-validation.json
python -X utf8 tools/probe_package_retrieval_quality.py --package-dir D:\models\_wrench-release-candidate-bbc680f --output phases\phase-340-5060ti-independent-verification\retrieval-2m-4m.json
python -X utf8 tools/run_package_220_replay.py --package-dir D:\models\_wrench-release-candidate-bbc680f --cases evals\wrench-expanded-v2\cases.jsonl --teacher-traces phases\phase-296-remote-current-220-replay-input\teacher-current-220.json --root C:\Users\stanc\.codex\worktrees\3e63\wrench-slm --output-dir phases\phase-340-5060ti-independent-verification\replay-220 --health-fixture --port 28911 --allow-historical-suite
python -X utf8 tools/run_package_220_replay.py --package-dir D:\models\_wrench-release-candidate-bbc680f --cases evals\wrench-expanded-v2\final.jsonl --teacher-traces phases\phase-296-remote-current-220-replay-input\teacher-current-220.json --root C:\Users\stanc\.codex\worktrees\3e63\wrench-slm --output-dir phases\phase-340-5060ti-independent-verification\replay-final --health-fixture --port 28912 --allow-noncanonical-count --allow-historical-suite
.\tools\smoke_portable_clients.ps1 -PackageDir D:\models\_wrench-release-candidate-bbc680f -OutputDir phases\phase-340-5060ti-independent-verification\clients\opencode-dsh -Port 28913
D:\models\_wrench-release-candidate-bbc680f\run_claude_code.ps1 -Port 28914 -ProxyPort 28915 -AllowedRoot phases\phase-340-5060ti-independent-verification\clients\claude-workspace -Prompt "Read README.md and report its first heading." -Print -TraceLog phases\phase-340-5060ti-independent-verification\clients\claude.trace.jsonl
python -X utf8 D:\models\_wrench-release-candidate-bbc680f\verify_freetoken_backend.py --model-dir D:\models\_wrench-release-candidate-bbc680f --freetoken-executable C:\Users\stanc\AppData\Local\FreeToken\venv\Scripts\ft.exe --output phases\phase-340-5060ti-independent-verification\native-backend-smoke.json --port 28916 --startup-timeout-seconds 90 --probe-payload-tokens 1024 --probe-timeout-seconds 90
```

## Resource and evidence boundaries

The preflight host snapshot had 51,370,344,448 bytes RAM with 27,580,395,520 bytes free, and 15,236 MiB free VRAM on the RTX 5070 Ti. During native load, the receipt recorded 23,844,937,728 bytes free RAM and 8,213 MiB free VRAM, both above the 10 percent reserve. After stop, 23,849,955,328 bytes RAM and 15,172 MiB VRAM were free. An existing FreeToken daemon was observed separately and was not terminated because it was not owned by this verification run.

The native receipt reports `full_weight_load_verified: true` and `native_generation_verified: true`, but `direct_raw_context_verified: false`, `dense_native_quality_verified: false`, and status `FAIL_FREETOKEN_NATIVE_BACKEND`. The generated text was repetitive. Treat it as bounded backend load and generation evidence only.

Primary artifact hashes are recorded by the files themselves and include:

- retrieval receipt: `b8d5457323fe18317eaea1282ca5041de272274efc8787b0e931f654d898825e`
- 220 evaluation: `f3af268aa15fdc40c6c7ce06b3f98c2d0505fbb0eb79c3ff5aaeaa4d9d5cdb5f`
- 220 trace manifest: `d19c9b8ffe0d67b347372bdca41d168bdc9470065a624d51f97f6796583936a5`
- final evaluation: `16eeb5f60686e00df15f37dea17f0739077e85b020cee1eacfa5d5bf6d0e4fe7`
- final trace manifest: `7be6c7499db28a7fe406fb86ad6c24418c602c402d4702a2798ce16e46b9e2e9`
- native smoke receipt: `2682f85d29c273c5398a6f33a9b27e15d00215f21212f9bdb25b66624a3de3ed`
