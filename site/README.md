# Wrench documentation site

The active project objective is the [30% frontier-token reduction goal](../docs/goal/wrench-token30/GOAL.md). This static site is historical product documentation; its old North Star, token targets and release plans do not define the current experiment.

## Build and check

Python 3.11+ is sufficient. Build to a task-specific temporary directory and
check the output before publishing or replacing generated files:

```powershell
python tools/build_docs_site.py --output tmp/site-preview
python tools/check_docs_site.py --site tmp/site-preview
```

Keep source pages under `site/pages/` and generated output under
`docs/gh-pages/`. Do not use a site build to rewrite historical evaluation
receipts. Any published status must link to the active goal and describe its
evidence limits accurately.
