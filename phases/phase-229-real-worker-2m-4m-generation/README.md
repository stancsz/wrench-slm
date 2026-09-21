# Phase 229: real worker 2M and 4M generation

The repository probe `tools/probe_real_worker_long_context.py` was run against
the fused development-only rank-8 LoRA checkpoint with the mechanical
shortcut disabled. Each request entered the Wrench worker as a monster raw
message, went through the integrated first-layer reducer, and then generated
through the real Transformers model on CUDA.

| raw target | worker raw estimate | staged model tokens | gate | total | exact |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 2,000,000 | 1,996,091 | 1,987 | 46.527 ms | 5,402.649 ms | yes |
| 4,000,000 | 3,996,303 | 1,987 | 135.008 ms | 5,389.513 ms | yes |

Both runs used one model call on `cuda:0`, returned the expected bounded
`read_file` proposal, stayed below the hard 4,000,000-token admission boundary,
and emitted raw and prepared payload hashes. The working-context budget was
64,000 tokens, although this particular exact lookup reduced to 1,987 tokens.

This is the strongest current evidence that Wrench can directly receive 2M to
4M raw input at its own worker path and still do useful work quickly without
dense attention over the stale payload. It does not prove dense-native 4M
attention, broad family-disjoint quality, MiniMax parity, or production
readiness. The checkpoint remains a temporary development artifact.
