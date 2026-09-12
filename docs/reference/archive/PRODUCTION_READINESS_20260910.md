# Wrench-SLM: production readiness and scope audit

Updated: 2026-09-10

> **Current decision.** The V21 adapter weights are ready for release within
> the authored Wrench-Pro task scope. See [MODEL_RELEASE_PROGRESS.md](MODEL_RELEASE_PROGRESS.md)
> and [MODEL_RELEASE_HANDOFF.md](MODEL_RELEASE_HANDOFF.md) for the current
> evidence.

This file is the broader service and architecture audit. Its original negative
verdict is retained for the hosted router and production-service questions; it
must not be read as saying that the V21 weight package is untrained. The V21
package does not establish hosted uptime, router savings, high-concurrency
serving, arbitrary shell safety, or production traffic reliability.

> **Scope.** Architectural critique with the explicit goal of answering: *is Wrench-SLM ready for production? If not, what are the gaps?*
>
> **Verdict in one line.** **The weights pass their release gates; the hosted
> production system remains unapproved.** The infrastructure and safety
> questions below require separate live evidence.

---

## TL;DR

| # | Gap | Severity | Evidence the gap is real |
| --- | --- | --- | --- |
| 1 | Hosted production path is not validated with the V21 package | Critical | The V21 receipts prove local packaged inference only; they do not measure a live service |
| 2 | Latency numbers are synthetic constants | Critical | `wrench/canary.py`: local `8 + 1 ms`, cloud `1100 + len(prompt)//8 ms` |
| 3 | Safety is asserted, not measured against the mutation subset | High | `data/manifest.json` lists 522 mutation records, no replay against them |
| 4 | Production acceptance standard is documentation, not an executable gate | Medium-High | `docs/reference/PRODUCTION_ACCEPTANCE_STANDARD.md` lists six anti-patterns; only the canary measures one |
| 5 | Mechanical-share justification comes from the sibling system, not Wrench's own logs | Medium | Cited 74.8–81.2% from `lean-router/logs/`; no Wrench-side re-derivation |

The five gaps together explain why the answer is *not yet*. None of them is exotic; all of them have a clear closing action.

---

## Gap 1: hosted path has not been validated with the released adapter

### What is missing

The V21 adapter now has a complete local release package and passes its frozen
and independent authored evaluations. The older `data/m3_baseline.json` result
is historical evidence for an earlier production-shaped path, not the V21
weight decision. A live service has not yet been run with the released adapter.

The architecture of Wrench-SLM is:
- A small transformer (Wrench-Pro 0.5B) that produces canonical JSON tool calls
- A 19-state FSM (`wrench/fsm.py`) that masks logits so only legal JSON survives
- A deterministic regex policy as the safety floor
- A reward stack with four components (`wrench/reward.py`)

The remaining question is integration: how the released adapter behaves behind
the router, provider boundary, and live safety controls. The local package
receipts do not answer that question.

### Why this blocks production

Production Wrench-SLM is intended to learn from a broader traffic distribution,
not only authored fixtures. The V21 result clears the weight-release protocol,
but a service claim still needs live traffic, safety, and integration evidence.

### What closing it looks like

1. Integrate the immutable V21 package behind the intended router in a staging
   environment.
2. Define a production-shaped, privacy-reviewed holdout and run the same raw,
   semantic, safety, and outcome gates without changing the V21 package.
3. Measure live latency, concurrency, memory, mutation rejection, and fallback
   behavior on the advertised deployment target.

---

## Gap 2: latency is a simulation, not a measurement

### What is missing

`wrench/canary.py` injects synthetic latency constants:
- Local: `8.0 + 1.0 ms`
- Cloud: `1100 + len(prompt)//8 ms`

The "9 ms vs 1,172 ms" headline number is therefore a ratio of two synthetic numbers, not a measurement. The site (`docs/status.html`) already labels this as a simulation; the in-repo docs and any external post must do the same.

### Why this blocks production

A 130× speedup claim is a competitive lever. If the production environment uses a different harness, an actual GPU, or non-trivial batch sizes, the real number could be 5×, 50×, or 500×. Publishing 130× without measurement is one benchmark rewrite away from being wrong, and production claims must not be benchmark-rewrite-fragile.

### What closing it looks like

1. Replace the synthetic constants in `wrench/canary.py` with a real timing pass.
2. Run 1,000 prompts × 5 trials on the actual target hardware:
   - **Wrench-Flash**: Raspberry Pi 4 / Pi 5, CPU-only, p50/p95/p99 latency.
   - **Wrench-Pro**: RTX 5070 Ti 16 GB GDDR7, single-GPU, p50/p95/p99 at 1 / 5 / 10 concurrent requests.
3. Record wall time, GPU utilization, memory headroom, and measured cloud-token savings from the cloud provider's actual response logs.
4. Pin the latency claim to the published SKU, OS, kernel, batch size, and concurrency level. Any change in those inputs re-runs the measurement.

---

## Gap 3: safety is asserted, not measured

### What is missing

The canonical protocol in `wrench/protocol.py` is strict JSON with required-key validation. The FSM mask in `wrench/fsm.py` rejects illegal output at the logits level. The regex policy uses a `command_substring` prefilter and never matches mutation-prefixed commands. These are *design* properties. `data/manifest.json` lists 522 `mutation`-categorized records in the production-shaped corpus, but no replay has been run to assert that the architecture never executes them locally.

### Why this blocks production

A security claim that says "by design, mutations never run locally" is weaker than "we ran the held-out mutation subset and got `executed_locally == 0` on 522 prompts." The first is a story; the second is evidence. Production deployment requires evidence, especially when the system is intended to sit beside an agent stack and intercept tool calls.

There is also a subtler problem: the boundary between "read-only diagnostic" and "mutation" is fuzzier in the wild than in the dataset. Edge cases like `git reset --soft`, `mv`, `cp -f`, `> file`, or `Set-Item -Force` can sit on the edge of the categorization. The architecture handles the *obvious* mutations; it has not been tested on the *edge* mutations.

### What closing it looks like

1. Held-out mutation replay: run the architecture against the 522 `mutation` records, assert `executed_locally == 0` on every one.
2. Adversarial regression suite:
   - Shell injection: `"; rm -rf /"`, `$(...)`, backticks, multi-line commands.
   - Path traversal: `../../../etc/passwd`, `~`, env-var expansion.
   - JSON escape edge cases: nested quotes, unicode in paths, control characters.
   - PowerShell quoting: `&{...}`, `$()`, `iex`, encoded-command, here-strings.
   - Sub-shell and pipe chains that look read-only but trigger writes via aliases.
3. Wire the mutation replay into CI. Any future policy or grammar change is automatically tested against the mutation corpus.
4. Publish the failure cases. "Zero failures on 522 prompts" is the right number to publish, but it must be *paired* with the methodology so reviewers can re-derive it.

---

## Gap 4: production acceptance standard is documentation, not an executable gate

### What is missing

`docs/reference/PRODUCTION_ACCEPTANCE_STANDARD.md` already names six production anti-patterns:
1. **Warm-cache**: measuring with pre-warmed shell or KV cache and reporting it as cold-start latency.
2. **Empty-loop**: running 0-message / no-tool loops to claim token savings.
3. **Micro-benchmark**: running on a single prompt to claim p99.
4. **Concurrency denial**: running at 1 QPS to claim low resource use.
5. **Memory under-report**: citing model size without KV-cache or runtime overhead.
6. **Vendor baseline**: comparing against an unrealistically weak cloud.

These are correct. But they are a guide for humans reading the README, not an executable gate.

### Why this blocks production

The natural failure mode for AI infrastructure projects is not "we forgot a check," it is "we kept telling ourselves a number that is true on one setup and quietly drifted on the next." An executable gate is the difference between an architectural principle and a deployment invariant.

### What closing it looks like

1. Implement each anti-pattern as a check in `scripts/`:
   - **Warm-cache detector**: require the first request of every trial to be unmeasured.
   - **Empty-loop guard**: assert that `≥ 1` tool call per agent run was attempted during the measurement.
   - **Micro-benchmark guard**: require the trial set to be ≥ 1,000 unique prompts.
   - **Concurrency floor**: require at least one trial at 5 / 10 / 20 concurrent requests.
   - **Memory under-report**: report peak RSS, peak VRAM, and KV-cache footprint, not just parameter count.
   - **Vendor baseline**: require the comparison cloud to be the same prompt set and the same SLA tier.
2. Make `scripts/verify_milestones.py` *fail* when any check fails. No milestone flips to PASS without a fresh receipt from the executable gate.
3. Tag every receipt with the hardware SKU, OS, kernel, batch size, and concurrency level. Future drift becomes obvious.

---

## Gap 5: mechanical-share justification comes from the sibling system, not from Wrench's own logs

### What is missing

The structural reason the project exists is the *mechanical share* of tool calls:
the percentage of prompts that are routine enough to handle locally.
`docs/reference/SPECIFICATION.md` cites 74.8 to 81.2%, measured from `lean-router/logs/`.

That number is the *justification*, but it is a measurement of a different system. Wrench's own logs do not yet exist as a separate stream, because the sidecar daemon (`wrench/sidecar.py`) has not been run against live traffic. As long as the justification lives in the parent's logs and not in Wrench's own, the architecture is borrowing evidence from another repo.

### Why this blocks production

A production rollout needs to know what fraction of *real Wrench traffic* is mechanical, because that fraction drives the cost model. If the parent's traffic is 75% mechanical but Wrench's traffic is 40% mechanical (because Wrench is wired into a different routing layer or a different agent), the token-savings projection is half of what the spec assumes.

### What closing it looks like

1. Run the sidecar live against `lean-router/logs/tool_calls.log` for ≥ 24 hours of representative traffic.
2. Re-compute the mechanical share from Wrench's own observation, not the parent's.
3. Compare the two distributions. If they diverge, the architecture needs to handle the cases Wrench sees but the parent does not.
4. Update the production cost model with the Wrench-side number. Cite both numbers side by side in the README and on `docs/`.

---

## Strengths That Must Not Be Lost

The audit is critical, but the architecture has real strengths worth preserving through the production journey.

| Strength | Why it matters |
| --- | --- |
| Canonical JSON protocol | Every required key is checked by `parse_call`; only `ROUTER_FALLBACK` is the safe answer on doubt. This is the right invariant for a system that sits beside a frontier model. |
| FSM-constrained decoding | The 19-state FSM and `GrammarLogitsProcessor` give a structural guardrail on top of the trained model's logits. Even an undertrained checkpoint cannot emit illegal JSON through this mask. |
| Deterministic regex policy as the floor | The regex policy in `wrench/policy.py` provides a safety net: when the model is uncertain, the regex still works on the easy slice. This is the right shape for a research-grade system. |
| Four-component deterministic reward | `wrench/reward.py` gives GRPO a stable, auditable signal. The four components (schema_valid, ast_exec, param_match, escalation) cover the four failure modes that matter. |
| Held-out isolation from day one | The 13,218 / 2,851 / 2,688 split with held-out quarantine is the right starting point. The training / eval separation must be preserved. |
| Production acceptance standard as a doc | Even before it is executable, naming the six anti-patterns makes them impossible to forget. The doc-to-script conversion is mostly mechanical. |

---

## Sequencing the Production Push

A pragmatic ordering, assuming the team is small and the GPU budget is real:

1. **Week 1–2.** Train Wrench-Pro 0.5B on the existing production-shaped split. Re-run M3. If M3 is not yet PASS, iterate.
2. **Week 2–3.** Run the held-out mutation replay and the adversarial regression suite. Land the result in CI.
3. **Week 3.** Replace the synthetic latency constants with a real Pi 4/5 and RTX 5070 Ti timing pass. Publish the receipts.
4. **Week 4.** Implement the six anti-pattern checks as scripts. Make `verify_milestones.py` the production gate.
5. **Week 5.** Run the sidecar against live traffic for ≥ 24 hours. Re-derive the mechanical share from Wrench's own logs.
6. **Week 6.** Cut the first release tag. Every README claim is backed by a JSON receipt from the executable gate.

A rough token / dollar budget for steps 1–3 belongs in the README once it is known. Until it is known, do not put dollar figures in the public site.

---

## Production-Ready Checklist

The architecture is production-ready when **all** of the following are true, each backed by a JSON receipt from an executable script:

- [ ] M3 is `PASS` with ≥ 99.5% schema validity and ≥ 90% arg-exact on a re-derived baseline.
- [ ] Held-out 1,000-record evaluation reports a *trained-model* score, not the regex fallback.
- [ ] Mutation replay reports `executed_locally == 0` across the 522 mutation records.
- [ ] Adversarial regression suite reports zero high-severity failures.
- [ ] Real timing pass on Pi 4/5 and RTX 5070 Ti reports p50 / p95 / p99 with hardware SKU pinned.
- [ ] Six anti-pattern checks are implemented in `scripts/` and CI fails on any violation.
- [ ] Wrench-side mechanical share is measured from ≥ 24 hours of live sidecar traffic.
- [ ] Sidecar daemon has been observed mining live `tool_calls.log` and updating model weights at least once.
- [ ] Every public claim on `README.md`, `goal.md`, and `docs/` is traceable to a JSON receipt.

When all nine are checked, the architecture is production-ready. Until then, it is honest research-grade infrastructure.

---

## What This Audit Does Not Cover

- **Cost analysis.** Token savings projections depend on cloud-provider pricing, which has drifted twice in the past year. A dollar-figure audit belongs in a separate doc once trained-model latency and recall are known.
- **Competitive analysis.** A comparison to other local-tool-execution systems (vLLM, llama.cpp tool use, etc.) is out of scope. The architecture is critiqued on its own merits, not against the field.
- **Sister-repo claims.** The 74.8–81.2% mechanical-share number is cited but not re-derived. Re-deriving it requires reading `lean-router/logs/`, which is out of scope for this audit.
- **Hardware procurement.** The Pi 4/5 and RTX 5070 Ti targets are noted; availability and pricing are not in scope.

---

## Closing Note

The architecture is sound. The five gaps are concrete and addressable. The
strength of the project, including the strict protocol, FSM guardrails,
deterministic safety floor, isolated held-out splits, and documented production
acceptance standard, is also what makes the gaps closeable. None of them is a
fundamental design flaw. None requires throwing away the current code. Closing
the five gaps turns a research-grade prototype into a system with a defensible
production claim.
