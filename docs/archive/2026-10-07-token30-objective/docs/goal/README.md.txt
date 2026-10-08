# Goals

- [First 30% frontier token reduction](wrench-token30/GOAL.md) (in progress,
  owner-directed 2026-10-06): compare the same complex task family with quality
  gates and complete frontier input, output, retry and recovery accounting.
  Local model tokens are free for this target and reported separately. The
  local diagnosis pilot is quality evidence; frontier reduction remains
  unmeasured. The owner approved $1 per task; the first frontier request
  returned HTTP 401, and authenticated access remains pending.

- [Selective local routing and frontier-fallback proof](wrench-gateway-model-research/GOAL.md)
  (active, owner-directed 2026-10-03): the Wrench LoRA adds task-routing
  behavior to Qwen; locally handle only task families supported by held-out
  quality and safety evidence, and hand uncertain or difficult tasks to the
  user's stronger model. Next: wire an immutable episode manifest through
  paired request and usage capture. Fixed 95/5 routing is superseded as a
  product quota. Provider calls and model runs remain behind their per-job
  authorization and admission gates. See the
  [research addendum](../reports/wrench-gateway-model-research/research-20260927.md),
  [readiness record](../evals/wrench-gateway-model-research/iteration-000-readiness-20260927.md),
  and [screen protocol](../evals/wrench-gateway-model-research/lora-screen-01-protocol-20260927.md).
  Historical strategy and same-agent critique remain in the
  [2026-09-26 research](../reports/wrench-gateway-model-research/research-20260926.md)
  and [review](../evals/wrench-gateway-model-research/review-20260926.md).

- [Measure acceptable local work](wrench-local-acceptability/GOAL.md) (closed
  2026-09-26 by owner decision): the 0.8B local SLM did not pass semantic
  acceptance screens, and the small-model OpenCode primary/controller direction
  is not feasible for the intended workflow. End-to-end frontier savings remain
  N/A with zero eligible matched pairs; the closure is not full v2 acceptance.
  See the [decision report](../reports/wrench-local-acceptability/direction-closure-20260926.md).
  Historical evidence: exposed
  synthetic screens cover exact reads, line ranges, literal searches, and four
  bounded review-only patch operations with exact diff/application oracles and
  abstention boundaries. The fresh E0 localization tokenizer profile stopped
  before loading its tokenizer or scoring cases because of a Windows lockfile
  hash mismatch; its exposed fixture is quarantined. These are mechanics results
  only; open-ended patch work and local SLM task classes remain unaccepted. A
  fresh deterministic failing-test evidence-packet attempt also stopped before
  scoring due to a runner defect; its exposed fixture is quarantined. Real-work
  utility and frontier-token savings remain unmeasured pending consented,
  outcome-verified matched tasks and complete usage receipts.
- [North Star pilot readiness](wrench-northstar-pilot-readiness/GOAL.md):
  proposed opt-in OpenCode corpus and task-oracle protocol; customer discovery,
  consent, and capture remain unapproved and unperformed.
- [E0 caller-owned context preparation](wrench-e0-context-pipeline/GOAL.md):
  accepted local composition of snapshot reads, structural candidates,
  request-pinned artifacts, bounded context, deferred schemas, prompt gating,
  an incomplete no-model receipt, and a deterministic preparation-accounting
  companion. This is not E0 milestone acceptance.
- [E0 snapshot-backed structural index](wrench-e0-snapshot-structural-index/GOAL.md):
  accepted bounded candidate-index slice; it does not scan or execute code.
- [E0 bounded outcome receipt](wrench-e0-outcome-receipt/GOAL.md):
  accepted reference-only schema/accounting contract and a v2 preparation to
  post-run evidence join; caller-supplied metadata does not prove truth,
  authority, consent, or complete lifecycle capture.
- [E0 serialized prompt budget gate](wrench-e0-serialized-prompt-gate/GOAL.md):
  accepted complete-message gate using injected serializer and token counter;
  fixture identities do not establish production runtime equivalence.
- [E0 bounded namespace registry](wrench-e0-namespace-registry/GOAL.md):
  accepted descriptive discovery and deferred schema lookup; schemas grant
  no execution authority.
- [E0 snapshot to artifact to context roundtrip](wrench-e0-snapshot-artifact-roundtrip/GOAL.md):
  accepted exact-byte roundtrip and bounded context admission.
- [E0 snapshot to context admission](wrench-e0-snapshot-context/GOAL.md):
  accepted in-memory exact-source bridge.
- [E0 deterministic context runtime](wrench-e0-context-runtime/GOAL.md):
  completed first implementation increment for query-ranked, bounded evidence
  assembly; does not claim full E0 completion.
- [E0 snapshot identity and exact-source retrieval](wrench-e0-snapshot-retrieval/GOAL.md):
  accepted bounded source-manifest and stale-source retrieval increment;
  POSIX pytest follow-up is complete.
- [E0 configured-root-bound snapshot identity](wrench-e0-snapshot-root-binding/GOAL.md):
  accepted v2 snapshot hash binding to the normalized configured root path;
  it is not physical-directory identity or authorization.
- [E0 snapshot root-object identity](wrench-e0-snapshot-root-identity/GOAL.md):
  accepted v3 binding to the root filesystem object and continuity token across
  validation, snapshot creation, and retrieval; IDs are replacement signals,
  not authentication or transaction proof.
- [E0 OpenCode V2 context adapter contract](wrench-e0-opencode-context-adapter/GOAL.md):
  provider-free, release-pinned session-root validation and local admission
  classification plus structural post-run session binding; OpenCode v2.0.15 is
  isolated-installed and configured for the local gateway, with version/config
  checks and a model-list GET only. A synthetic offline loopback request/lease
  boundary and a strict Wrench-owned project enrollment registry are
  independently reviewed; no Wrench hook integration or task/prompt request
  has run. The enrolled registry now feeds an in-memory selected-source
  snapshot seam, covered only by synthetic tests and static review. A
  synthetic offline composition now joins candidate selection, exact retrieval
  and store roundtrip, context preparation/materialization, final-message
  lowering, and the fixture request lease. A route-owned offline path joins
  deterministic rule-route evidence through preparation, lowered request, and
  terminal fixture lease receipt; independent review passed. This remains
  synthetic-only evidence. Provider wire, tokenizer equivalence, dispatch veto,
  and the exact-token E0 gate remain unresolved.
- [E0 ARB benchmark admission audit](wrench-e0-arb-benchmark-admission/GOAL.md):
  read-only review of the proposed public retrieval diagnostic; release metadata
  is pinned, while licensing and expanded-size evidence still block acquisition.
- [E0 bounded artifact store](wrench-e0-artifact-store/GOAL.md):
  accepted standalone content-addressed persistence with a caller-owned
  preparation facade now using it; production request lifecycle integration
  and recovery qualification remain open.
- [E1 Windows candidate identity verifier](wrench-e1-candidate-identity/GOAL.md):
  accepted synthetic-fixture mechanics for flat manifests on the reviewed
  Windows NTFS host; no model candidate was downloaded or evaluated.
- [E1–E3 lifecycle gap audit](../reports/wrench-v2-realignment/e1-e3-lifecycle-gap-audit.md):
  read-only review finds model/runtime identity, consented experience lineage,
  and adapter activation/recovery incomplete; a synthetic-only lifecycle
  component is the recommended next engineering increment.
- [E3 synthetic model-version lifecycle](wrench-e3-synthetic-version-lifecycle/GOAL.md):
  accepted bounded, offline version state-machine mechanics with hash-bound
  manifests, admission, request pins, rollback/reset, and recovery fixtures;
  production compatibility and recovery remain unproven.
- [Wrench v2 realignment](wrench-v2-realignment/GOAL.md): completed historical
  cleanup and experiment-definition record. Its original continuous-personal
  LoRA direction is superseded by the current selective-routing direction.
- [Experiment v2](../northstar/V2_EXPERIMENT.md): planned product implementation
  stages, beginning with the deterministic context/recovery baseline.
- [Wrench 25k quality data](wrench-25k-data/GOAL.md): superseded v1 binary-only
  corpus scope. Retained for provenance, unresolved data/charge findings and
  reusable validation work; not an active v2 generation instruction.
