# Phase 354: family-disjoint MiniMax development pilot

Status: `PASS_DIAGNOSTIC_FAMILY_DISJOINT_DEVELOPMENT`, not release evidence

This pilot follows the Sol advisor decision to freeze the deterministic hybrid
as the product path and obtain stronger workflow evidence before another
learned-model iteration. It uses the reviewed suite's `development.jsonl`
split only. The suite manifest assigns development groups 6 and 7, separate
from calibration groups 0 through 5 and final groups 8 and 9. The suite is
still `DRAFT_PENDING_HUMAN_APPROVAL`, so this pilot is diagnostic and cannot
authorize release or learned routing.

## Frozen inputs

- Cases: `evals/wrench-expanded-v2/development.jsonl`
- Expected case hash from the suite manifest:
  `8070c2c7cb100b2c046763a9f374ae4f670a3e730e7c97b05ffeb340c869bc70`
- Wrench package: `D:\models\_wrench-release-candidate-8d9ea2c`
- Package runtime source commit: `8d9ea2c`
- Teacher endpoint: local MiniMax-compatible `http://127.0.0.1:4000/v1/chat/completions`
- Teacher request: model `minimax`, temperature `0`, streaming enabled,
  `max_tokens=768`, no proposal execution
- Wrench serving: package-local HTTP endpoint, client mechanical shortcut
  disabled, health fixture enabled for allowlisted health cases
- Safety boundary: independent verifier remains authoritative; no mutations
  or arbitrary shell execution are permitted

## Frozen measurements

The pilot records, per arm and per case: teacher frontier tokens, Wrench local
tokens, fallback and retry counts, model calls, verified acceptance, final
success, expected-outcome match, prohibited accepts, unexpected mutations,
latency, and raw receipt hashes. Retrieval evidence is recorded separately as
reference-card recall, evidence-window recall, current-intent preservation,
hash binding, raw token count, staged model-prefill tokens, and staging
latency.

Stop immediately and mark `FAIL_STOP` on any prohibited accept, unexpected
mutation, verifier bypass, case-hash mismatch, teacher/Wrench input mismatch,
or non-zero transport/runtime failure that invalidates paired comparison. Do
not claim 5060TI evidence unless the remote receipt attests the required host
identity and telemetry.

The package replay and raw teacher capture remain outside Git under
`D:\models\wrench-phase-354-family-disjoint-development-pilot`. This phase
directory will receive only the redacted summary and hash-bound receipt needed
for reproducibility.

## Runtime result

The 44 development rows completed with zero teacher transport failures. The
development split contains 24 eligible rows and 20 boundary or out-of-domain
rows. The paired package replay recorded:

| Arm | Weighted final success | Weighted verifier success | Frontier tokens | Local tokens | Fallbacks | Median / p95 ms | Prohibited accepts | Mutations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniMax teacher only | 0.900604 | 1.0 | 7,818 | 0 | 0 | 3,877.981 / 8,112.601 | 1 | 0 |
| Rules + identical fallback | 0.900604 | 1.0 | 7,736 | 0 | 20 | 0.605 / 34.474 | 1 | 0 |
| Wrench + identical fallback | 1.0 | 1.0 | 0 | 4,849 | 0 | 174.242 / 272.873 | 0 | 0 |
| Wrench only diagnostic | 1.0 | 1.0 | 0 | 4,849 | 0 | 174.242 / 272.873 | 0 | 0 |

The paired workflow gates all passed for this diagnostic slice: weighted
mechanical frontier-token coverage `1.0`, net frontier-token savings `1.0`,
teacher final-success non-inferiority `true`, zero Wrench prohibited accepts,
and zero mutations. The teacher arm's one prohibited accept is retained as an
input observation and is not hidden by the Wrench result.

The separate deterministic retrieval receipt recorded target-reference recall
`1.0`, evidence-window recall `1.0`, current-intent preservation `1.0`, and
hash-bound reference rate `1.0` across 44 cases with zero model calls. This is
retrieval and workflow evidence, not learned MiniMax parity or dense-native
attention quality.

External receipt hashes:

- teacher capture: `E3C23FCE30DA18B75E4B6E150F3CCA3AEF9D0068B619D7708BC67800115A5BC7`
- retrieval diagnostic: `0FC31DC7C76ABD5CC26AA412CA81CCC2DF9A3423889702E27E612D41E923E745`
- replay evaluation: `1B96A9D96A5E0C987CA277A662BD26E39603DC61E09E8F3861843A6F519C22A5`
- replay trace manifest: `BBBDBBD6924A3C9790804ACB3D5A677AA61B6D98778B9983D8310C464AA2560C`

This closes one meaningful family-disjoint development experiment. It does
not close human approval, the sealed final decision, current-head independent
5060TI verification, learned routing, or production release.
