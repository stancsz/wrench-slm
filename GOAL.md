# Wrench direction: Layer 1 and self-learning LoRA

Updated: 2026-09-23 (America/Edmonton)
Owner: human product owner; repository agent maintains the evidence

The current product direction is **Wrench v2**, a local Layer 1 context runtime
with a frozen Qwen checkpoint, a versioned Wrench-Core LoRA and a replaceable
Continuous LoRA learned from verified experience. This supersedes v1's
27B-to-4B pruning direction and the binary-classifier-only training target.

## Authoritative records

- [North Star](docs/northstar/README.md): customer, value, standards, constraints.
- [Architecture](docs/northstar/V2_ARCHITECTURE.md): context pipeline and adapter lifecycle.
- [Experiment v2](docs/northstar/V2_EXPERIMENT.md): stages, comparison arms, metrics and stop criteria.
- [Realignment goal](docs/goal/wrench-v2-realignment/GOAL.md): this cleanup's acceptance and evidence.
- [Gateway LoRA experiment](docs/goal/wrench-gateway-model-research/GOAL.md): current staged study of a small Wrench controller, stronger-model routing, and the measured 95/95 target.
- [V1 learning](docs/northstar/V1_LEARNINGS.md): incident account and durable corrections.
- [Storage/recovery](docs/northstar/STORAGE_AND_RECOVERY.md): strict aggregate limit below 50 GB.
- [Collaboration contract](COLLABORATION_CONTRACT.json): present execution authority.
- [Goal index](docs/goal/README.md): current and superseded work.

The current user-directed continuation is the bounded gateway LoRA experiment
linked above. It does not mark the deterministic v2 context baseline, E0-E4,
or 95/95 targets accepted. The product implementation milestones remain
staged in the experiment record.

Retained v1 tools, tests, source and receipts support reuse and regression
analysis. They do not establish v2 capability. The former corpus goal, paid
canary and hardware queue are historical scoped work; their permissions and
results do not transfer to this experiment. See the
[exact pre-realignment snapshots](docs/archive/2026-09-23-v1/README.md).
