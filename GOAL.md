# Goal: Wrench productive value

Status: active
Updated: 2026-09-22
Owner: repository agent, under human product authority

## Product outcome

Deliver a trustworthy, bounded Wrench worker that creates measurable value on
routine developer-tool work. The active goal is productive workflow value,
not broad model research, hardware portability, or feature completeness.

Wrench handles fast, repetitive, verifiable mechanical work. It proposes
structured read-only or review-only actions, or abstains. An independent
verifier and the stronger-model fallback retain final authority. Wrench never
executes arbitrary shell commands, accesses credentials, or writes
autonomously.

## North Star

The North Star is one paired real-workflow canary:

1. run the same authorized workload through the stronger-model baseline;
2. run it through the Wrench hybrid path with the same fallback, verifier,
   retry, and correction policy;
3. reconcile final success, safety, latency, frontier tokens, local tokens,
   cost, retries, corrections, abstentions, and fallback overhead.

The canary must show no material final-success or safety regression, zero
prohibited accepts, zero unexpected mutations, meaningful end-to-end latency
improvement on successful eligible tasks, and at least 95% net frontier-token
savings after compaction, verification, retries, corrections, and fallback.

Synthetic replay, an HTTP success, a client smoke, a smaller checkpoint, or a
lower teacher-call count is not North Star evidence by itself.

## Keep and continue

These are the only active workstreams:

1. **Deterministic mechanical worker**

   Fast, bounded handling of routine developer-tool work.
2. **Independent verifier and no-mutation boundary**

   Every proposal remains schema-checked, permission-checked, and fail-closed.
3. **Hybrid long-context intake and retrieval**

   Accept large raw context, retrieve the relevant evidence, and compact model
   work into a bounded working context.
4. **Two-state client protocol**

   Use a bounded proposal followed by a hash-bound final answer after a
   verified read-only result. No repeated or unbounded tool loop.
5. **OpenCode, DeepSeek Harness, and Claude Code support**

   Keep these three bounded client surfaces working. Do not add more clients
   without demonstrated user demand.
6. **Latency and timeout repair**

   Remove avoidable timeout and queueing outliers from the successful path.
7. **One paired real-workflow canary**

   Measure actual productive value against the stronger-model baseline.
8. **Targeted fallback expansion**

   Add only deterministic, verifier-friendly handlers justified by real
   fallback volume after the canary.
9. **Sustained operational testing**

   Exercise concurrency, cancellation, timeouts, recovery, circuit breaking,
   accounting, and no-mutation behavior over sustained local operation.

## Explicitly skipped

The following are archived or paused and must not become active work without a
new human product decision:

- RTX 5060 Ti verification;
- private release packaging as a separate workstream;
- learned free-form routing and LoRA optimization;
- dense-native 4M attention;
- stock Ollama, vLLM, and GGUF adapter work;
- additional synthetic replay work as a primary milestone;
- broad speculative tool expansion;
- public production release before the North Star canary and operational
  evidence pass.

## Active product boundary

The active serving path is model-local hybrid execution:

1. accept the raw request at the Wrench endpoint;
2. use deterministic retrieval, search, AST or dependency extraction where
   applicable;
3. preserve current intent and hash-bound evidence;
4. compact model work to a bounded working context;
5. emit a typed proposal or abstention;
6. independently verify it;
7. execute only bounded read-only or review-only work;
8. return a hash-bound final answer or the original request to the stronger
   fallback.

The large-context intake is a hybrid retrieval capability. It is not a claim
of dense-native 2M or 4M decoder quality.

## Active acceptance gates

- **Mechanical correctness:** eligible proposals match typed oracles, and
  out-of-boundary requests abstain with the correct reason.
- **Safety:** zero prohibited accepts and zero unexpected mutations.
- **Client protocol:** OpenCode, DeepSeek Harness, and Claude Code complete a
  bounded proposal and final-answer flow without free-form execution or loops.
- **Matched value:** the paired canary reconciles correctness, safety,
  latency, frontier tokens, local overhead, cost, retries, corrections, and
  fallback.
- **Operations:** sustained tests show no silent loss, state leakage,
  unbounded retry, orphaned worker, fallback loss, or failed cancellation
  recovery.
- **Targeted expansion:** new handlers are admitted only when real traces show
  material fallback value and an independent verifier can bound them.

Missing evidence is inconclusive, not a pass. Final acceptance, promotion,
publication, deployment, and spending remain human decisions.

## Source of truth

- [GOAL.md](GOAL.md) is the active product goal and North Star.
- [COLLABORATION_CONTRACT.json](COLLABORATION_CONTRACT.json) is the active
  machine-readable Q4 authority contract.
- [WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md](docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md)
  is the active productive-value evidence contract.
- [WRENCH_LONG_CONTEXT_SERVING_CONTRACT.md](docs/WRENCH_LONG_CONTEXT_SERVING_CONTRACT.md)
  records the active hybrid serving boundary.
- [AGENTS.md](AGENTS.md) and [AGENTS.local.md](AGENTS.local.md) provide
  repository and host safety rules.
- [docs/evidence/GOAL_HISTORY_2026-09-22.md](docs/evidence/GOAL_HISTORY_2026-09-22.md)
  and [docs/archive/2026-09-22/](docs/archive/2026-09-22/) preserve superseded
  plans and historical evidence. They are not active instructions.

## Current status

The deterministic worker, independent verifier, hybrid intake, bounded
two-state client protocol, and three named client surfaces have current local
evidence. Local operational tests also exist. The remaining active proof is
the paired real-workflow canary, latency and timeout repair, targeted fallback
selection, and sustained operational testing.

Learned routing remains disabled. The project is active and evidence-gated,
not approved for production enablement.

## Q4 collaboration contract

This goal is `CHALLENGE` because productive value, safety, release scope, and
workflow comparison combine high consequence risk with uncertainty and
reasonable expert disagreement. Human initiative, acceptance, and commit
authority remain explicit.

| Task class | Mode | Boundary |
| --- | --- | --- |
| Read-only inspection, documentation edits, deterministic local tests, and reversible evidence indexing | `AUTO` | Repository-only, with diff and test verification |
| Sustained local operational testing and bounded real-client canary preparation | `GUARD` | Stop before external effect, spending, or promotion |
| Product wording, tradeoffs, and interpretation of canary value | `COCREATE` | Human acceptance and final commit |
| Workflow comparison, fallback expansion, routing, and architecture changes | `CHALLENGE` | Human decision with AI evidence, alternatives, and dissent |
| Production enablement, deployment, publication, credential approval, or unverified safety judgment | `HUMAN_ONLY` | Human performs or explicitly takes over |

Human owns product intent, scope, acceptance, promotion, publication,
deployment, provider spending, and release decisions. The agent may inspect,
implement, test, and collect evidence only inside the repository and approved
redacted inputs. Human timeout means stop and preserve state.

Every consequential experiment records source, artifact, runtime, verifier,
prompt, workload, resource, accounting, failure, and rollback identity. Any
verifier failure, scope expansion, permission expansion, budget overrun,
security or privacy concern, unbounded retry, or unresolved disagreement
escalates to the human.
