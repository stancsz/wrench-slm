# Iteration 123: deterministic lookup fail-closed controls

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-DETERMINISTIC-GUARD-ITER123`  
Status: **3/3 exact positive lookups and 4/4 malformed/stale-input controls passed**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Result

Iteration 122 showed that three fixed synthetic TOML/Python lookups can be
answered without a model. This follow-up pins the fixture identity, uses
bounded TOML and AST parsing, rejects duplicate or malformed configuration,
and rejects duplicate or behaviorally changed Python symbols rather than
selecting the first match.

| Check | Expected behavior | Result |
|---|---|---|
| Retry policy, TOML fixture | Exact `3,250`, required lines visible | Pass |
| Session lifetime, TOML fixture | Exact `1800,300`, required lines visible | Pass |
| Retry function, Python AST | Exact `calculate_retry_delay`, signature and body evidence visible | Pass |
| Duplicate TOML key | Abstain/reject | Pass |
| Missing required TOML key | Abstain/reject | Pass |
| Duplicate Python function name | Abstain/reject | Pass |
| Modified fixture hash | Reject stale identity | Pass |

The positive path parsed 1,203 bytes from the already-loaded synthetic fixture
in 0.0021923 seconds total. It used zero model and provider calls. Compared
with Iteration 121's local-model arm (1,392 model input tokens and 25 output
tokens), this shows a mechanical lower-compute route for these three fixed
question shapes. It is not an end-to-end paired runtime comparison: parser
timing omits startup and snapshot/context preparation, and the fixture is
synthetic. Zero model tokens do not establish frontier tokens saved.

## Identity and admission

- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Runner SHA-256:
  `807797c0e13d643e0622ec0dc3420024527d00622eceb130b773c678c536a3ad`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\deterministic-guard-iter123.json`,
  3,101 bytes, SHA-256
  `8c8075a1153c40d985f1dd03703c08ad2475b674bb0daeb314fa93c7c924a3d5`.
- Runtime: Python 3.13.15, standard-library `tomllib` and `ast`; no model
  inference, GPU work, network, provider, or spend.
- At job start, RAM was 19.86% free. Storage admission reserved 20,000,000
  bytes, included the Docker WSL model volume and hourly automation directory,
  and remained below the 50 GB ceiling. C: had over 140 GB free. The job
  stopped, output was counted, and the reservation was released.

This is a fail-closed check for four authored mutations, not a broad parser or
engineering reliability guarantee. The fixed fixture and expected results are
synthetic; no code patch, test repair, interruption, recovery, multi-language
repository work, LoRA contribution, or eight-hour session was tested. Preserve
the broader goals and measure the next comparator on varied, frozen task
episodes with exact outcome evidence.
