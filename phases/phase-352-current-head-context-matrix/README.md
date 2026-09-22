# Phase 352: current package context matrix

Date: 2026-09-22

The exact package at `D:\models\_wrench-release-candidate-8d9ea2c` was tested
through its own model-local OpenAI-compatible endpoint at five logical input
sizes. Every request carried a real raw payload, passed the no-truncation
token-count gate, bound a SHA-256 payload hash, and completed with zero model
calls:

| Raw target | Measured raw tokens | Total ms | First-layer gate ms | Effective tokens |
| ---: | ---: | ---: | ---: | ---: |
| 64,000 | 63,994 | 26.718 | 2.060 | 9 |
| 128,000 | 127,993 | 34.716 | 2.456 | 9 |
| 256,000 | 255,993 | 31.736 | 3.015 | 9 |
| 2,000,000 | 1,999,998 | 92.177 | 12.681 | 9 |
| 4,000,000 | 3,999,995 | 173.287 | 24.041 | 9 |

The 4M logical input was approximately 32 MB of payload text and remained
inside the package's declared 4M limit. This is direct model-local hybrid
intake plus deterministic first-layer reduction. It is not dense native
attention over every raw token, learned MiniMax parity, independent RTX 5060
Ti evidence, or production approval.

Individual hash-bound receipts are the JSON files in this directory.
