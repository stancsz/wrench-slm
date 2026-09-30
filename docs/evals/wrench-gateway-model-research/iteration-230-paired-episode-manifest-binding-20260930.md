# Iteration 230: bind paired usage to a frozen episode manifest

Date: 2026-09-30 (America/Edmonton)
Job ID: `WRENCH-ITER230-PAIRED-EPISODE-HASH-BINDING-20260930-01`
Scope: local response-usage accounting and synthetic unit tests only.

## Gap

The paired token aggregator matched arms by `pair_id`, but that identifier did
not bind either arm to the task and fixture definition. Reusing a pair ID for
different task content could therefore produce a mathematically valid ratio
that was not a same-episode comparison.

## Change

Each usage receipt and arm episode now carries a lowercase SHA-256
`episode_manifest_sha256`. Receipt integrity hashes include the manifest
identity. Aggregation requires both arms for each pair ID to carry the same
manifest digest and rejects disagreement with
`paired_episode_identity_mismatch`. Receipt/episode digest disagreement also
fails closed. A new synthetic regression covers a reused pair ID with
different baseline and Wrench manifests; another covers manifest tampering.

The producer must hash a canonical, frozen episode manifest that covers the
task and fixture identities, then pass the same digest to both arms. This
iteration adds the guard only; it does not define or wire that producer.

## Verification

Focused command:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_frontier_usage.py
9 passed, 3 subtests passed in 0.64s
```

The tests use synthetic response bodies and never call a provider. No model,
tokenizer, credential, SubRoute, or held-out data was accessed. No runtime,
training, or product-success claim is made.

## Artifact identity and limits

- `src/wrench_harness/frontier_usage.py`: `5C9C2C13F495A011610293213E21E5EB26474AFD07DB3F99BD448A0FDD708001`
- `tests/test_frontier_usage.py`: `DDD8999AA48B2DC036C59BF227477FB350FE592A437C464FB88BCB3063FFDA80`

`episode_manifest_sha256` remains caller-supplied: until an
approved capture path constructs it from the exact frozen prompt/task/fixture
manifest and wires it through both arms, this guard alone does not prove that
two real requests were equivalent. The full-lifecycle frontier-token,
verified task-success, cost, and all-day engineering targets remain unproven.

The on-disk gateway goal SHA-256 is
`2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`; the
heartbeat-declared SHA-256 is
`B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`.
The mismatch remains unresolved and model work remains fail-closed.
