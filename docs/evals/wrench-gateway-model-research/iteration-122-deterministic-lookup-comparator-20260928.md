# Iteration 122: deterministic lookup comparator

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-DETERMINISTIC-LOOKUP-COMP-ITER122`  
Status: **3/3 predeclared synthetic lookups passed with bounded TOML/AST parsing; no model or provider used**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Result

This comparator handles the same three authored fixture questions as Iteration
121 using Python's standard-library TOML parser and AST parser. It produced the
three exact expected answers, surfaced all required evidence lines, and used
zero language-model/provider calls. It parsed 1,203 source bytes from the
already-loaded in-memory fixture and took 0.0018809 seconds for the three
parser calls combined. The measured time excludes Python startup, fixture
module import, process scheduling, and any external state or recovery work.

| Case | Exact answer | Evidence | Parse time |
|---|---|---|---:|
| Retry policy | `3,250` | retry status, limit, and initial backoff | 0.0006558 s |
| Session lifetime | `1800,300` | timeout and refresh lead time | 0.0005025 s |
| Retry function | `calculate_retry_delay` | exact function signature and return expression | 0.0007226 s |
| **Total** | **3/3 passed** | **all required evidence visible** | **0.0018809 s** |

The paired local-model comparator is the Iteration 121 Qwen3.5-0.8B base-model
arm at context budget 64: 3/3 passed, with 1,392 local input and 25 local
output tokens. This deterministic arm used zero model tokens by design. Those
figures show that these three narrowly structured mechanical lookups do not
need an SLM when the data is available in the expected TOML/Python formats.
They are not an apples-to-apples end-to-end runtime comparison: Iteration 121
includes Wrench E0 preparation and model loading; this parser timing excludes
startup and performs direct reads from an in-memory fixture. Zero model tokens
here do not establish frontier tokens saved, task-success retention, or all-in
cost savings.

## Identity and limits

- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Comparator SHA-256:
  `421f087e01e2ca8838c2271320845ea9ef28fdae84fbb97d0eb21c16f2ff3d5e`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\deterministic-lookup-iter122.json`,
  2,500 bytes, SHA-256
  `19e1b421c4d0e0952e3bb06d0549f2d067eadc91ccc6f6d3a8b2ba606adcf998`.
- Runtime: Python 3.13.15, standard-library `tomllib` and `ast`; no GPU
  inference, download, network access, adapter, or provider spend.
- Storage admission reserved 20,000,000 bytes, included the Docker WSL model
  volume and hourly automation directory, and remained within the 50 GB
  aggregate limit. C: had more than 140 GB free.

This proves a tiny fixed mechanical slice only. It says nothing about choosing
the right tool for unseen inputs, editing code, tests, debugging, interruption
recovery, or working all day. Keep the broader model/controller research and
all 95/5 product gates open. The next engineering step is to put deterministic
prechecks in the same frozen harness, then test where they fail closed and
whether the local model adds verified value on nontrivial decisions.
