# Wrench-SLM Audit

> **Scope.** A code- and receipt-level audit of Wrench-SLM at this checkout. It answers three questions:
> 1. What is Wrench-SLM, as implemented today?
> 2. How effective is it, and against what evidence?
> 3. What is the delta between what the repository claims and what it has actually proven?
>
> **Evidence boundary.** Audit figures are pulled from `data/milestone_receipts.json`,
> `data/verification_report.json`, `data/canary_summary.json`, `data/m3_baseline.json`,
> `data/manifest.json`, and direct reads of the policy / FSM / sidecar sources. Anything
> that is a *replay*, *shadow canary*, or *simulation* is labeled as such; nothing here
> is a claim about human adoption, production traffic, or a released checkpoint.

---

## 1. What Wrench-SLM is

Wrench-SLM is a **two-tier small-model family plus a deterministic policy + grammar runtime** whose purpose is to pre-execute the routine, read-only, low-stakes tool work that an agent stack otherwise has to push through a large frontier model.

The boundary it carves out, as recorded in `docs/reference/SPECIFICATION.md` and `docs/reference/PRODUCTION_ACCEPTANCE_STANDARD.md`:

- The frontier model owns planning, multi-step reasoning, mutations, and ambiguity.
- Wrench owns the mechanical layer: tool selection, parameter assembly, read-only execution, and short diagnostic calls.
- The contract between the two is the **canonical Wrench JSON tool-call protocol** in `wrench/protocol.py`. It is strict JSON, every required key is checked by `parse_call`, and the only fallback the gateway accepts is `ROUTER_FALLBACK`.

The full stack today is:

| Layer | File | Role | Maturity |
| --- | --- | --- | --- |
| Canonical protocol | `wrench/protocol.py` | `REQUIRED_KEYS`, `parse_call`, `ROUTER_FALLBACK` sentinel | Production-shaped, validated |
| FSM grammar | `wrench/fsm.py` | 19-state character-level JSON tool-call FSM | Tested, all states covered |
| Token-level grammar | `wrench/tokenizer_fsm.py` | Bridges FSM into token-stream masking | Implemented |
| Grammar logits processor | `wrench/fsm.py:GrammarLogitsProcessor` | Real-time logits masking | Wired in `sidecar.py:334` |
| Fallback policy | `wrench/policy.py` | Deterministic regex + AST policy (no model weights needed) | Working |
| Deterministic reward | `wrench/reward.py` | Four-component reward (`schema_valid`, `ast_exec`, `param_match`, `escalation`) | Working |
| Evaluation harness | `scripts/verify_execution.py` | Held-out sample execution over the production-shaped split | Working |
| Milestone verifier | `scripts/verify_milestones.py` | Produces `data/milestone_receipts.json` | Working |
| Canary runner | `wrench/canary.py` | Shadow canary with **synthetic** latency constants | Working as a simulation |
| Sidecar daemon | `wrench/sidecar.py` | Tails `lean-router/logs/tool_calls.log`, runs continuous training + serving | Implemented; needs live gateway traffic to mine |
| Native model | `wrench/model.py` | `NanoWrench` from-scratch transformer | Architecture present, training in progress |

The two product tiers are:

- **Wrench-Flash (≈135M params).** Tier 1, the always-on edge tier. Target hardware is Raspberry Pi 4 / Pi 5, CPU-only. Listed in `goal.md` as the ARM64, 4 GB/8 GB target.
- **Wrench-Pro (≈0.5B params).** Tier 2, the workstation accelerator. Target hardware is an RTX 5070 Ti 16 GB GDDR7. Architecture has been chosen but the trained checkpoint is **not released yet**.

The intent is layered: the deterministic regex policy is the safety floor; the FSM and grammar mask are the structural guardrail; the small transformer is the throughput and capability amplifier.

---

## 2. What the receipts actually prove

All six milestone receipts are real artifacts of the verifier at `scripts/verify_milestones.py`. The pass / fail picture, verbatim from `data/milestone_receipts.json` and `data/m3_baseline.json`:

| ID | Gate | Verdict | Headline number | What the number actually is |
| --- | --- | --- | --- | --- |
| **M1** | Real data flow | **PASS** | 18,757 records (13,218 / 2,851 / 2,688) | Production-shaped data successfully split with held-out isolation. Genuine. |
| **M2** | Standards docs | **PASS** | `SPECIFICATION.md`, `ACCEPTANCE_CRITERIA.md`, `PRODUCTION_ACCEPTANCE_STANDARD.md` present | Process gate, not a model gate. |
| **M3** | SFT readiness baseline | **FAIL** | Schema valid 68.6 %, arg-exact 28.6 % | **No checkpoint yet.** This is the unaided regex policy on real production-shaped records; it is the floor that any trained model must beat. |
| **M4** | FSM grammar coverage | **PASS** | 227 valid canonical calls, 19-state coverage | All FSM states reachable. |
| **M5** | Deterministic GRPO reward | **PASS** | Four components wired | Reward exists; not yet used to train a real checkpoint. |
| **M6** | Offload canary | **PASS** | 971 / 1,000 local offload, 36.87 % token savings | **Shadow canary** runner injects synthetic latency (`8 + 1 ms` local, `1100 + len(prompt)//8 ms` cloud). Useful for the routing decision, not for hardware timing. |
| **Held-out sample** | Execution pass | **99.1 %** (991 / 1,000) | Platform: POSIX 100 %, Windows 98.5 %, cross-platform 98.1 % | Deterministic regex policy + grammar on a 1,000-record slice of the held-out split. This is a **policy smoke test on real data**, not a model-quality result. |

**Honest reading.** Of the seven headline numbers above, five (M1, M2, M4, M5, the regex-policy 99.1 %) describe working infrastructure. Two (M3, M6) are simulations of a future trained model. **No number on this page is a measurement of a trained Wrench checkpoint, because no trained Wrench checkpoint has been released yet.**

The cleanest framing is the project’s own: this is **research-stage infrastructure with all the safety floor and routing plumbing in place, waiting on a trained model.**

---

## 3. Effectiveness , measured against the stated purpose

Wrench-SLM is meant to deliver three things:

### 3.1 Cheaper tool calls (token economics)

**Claim.** The 36.87 % cloud-token savings in `data/canary_summary.json` is the share of 1,000 canary prompts that the deterministic regex policy can fully answer locally.

**What it proves today.** A regex + grammar policy can correctly answer a meaningful share of routine prompts without ever crossing to the cloud. The cost model is real; the routing is real.

**What it does not prove.** The canary treats both latency values as synthetic constants, so the "130.23× faster" claim is a *ratio of two synthetic numbers*. It is a fair description of the design intent, but it is not a hardware measurement. Treat the latency gain as a *target*, not as a measurement.

### 3.2 Faster tool calls (latency)

**Claim.** Local 9 ms vs cloud 1,172 ms on average.

**Audit correction.** Read `wrench/canary.py` directly: the local value is `8.0 + 1.0 ms` and the cloud value is `1100 + len(prompt)//8 ms`. These are control constants, not measurements. The site should label them as such (it now does, in `docs/status.html`).

**Recommendation.** When Flash is built and the policy can actually run end-to-end on a Pi 4/5, replace this row in `data/canary_summary.json` with a real timing pass , for example, 1,000 prompts × 5 trials × p50/p95/p99 on the real device. Until then, this row of the canary table is **simulation**.

### 3.3 Narrower blast radius (safety)

**Claim.** Only read-only and diagnostic tools can be speculatively executed; mutations and destructive commands must escalate to the cloud.

**Audit.** The canonical protocol in `wrench/protocol.py` is strict JSON, validates required keys, and has `ROUTER_FALLBACK` as the only safe answer on doubt. The grammar mask is a real guardrail. **However:**

- `data/manifest.json` lists 522 records categorized as `mutation` in the production-shaped corpus. This is fine *if* those records are correctly excluded from local execution. The safety of the system depends on the policy not matching them, the FSM not letting them through, and the sidecar not training on them. Spot-checking `wrench/policy.py`, the deterministic policy uses a regex prefilter (`command_substring`) and never matches a mutation-prefixed command , that gate holds.
- The "zero false-local" gate from `docs/reference/PRODUCTION_ACCEPTANCE_STANDARD.md` is the right test. It has **not** been measured yet against the mutation subset. Recommended next experiment: a held-out replay that asks the regex policy the 522 mutation prompts and asserts zero matches.

**Summary.** The *design* is safe. The *demonstration* of safety on the mutation subset has not been done.

### 3.4 Mechanical-share fit

`docs/reference/SPECIFICATION.md` cites that **74.8–81.2 %** of the lean-router tool-call volume is mechanical, and that each frontier round adds ~2 s of prefill + decode on top of the tool cost. This is the structural reason the project exists. If that share is correct, Wrench has a large addressable slice to attack. **The share itself is a measurement of a sibling system (`lean-router/logs/`), not of Wrench.** I deliberately did not mutate the sibling repo to re-derive this number here.

---

## 4. The five biggest gaps between claim and proof

1. **No trained checkpoint is released.** The "0.5B" target is a configuration, not a model. `data/m3_baseline.json` makes this explicit by labeling M3 `FAIL`. Until the trained Wrench-Pro clears the 99.5 % schema-validity gate on the held-out split, every "effectiveness" number that is presented without a simulator caveat is over-claiming.
2. **The latency story is a simulation.** Replace the synthetic `LOCAL_LATENCY_MS` / `CLOUD_LATENCY_MS` constants with a real hardware pass before any public claim of "130× faster" lands in a README, slide, or social post.
3. **The 99.1 % held-out result is a policy result, not a model result.** It proves the deterministic fallback + grammar work end-to-end on real data. It does **not** prove that the trained model is good. The site now labels this correctly; the broader repo copy should follow.
4. **Safety is asserted, not measured against the mutation subset.** The leverage is on the *protocol contract* and the *grammar*. Both are solid. The remaining open item is the empirical "regex policy never matches a mutation prompt on the 522-record held-out mutation subset" check.
5. **Continuous training has no live traffic.** `wrench/sidecar.py` is implemented and can tail `lean-router/logs/tool_calls.log`, but the canary corpus (`data/canary_summary.json`) is a static, not a stream. Until the sidecar has actual live tool-call traffic to mine, the “in-a-loop learning daemon” is correctly architected but unexercised.

---

## 5. Verdict and recommended next steps

**Verdict.** Wrench-SLM is a well-defined, well-documented research project whose safety floor, routing, and grammar guardrails genuinely work today. Its effectiveness as a *model* is not yet measurable, because no model has been released. The project is honest about this in the receipts (`M3 = FAIL`, no checkpoint path in `models/`). The risk is that public-facing copy drifts toward "shipping" language before the model clears its gates.

**Recommended next steps, in priority order.**

1. **Train a real checkpoint** (Wrench-Pro 0.5B target) on the existing 13,218 / 2,851 production-shaped split with held-out quarantine. Re-run `scripts/verify_milestones.py`. The next M3 receipt is the moment the project graduates from "infra" to "model."
2. **Re-run the canary with real timing** on the target hardware: Pi 4 / Pi 5 for Flash, RTX 5070 Ti for Pro. Replace the synthetic constants in `wrench/canary.py` with measured p50 / p95 / p99 over 5 trials × 1,000 prompts.
3. **Run the mutation-safety replay** on the 522 `mutation`-categorized held-out prompts. Assert `executed_locally == 0`.
4. **Document the policy-result vs. model-result distinction** consistently across `README.md`, `goal.md`, `eval.md`, and `docs/`. The site already does this; the in-repo docs should match.
5. **Set a release gate.** `docs/reference/PRODUCTION_ACCEPTANCE_STANDARD.md` already names six anti-patterns (warm-cache, empty-loop, micro-benchmark, etc.). Lift those into a single executable gate in `scripts/` so any future README claim has a verifiable source.

---

## 6. Audit ledger

| Claim | Authoritative source | Status |
| --- | --- | --- |
| M1, M2, M4, M5 receipts | `scripts/verify_milestones.py` → `data/milestone_receipts.json` | Re-verified |
| M3 baseline (68.6 % / 28.6 %) | `data/m3_baseline.json` | Re-verified |
| M6 canary (971/1,000, 36.87 %) | `data/canary_summary.json` | Re-verified; **latency numbers are simulated** |
| Held-out 99.1 % | `scripts/verify_execution.py` on 1,000-record deterministic seeded slice | Re-verified; **policy result, not model result** |
| Hardware targets | `goal.md`, `docs/reference/SPECIFICATION.md` | Targets only; no measured profile yet |
| Mechanical share 74.8–81.2 % | Cited from sibling system `lean-router/logs/` | Out of scope for this audit; not re-derived |
| Grammar FSM coverage | `wrench/fsm.py`, `scripts/verify_milestones.py` (M4) | Re-verified |
| Mutation safety | Protocol contract + regex policy gate | Asserted; not measured on the mutation subset |
| Checkpoint release | `models/` directory | **Not present** at this checkout |
