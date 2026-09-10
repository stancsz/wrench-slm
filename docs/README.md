# Wrench-SLM GitHub Pages site

This folder is a static, dependency-free project site for Wrench-SLM.

## Contents

- `index.html` explains the Wrench-SLM purpose and the Flash / Pro split.
- `status.html` presents an intentionally bounded project-status view.
- `assets/status.json` mirrors selected values from the repository audit receipts so the site works when deployed independently.

## Keeping the status page current

When project receipts change, update `assets/status.json` from these repository sources:

- `../data/milestone_receipts.json`
- `../data/canary_summary.json`
- `../data/verification_report.json`

The site must preserve evidence boundaries. A replay, canary, or audit receipt is not proof of human adoption, live production behavior, or released-model quality.

## Preview locally

```powershell
py -3 -m http.server 8080 --directory docs
```

Then open `http://127.0.0.1:8080`.

## Deployment

Publish the contents of this directory as the GitHub Pages artifact or branch root. The site has no build step.
