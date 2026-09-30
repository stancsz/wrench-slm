# Iteration 096: persisted state enters E0 context compilation

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-GW-E0-STATEFUL-CONTEXT-096-20260928`  
Status: **narrow E0 integration implemented and mechanics verified; utility and live-client integration remain unmeasured**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway research goal SHA-256 preserved:  
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Change

`prepare_e0_context` now accepts a host-loaded execution-state receipt. It bounds the receipt and fact count, checks every state evidence reference against the exact source identities loaded for that E0 request, and fails closed without producing a prompt when a referenced source is absent or stale. Valid facts enter the same bounded `ContextLedger` as evidence-linked summaries. The prompt compiler marks them as untrusted data, and the existing final serializer/token counter accounts for their added prompt content. Selected-source receipts expose summary lineage; preparation receipts bind the state revision, state hash, event hash, selected fields, and omitted fields.

This creates a deterministic bridge from the event store in Iteration 095 into E0 preparation. The host still chooses and loads the state receipt; no model gained filesystem, shell, routing, or execution authority.

| File | SHA-256 |
|---|---|
| `src/wrench_harness/e0_context_pipeline.py` | `1D5AB770389DAC16485125A12E71B9D2B1AD6CFE8A465ACF076723B2D9DDD03D` |
| `src/wrench_harness/selected_segment_sources.py` | `7B34D2966E8B23CCB0DA8E1B9AA1D1D7389867BB3110860951F3CA25D40B6C7A` |
| `tests/test_execution_state_e0_context.py` | `43ECBCE93D10B7CC9BD5446C301D2921DB274029990209EF02756DFB8D9A913A` |

## Verification

The focused Python 3.11 `unittest` module passed **3/3** cases:

- A persisted fact is compiled as untrusted context, selected by the ledger, linked to its exact source, and included in the final prompt-token count.
- Preparation without a state receipt keeps the stateless path ready.
- A changed source fails closed with no prompt.

The test counter is deliberately a character-count test double. It verifies that the compiler's final serialized output is counted, not tokenizer-specific token savings. The test uses temporary synthetic source and state data and removes its scratch directory afterward. `git diff --check` passed for the changed source and test files.

## SubRoute and host admission

At the owner's direction, the existing `http://127.0.0.1:4000` SubRoute was checked with GET requests only. `/health/liveliness`, `/models`, `/models/openrouter`, and `/api/active-model` returned HTTP 200. The active snapshot was `openrouter`, `mode=force`, `policy_version=4`. These checks identify the configured alias and mode; they do not verify which upstream served a completion. No completion, provider call, route change, or credential access occurred. The aggregate spend cap remains unspecified, so generation remains closed.

The final live host sample for this iteration showed 727,703,552 / 34,290,302,976 bytes of free RAM (2.12%) and 15,210 / 16,311 MiB of free VRAM. RAM was below the required 10% reserve. No model load, training, inference, benchmark, package, or delegated job ran; only bounded source work and focused unit tests ran.

The post-report storage check reported `WITHIN_LIMIT`: 15,418,949,564 bytes actual and 6,353,000 bytes in active reservations, or 15,425,302,564 bytes projected against the 50,000,000,000-byte ceiling. The report and code remain under the repository root. The accounting included the approved data root, Docker model volume, and hourly automation directory. C: had 144,090,820,608 bytes free at the destination-space check.

## Limits and next work

The source evidence ID currently includes the complete snapshot hash as well as path and content hash. Consequently, a new repository snapshot makes a persisted fact's evidence ID stale even when the cited file itself is unchanged. This bridge proves same-snapshot compilation and changed-source rejection, not long-horizon continuity across ordinary repository edits. The next source task is a stable, namespaced path-plus-content identity that still invalidates a fact when its cited file changes, with current-source reacquisition before prompt compilation.

There is still no integration into a live OpenCode transport or SubRoute request, no learned LoRA decision in this path, no real-tokenizer matched comparison, and no coding-task outcome or lifecycle-cost result. This iteration does not establish the 95% success, 95% frontier-token or dollar savings, or sustained all-day engineering targets. The gateway claim remains unproven.
