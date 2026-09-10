# Controlled usefulness pilot v1

Design fixed on 2026-09-09 before candidate training and scored comparisons.
Runner/source hashes and selected checkpoint hashes must be recorded before the first evaluation request. Any subsequent implementation correction must be recorded; affected scored runs cannot silently be reused under changed conditions.

## Claim and population

Compare a native-tool cloud workflow (A), the same workflow with a deterministic speculative helper (B), and the same workflow with an isolated Pro SFT candidate (C). The claim is limited to authored Windows developer scenarios executed against real disposable OS fixtures. This does not estimate production traffic coverage, Pi performance, arbitrary shell execution, or general coding ability.

Dataset: data/pilots/authored-developer-v1. Manifest hashes identify the frozen inputs. Training has 640 scenarios in 32 wording families; development and calibration each have 80 scenarios in eight separate families; evaluation has 120 scenarios in 24 separate wording families. Each fixture seed belongs to exactly one split. Shared tool primitives are intentional; wording templates and scenario derivatives are split before instantiation.

The eight categories are configuration lookup, line extraction, literal code search, Git working-tree inspection, Git history inspection, loopback health diagnostics, draft-only file writes, and ambiguous service selection. Each evaluation category has 15 scenarios. All contents are generated and contain no private project data. Prompt and context are the only model/rule inputs. Hidden fixture contents and expected outcomes are never forwarded. Context-dependent requests use prior selection results available before prediction.

Language allocation is explicit: training/development/calibration are English; evaluation has 80 English and 40 Chinese tasks. Chinese is a held-out transfer probe of the pretrained model after specialization, not a claim that bilingual task training occurred. Report those results separately.

## Candidate and development budget

- Base: Qwen/Qwen2.5-0.5B-Instruct revision 7ae557604adf67be50417f59c2c2f167def9a775, original tokenizer, BF16, native SDPA.
- One planned SFT candidate: LoRA rank 16, alpha 32, dropout 0.05; attention and MLP projections.
- 150 optimizer steps, microbatch 2, accumulation 4, constant learning rate 0.0001, seed 42. Maximum total input plus supervised completion: 1536 tokens, no silent truncation.
- No GRPO, hyperparameter sweep, test-driven retraining, or vocabulary changes. A machinery failure may be repaired and rerun with a new receipt before evaluation; a quality failure is not grounds to secretly increase this budget.
- Compare base and SFT predictions on all 80 development examples, and audit the selected SFT candidate on all 80 calibration examples. Use these to disclose candidate limitations. The sole fixed-budget candidate is selected for the end-to-end experiment; do not select on evaluation outcomes.
- Local inference: input maximum 1536 tokens, output maximum 192 tokens, greedy decoding, complete output validation. No uncalibrated probability claims. Operating rule: offer a schema-valid call allowed by the bounded executor; model abstention, invalid generation, or unsupported input becomes fallback with a distinct recorded reason.

## Cloud protocol and resource limits

- Endpoint: http://127.0.0.1:4000/v1/chat/completions; request minimax/minimax-m3 with real native tool schemas on every turn, temperature 0, maximum 384 completion tokens, non-streaming.
- Per HTTP attempt: 45-second timeout, zero automatic transport retries, maximum request body 24,000 UTF-8 bytes. A transport failure remains a failed episode.
- Maximum three cloud turns per episode, including corrections, maximum two tool calls in any one returned message. Excess calls or incomplete responses are recorded as failures, never dropped.
- Main experiment: exactly 120 scenarios x three arms x one run = 360 episodes, up to 1,080 cloud attempts.
- Separate harness smoke allowance: at most 12 cloud attempts on development-only scenarios. Total experiment allowance: 1,092 attempts and 3,000,000 reported cloud tokens; admission reserves 32,768 input plus 384 output tokens against the remaining token allowance. Stop if usage is missing or routing expands beyond the native single-pass workflow.
- Stop on unexpected provider/model identity or Cheap Plus telemetry. Correlate request IDs with gateway event logs before final analysis. Provider token counts take precedence over local token estimates. Cached tokens and reported costs are preserved separately. Missing usage is unavailable, never zero.
- The earlier two gateway connectivity preflights are separate, already recorded diagnostics; they are not scored episodes.

## Execution and fairness

Construct the fixture before starting episode clocks. All three arms use the same immutable task snapshot and visible context; the same owned loopback service remains available for the three matched episodes. Verify the file fingerprint after each operation and arm. No model-generated write is applied. Git inspection uses optional index writes disabled. Unsupported commands and escaped paths are rejected before execution.

Randomize task order and arm order with seed 20260909. Run episodes serially to avoid a Wrench-only concurrency penalty or cloud-arm congestion from our own workload. Existing unrelated host activity is not changed and is a limitation. Record episode timestamps. Local model loading is outside clocks; all prediction tokenization, generation, and validation are inside C's clock. Rules and any local execution are inside B's clock.

For B and C, an eligible prediction is executed once before the first cloud request. The same speculative envelope contains the call and real observation, or the draft-only receipt, with an instruction to verify alignment. If incorrect, the cloud can request a correction through the normal tools. A falls through the ordinary cloud-call/tool-result loop. All arms use identical system instructions, tool definitions, final answer schema, and turn budget. No arm sees the expected answer.

## Outcomes and analysis

The cloud must return a final JSON object with an answer field: a string for configuration/health/commit subject, an ordered list for line extraction, filenames for Git status/search, DRAFT_ONLY after submitting a correct draft, or NEEDS_CLARIFICATION when the service cannot be identified. Success requires exact task-specific outcome equality, an appropriate real tool observation for resolvable read tasks, a correct registered draft for draft tasks, and unchanged fixture state. String/list comparisons are deterministic; shell-string equality is a separate diagnostic.

Include all assigned episodes. Report final task success, complete episode latency, p50/p95/p99, all cloud prompt/completion/cached tokens, actual tool calls, local prediction overhead, rejected or invalid predictions, unused speculation, and correction turns. No success-only latency average may replace the all-episode result. Cap failures only through the declared runtime limits, not by imputing a favorable completion time.

For comparisons, pair episodes by scenario. Report both raw scenario results and uncertainty clustered by the 24 wording families, using 10,000 seeded bootstrap resamples. Treat differences as evidence within this authored population. Report each category and language slice separately; do not search for a winning slice and call it confirmed.

For the quality decision, also use a conservative one-sided Hoeffding lower bound on the paired family-mean success difference in [-1, 1]: observed difference minus sqrt(2*ln(20)/24), bounded below by -1. This prevents the bootstrap's zero variance on identical outcomes from implying an unjustifiably tight quality guarantee. It will often make a small pilot inconclusive about the two-percentage-point margin.

Decision criteria from goal.md remain unchanged: observed C success must be no worse than A and B, with one-sided 95% uncertainty excluding a loss above two percentage points; C must save at least 10% mean latency or total cloud tokens against each comparator with an interval supporting improvement; report other material regressions. No unauthorized execution or invalid call may escape the boundary. A weak small-sample uncertainty bound must not become a GO merely because all observed examples passed. No-GO applies to this candidate and workflow, not to every possible Wrench model. NARROW findings require independent confirmation. Missing accounting or insufficient statistical evidence requires qualification or INCONCLUSIVE.

## Required receipts

Protocol and source hashes, dataset manifest and isolation/length audits, selected model and training receipts, base/SFT development results, calibration audit, environment definitions/fingerprints, per-attempt cloud requests/responses/usage, per-operation execution receipts, per-episode results, gateway correlation, reproducible aggregate analysis, and an evidence-backed decision report. Files under artifacts/usefulness-pilot are versioned and existing runs are preserved.
