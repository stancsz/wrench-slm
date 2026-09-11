# Website and project documentation

The `docs/` folder contains the static GitHub Pages website and project
documentation. The repository-level architecture and product intent are in
[`ARCHITECTURE.md`](../ARCHITECTURE.md), [`NORTHSTAR.md`](../NORTHSTAR.md), and
[`product-specs/PRODUCT_SPEC.md`](product-specs/PRODUCT_SPEC.md). The concise
operator map is [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md). Detailed training,
audits, pilots, and release handoffs live in [reference/](reference/).

The folder reorganization is complete: the former `gh-pages/` website files are directly in `docs/`, and the documents previously in `docs/` are now in `docs/reference/`.

```text
docs/
  index.html       Website overview
  status.html      Release status page
  assets/          Website scripts, styles, and status data
  product-specs/   Durable product contract
  PROJECT_GUIDE.md Operator and contributor map
  reference/       Training instructions, specifications, audits, and handoffs
    archive/       Historical documentation
```

For the model release, start with the [release handoff](reference/MODEL_RELEASE_HANDOFF.md) and [training from a clone](reference/TRAINING_FROM_CLONE.md). For selective offload, start with the active goal, the [real-runtime protocol](reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md), and the [production evidence matrix](PRODUCTION_EVIDENCE_MATRIX.md).

For contributors, use the [project guide](PROJECT_GUIDE.md) and the [code and
workflow guide](reference/CODE_GUIDE.md). The latter maps the Python modules,
script families, test families, and their evidence boundaries.

## Contents

- `index.html` explains the Wrench-SLM purpose and the Flash / Pro split.
- `status.html` presents an intentionally bounded project-status view.
- `PRODUCTION_VALUE_SCORECARD.md` and `PRODUCTION_EVIDENCE_MATRIX.md` provide the current production and token-value audit.
- `PRODUCTION_EVIDENCE_INTAKE.md` defines the exact authorized inputs required to run the matched value experiment.
- `assets/status.json` mirrors selected values from the repository audit receipts so the site works when deployed independently.

## Keeping the status page current

When project receipts change, update `assets/status.json` from these repository sources:

- `../data/archive/baseline/milestone_receipts.json`
- `../data/archive/baseline/canary_summary.json`
- `../data/archive/baseline/verification_report.json`

The site must preserve evidence boundaries. A replay, canary, or audit receipt is not proof of human adoption, live production behavior, or released-model quality.

## Preview locally

```powershell
py -3 -m http.server 8080 --directory docs
```

Then open `http://127.0.0.1:8080`.

## Deployment

Publish the contents of this directory as the GitHub Pages artifact or branch root. The site has no build step.
