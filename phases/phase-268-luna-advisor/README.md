# Phase 268: worker-plane claim and receipt dry-run

Status: local orchestration dry-run passed. No hardware result was produced.

The Sol advisor was consulted after the 5060 Ti lane showed a repeatable
pending-with-no-consumer state. Its recommendation was to test the worker
claim and receipt protocol locally before spending more time on semantic
evaluation or prompting the idle remote thread.

The exact pending manifest was copied into an isolated local queue sandbox and
processed by `tools/simulate_5060ti_worker_claim.py`. The mock executor:

1. copied the immutable manifest into `jobs/pending`;
2. atomically moved it to `jobs/running`;
3. emitted a liveness receipt with a unique claim nonce;
4. atomically moved the manifest to `jobs/failed` with a terminal
   `BLOCKED_MOCK_ONLY` receipt;
5. recorded the transition log and explicit unavailable GPU/resource fields.

The mock never downloaded the model, ran the preflight command, queried a GPU,
or created an independent 5060 Ti claim. The final sandbox had zero pending
entries, zero running entries, zero completed entries, and three failed-side
diagnostic entries. This separates a valid queue protocol from the still
missing worker dispatch/authentication.

Evidence:

- `advisor-packet.txt`
- `advisor-response.json`
- `mock-queue/jobs/failed/wrench-5060ti-hf-package-20260921-02.liveness.json`
- `mock-queue/jobs/failed/wrench-5060ti-hf-package-20260921-02.mock-receipt.json`
- `mock-queue/transitions.jsonl`
- `tools/simulate_5060ti_worker_claim.py`
- `tests/test_simulate_5060ti_worker_claim.py`

The advisor also recommended one final bounded remote liveness challenge with a
nonce and exact command output, then stopping remote attempts if the worker
times out, returns an unrelated acknowledgement, omits the nonce/output, or
fails authentication. This phase does not authorize that external action.

