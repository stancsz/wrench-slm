# Wrench developer documentation

The website connects the mission, current bounded worker, practical example,
client status, evidence, and hardware roadmap. Product mission: affordable AI
for the rest of us. Initial audience: less than 8 GB of GPU memory. Next target:
less than 2 GB and older phones. Sharing spare compute with friends is a future
vision, not a shipped feature.

Both languages are complete: English at `/index.html`, conversational Chinese
at `/zh/index.html`. The language switch preserves the page and section anchor.
Chinese source lives in `site/pages/zh/`. The build shares assets and generates
Chinese illustration labels from the original SVG. Keep section IDs aligned
between translations so deep links continue to work. The checker enforces page
parity, document language, matching IDs, and counterpart links.

The bilingual homepage uses the hook "Spend the good tokens on the hard parts"
and "好钢用在刀刃上。好 token，花在真难题上。" The new under-0.5% cloud-cost
ambition is explicitly separate from the existing 95% frontier-token target
(equivalent to at most 1/20 baseline usage). The 4M copy describes hybrid
large-input retrieval, not native attention or a completed hardware benchmark.

## Build and preview

Python 3.11+ is sufficient for the static build. No frontend package install is
required.

```powershell
python tools/build_docs_site.py
python tools/check_docs_site.py
python -m http.server 4387 --bind 127.0.0.1 --directory artifacts/docs-site
```

Open http://127.0.0.1:4387/. Test the mobile layout, documentation navigation,
example case buttons, copy buttons, and FAQ disclosures. Content remains
readable without JavaScript. Fonts use Google Fonts with local fallbacks.

## Example receipt

The saved public receipt is produced by `examples/local_first.py`, using the
real Python verifier in an installed checkout. It normalizes the temporary
fixture path to its basename. It does not expose local directories, model
artifacts, provider logs, credentials, or billing data.

To refresh after a relevant verifier change:

```powershell
python examples/local_first.py | Set-Content -Encoding utf8 site/assets/demo-receipt.json
python tools/build_docs_site.py
python tools/check_docs_site.py
```

Use UTF-8 without a BOM (PowerShell 7). Verify the captured output, rather than
editing a receipt to make a claim pass. This example is not a cost benchmark.

## GitHub Pages

Publish only the checked contents of `artifacts/docs-site` to the root of the
`gh-pages` branch. Configure Pages to deploy from that branch's root. The
`.nojekyll` file keeps the static HTML and assets intact. Do not publish the
repository root, runtime code, raw `phases/`, or local artifacts.

GitHub Pages from a private repository requires an eligible existing GitHub
plan. The website can be public while the source repository remains private.
Do not change repository visibility or upgrade a plan as part of deployment.
If the current plan blocks Pages, complete the local preview and obtain a
decision on a separate public documentation-only repository.

The canonical project path is `/wrench-slm/`. Normal assets and navigation use
relative URLs. Update the 404 home link if deploying under a different name.

## Editorial maintenance

- `GOAL.md` owns scope and acceptance. The website translates it for developers.
- Keep mission, next milestones, demonstrated behavior, and shipped support distinct.
- Keep the README, homepage, roadmap, and evidence page aligned.
- Do not imply public source access, a license, device support, or paid savings
  until each is actually available or demonstrated.
- Update the review date when refreshing status. Do not auto-label old evidence
  as current during a build.
- Detailed experiment receipts remain private; call summaries maintainer
  summaries and give readers a public bounded example they can inspect.

## Review findings, 2026-09-22

The original README described internal workstreams without a first-use path.
The current private GitHub repository had no Pages configuration, homepage,
release, or license file. Historical site references in memory were absent
from this checkout. The new site provides a clear mission, tested local
example, plain-language tool reference, honest client status, and staged
hardware roadmap. The remaining activation gap is a publicly accessible,
licensed distribution, which this documentation task does not manufacture.

First-use success means an authorized collaborator reproduces all three
example outcomes. No analytics or tracking is installed. Website visits or
stars should not be reported as successful use or savings.
