# Wrench-SLM product specification

Updated: 2026-09-11

## Product intent

Wrench-SLM should reduce stronger-model work on a small, reliable subset of
routine developer tasks by producing a structured proposal or a safe local
read-only result. It should preserve correctness and clear fallback behavior
when the local model cannot establish the requested outcome.

The product is not a general coding agent, an autonomous shell, a hosted API,
or a claim of universal model intelligence. The current project is a research
and release repository with one verified adapter package and an active
selective-offload experiment.

## Product surfaces

| Surface | Current status | Contract |
| --- | --- | --- |
| Wrench-Pro V21 adapter | Maintained release | Load with the pinned Qwen base and use the repository formatter/validator |
| Full verified V21 package | Maintained reproducibility path | Restore from the asset catalog and verify checksums before use |
| Selective local completion | Active experiment | Read-only, public-context, verifier-gated, fallback-first |
| Wrench-Flash | Proposed | No validated checkpoint or Raspberry Pi benchmark in this release |
| Sidecar and legacy integration | Historical/experimental | Not a V21 serving recipe or production proof |

## Intended use

The intended operator supplies a developer request, Windows/PowerShell context,
declared tools, and visible resources. Representative supported shapes include
configuration/file reads, literal search, Git status, local health reads, and
review-only write proposals. Unsupported operations, missing tools, invalid
bounds, ambiguity, and unsafe actions should become explicit fallback rather
than forced local completion.

## Release contract

V21 is a LoRA adapter trained from authored supervised examples. Its release
identity, base revision, checkpoint selection, data lineage, evaluation
receipts, licenses, and package checksums are defined by `releases/v21/` and
`docs/reference/MODEL_RELEASE_HANDOFF.md`.

The recorded V21 suite results are bounded evidence: 440/440 frozen holdout
exact predictions, 280/280 routine cases, 160/160 fallback cases, and 220/220
fresh-context cases. These are not a production traffic sample or a guarantee
of arbitrary coding reliability.

## Selective-offload acceptance

The active experiment must establish, in order:

- an oracle-free local route with zero provider calls on accepted local cases;
- a fresh disjoint evaluation with runtime routing separated from offline gold;
- trusted, provenance-labeled scenario data and a versioned cloud price ledger;
- matched cloud-only, rules-plus-fallback, and rules-plus-learned workflow
  accounting;
- an operator decision that enables learned selection, keeps rules-only, or
  disables local completion.

No positive value claim is allowed until provider prompt/completion tokens,
cached tokens, calls, billed cost when available, local time, total latency,
fallbacks, corrections, failures, and final outcomes are recorded for the
same assigned tasks across all arms.

## Non-goals

- arbitrary command execution or deployment;
- autonomous writes;
- replacing the stronger model for general coding;
- claiming production adoption from fixtures, simulations, canaries, or
  metadata-only log scans;
- promoting Wrench-Flash without a checkpoint and hardware evidence;
- calling experimental grammar, speculative decoding, or SDPA code a shipped
  performance feature without direct measurements.

## Decision policy

Prefer deterministic rules when they cover the same safe scope. The learned
proposal earns inclusion only when it improves on the same rules and fallback
path with complete accounting, no observed local-caused wrong completion, and
no boundary violation. Uncertainty must be reported, not hidden by pruning
failed rows or relabeling authored data as production traffic.

## Source hierarchy

1. Current release receipts and package manifests.
2. Current code and executable tests.
3. `NORTHSTAR.md` for durable product direction.
4. The active goal for current experiment acceptance.
5. Historical reference documents, which explain lineage but do not override
   current evidence.
