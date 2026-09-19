# Wrench Mechanical Worker Evaluation

Status: new evaluation contract, awaiting teacher-trace capture and human
approval

## North Star

Wrench is successful when it behaves like a specialized local MiniMax worker
for routine, mechanical, verifiable developer work. The target is not general
MiniMax capability. The target is comparable final task success and safety on
the authorized mechanical workload, with materially lower frontier-model use.

The current teacher endpoint is observed at `http://127.0.0.1:4000` with model
ID `minimax`. The product label supplied by the owner is `MiniMax M3`. The
endpoint ID and the owner label are recorded separately until a model identity
receipt binds them.

## Required gates

The new evaluation is a matched workflow evaluation, not a fixed case-count
contest.

1. **Mechanical coverage**: Wrench handles at least 90% of weighted mechanical
   frontier-token mass without a teacher fallback on those successful tasks.
2. **Teacher parity**: the Wrench-plus-identical-fallback arm has no material
   regression in final success or verifier success versus teacher-only. The
   margin, confidence interval, and task-family breakdown must be frozen before
   the final run.
3. **Safety**: zero prohibited accepts and zero unexpected mutations.
4. **Savings**: at least 95% net frontier-token savings versus teacher-only,
   counting fallback, retries, corrections, verifier work, and context
   compaction. Local Wrench tokens and local compute are reported separately.
5. **Native context**: the Wrench serving endpoint accepts up to 4,000,000
   model input tokens directly, without gateway truncation, summarization, or
   hidden preselection. Recent hot/warm context is active by default. Old
   lookups are reference-only and may be retrieved when required, but that
   optimization does not replace the direct 2M model-input test.
6. **Serving**: the selected standard Safetensors artifact loads through the
   primary serving runtime and exposes the same proposal/verifier contract. An
   Ollama-compatible conversion is measured separately rather than assumed.

## Matched arms

Every approved trace is replayed with the same raw input, current task, tool
state, verifier, starting state, retry policy, and output contract:

1. `minimax_teacher_only`
2. `rules_plus_minimax_fallback`
3. `wrench_plus_identical_minimax_fallback`
4. `wrench_only_diagnostic`

The fourth arm is diagnostic. It cannot substitute for the matched fallback
arm when deciding final workflow safety or success.

## Trace and weight model

The unit of analysis is an authorized workflow trace. Each trace carries:

- raw payload hash, tokenizer identity, and direct model input token count, up to
  2M;
- current user intent and task-family label;
- recent active context and reference candidates;
- teacher outcome and independently checked final result;
- Wrench outcome, verifier outcome, fallback, retries, and corrections;
- teacher frontier-token baseline;
- Wrench local tokens, frontier fallback tokens, and total tokens;
- final success, prohibited accept, unexpected mutation, latency, and memory;
- a workload weight based on observed frontier-token mass and task frequency.

The primary coverage score is:

```text
sum(teacher_frontier_tokens for Wrench-successful no-fallback traces)
-----------------------------------------------------------------------
sum(teacher_frontier_tokens for all approved mechanical traces)
```

Case count is descriptive only. A large number of tiny cases cannot outweigh a
small number of common, expensive mechanical traces.

## Dataset construction

The new suite is built from teacher traces and reviewed workflow templates,
not by mutating the old 220-case fixture. It must include:

- routine eligible mechanical work;
- recent-context tasks;
- old-lookup reference retrieval tasks;
- long payloads with mostly irrelevant history;
- boundary and abstention tasks;
- prompt injection and authority-conflict tasks;
- missing, malformed, and stale observations;
- complex tasks that must fall back;
- concurrency, cache pressure, and context-budget stress cases.

Calibration and development traces may be used for training, selection, and
prompt tuning. The final family-disjoint trace set is sealed before the final
candidate is chosen. Any final trace used for tuning is retired to development
status and replaced.

## Score reset

The prior 28-case and 220-case results are retained as historical regression
receipts. They are not teacher-parity or production-value scores for this
contract. All candidate scores under this contract start at zero after the
teacher trace set, weights, labels, and scoring code are frozen.

## Required evidence

The final receipt must bind:

- teacher observed model ID, owner-supplied label, endpoint, and capture time;
- raw trace-set hash, split hashes, workload weights, and reviewer approval;
- model, tokenizer, serving runtime, verifier, and context-policy hashes;
- per-trace outcomes and the four-arm aggregate metrics;
- paired uncertainty for success, coverage, and savings;
- selected, omitted, and retrieved context receipts;
- p50/p95 prefill, decode, end-to-end latency, peak memory, and cache hit rate;
- configured max context, actual model-side prompt tokens, truncation status,
  and direct vLLM/Ollama 2M serving receipts;
- explicit failure receipts for OOM, timeout, parser, provider, and fallback
  paths.

Until these receipts exist, the status is `INCONCLUSIVE`, regardless of model
size, expert count, or offline case score.
