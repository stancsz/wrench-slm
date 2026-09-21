# Phase 216: v88 direct model-local context matrix

Date: 2026-09-20

The package-local endpoint was measured at the five context points required by
the active contract. Each point ran three fresh package-server repetitions.
The probe now reserves the current-intent suffix and checks the bounded token
estimate before sending, so the 4M point stays at or below the declared
4,000,000-token logical limit.

| requested point | observed raw tokens | p50 HTTP ms | empirical p95 HTTP ms | gate p50 ms | staged tokens |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64K | 63,994 | 25.545 | 26.104 | 2.020 | 9 |
| 128K | 127,993 | 27.116 | 28.313 | 2.220 | 9 |
| 256K | 255,993 | 30.321 | 30.683 | 2.977 | 9 |
| 2M | 1,999,998 | 103.465 | 106.465 | 12.354 | 9 |
| 4M | 3,999,995 | 158.906 | 159.251 | 23.952 | 9 |

All 15 probes returned `PASS_MODEL_LOCAL_SERVER_4M`, an accepted bounded
`read_file` proposal, `embedded-mechanical`, and zero model calls. The raw
payload is received directly by the package-local endpoint. This is hybrid
MapReduce/mechanical intake evidence, not dense native attention quality.

The 2M and 4M measurements are above the earlier 100 ms aspiration at the
complete HTTP boundary, while the first-layer gate itself remains under 25 ms
at 4M. The current evidence supports fast practical intake and bounded model
work, not a claim of sub-100 ms 4M end-to-end latency.

Probe receipts are in this directory. The probe correction is in
`tools/probe_model_local_server.py`.
