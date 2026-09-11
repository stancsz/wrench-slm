# Project guide

This is the shortest reliable map of the repository. Start here when a fresh
agent or operator needs to understand what is maintained, what is experimental,
and which command owns a claim.

## Start here

1. Read `README.md` for the current V21 artifact and bounded results.
2. Read `NORTHSTAR.md` for durable product direction.
3. Read `ARCHITECTURE.md` for system boundaries and invariants.
4. Read `docs/product-specs/PRODUCT_SPEC.md` for the product contract.
5. Read the active `GOAL.md` before changing the selective-offload track.
6. Read `docs/reference/MODEL_RELEASE_HANDOFF.md` before restoring or training
   the release package.

## Common workflows

### Verify a restored release package

```powershell
python scripts/fetch_assets.py --list
python scripts/fetch_assets.py --asset package-v21
python scripts/verify_assets.py
python -B scripts/verify_weight_package.py artifacts/model-release/package-selected-v21
```

Use the exact asset and package paths printed by the commands. A private model
or asset repository requires an authenticated account.

### Run repository checks

```powershell
py -3 -m pytest --import-mode=importlib tests -q
ruff check scripts/ wrench/ tests/
```

The explicit `tests` path is intentional. This workspace can contain an
ignored clean-export under `artifacts/repository-cleanup/` with duplicate test
module names; an unscoped root pytest invocation can collect those files and
fail before running the current checkout. Use `python -B` for relocated or
checksummed packages so Python bytecode does not create untracked files inside
the verification tree.

### Inspect selective-offload evidence

The current active contract and result documents are:

- `goal.md` and `goals/active/selective-offload-real-runtime-v2/GOAL.md`
- `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md`
- `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_RESULT.md`
- `scripts/verify_trusted_readiness.py`

The readiness gate is expected to reject the current metadata-only receipt.
That rejection is evidence of an incomplete M2-data prerequisite, not a failed
product release. Do not run a paid provider pilot without explicit attempt and
token ceilings, the required readiness receipt, and operator authorization.
When those prerequisites are available, use
`scripts/run_authorized_selective_pilot.py` so the readiness check runs before
the frozen runner. The frozen runner's `--dry-run` path remains available for
zero-provider preflight verification.

## Documentation map

| Need | Read |
| --- | --- |
| Public overview | `README.md`, `docs/index.html` |
| Project status | `docs/status.html`, `docs/assets/status.json` |
| Architecture | `ARCHITECTURE.md` |
| Product intent | `NORTHSTAR.md`, `docs/product-specs/PRODUCT_SPEC.md` |
| Release reproduction | `docs/reference/MODEL_RELEASE_HANDOFF.md`, `docs/reference/TRAINING_FROM_CLONE.md` |
| Release lineage and licenses | `releases/v21/README.md`, `MODEL_CARD.md`, `LINEAGE.md`, `NOTICE` |
| Data rules | `data/README.md`, `docs/reference/TRAINING_CORRECTNESS_AUDIT.md` |
| Script inventory | `scripts/README.md` |
| Code and workflow map | `docs/reference/CODE_GUIDE.md` |
| Historical material | `docs/reference/archive/` and documents explicitly marked historical |
| Research notes | `docs/wiki/index.md` |

## Status vocabulary

- **Maintained** means the path is part of the current documented workflow.
- **Verified** means a named executable receipt exists for the named scope.
- **Historical** means retained for lineage or compatibility and not a current
  gate.
- **Experimental** means code may be useful for research but has no release or
  production claim by presence alone.
- **Blocked** means a stated external decision or missing evidence prevents the
  next contract step. It does not mean ordinary implementation work is hard.

## Documentation rules

- Tie every metric to a receipt, denominator, date, and environment.
- Keep release inputs, pilot data, historical data, and generated fixtures
  visibly separate.
- Do not rewrite historical results to match the current model.
- Treat a package release and production readiness as separate gates.
- When product intent changes, update `NORTHSTAR.md` and the product spec
  before weakening or replacing an active goal.
