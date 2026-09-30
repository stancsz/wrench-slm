# Iteration 065: cluster inference and SubRoute 4000

Timestamp: 2026-09-28 (America/Edmonton)

Repository: Wrench `af01304824f079a64b6c3902397a2034b843511a`

## Decision and evidence

The product-proof protocol now assigns the five confirmatory acceptance claims
to the LoRA Wrench hybrid arm and allocates a one-sided 99% confidence bound to
each (`alpha=0.01`, Bonferroni family-wise alpha 0.05). The deterministic
Wrench + frontier arm is a distinct secondary control. Any future confirmatory
claims for that control need an expanded multiplicity plan fixed before
enrollment.

The protocol also freezes the population estimands as weighted completion and
route proportions, conditional verified-success retention, and ratios of
paired weighted token and all-in cost totals. It rejects averaging per-task
token or cost savings percentages, dropping failures/rescues, or treating a
zero-denominator resample as a pass. Paired arms remain together through
resampling. Task-family labels are strata with preregistered weights, not four
independent clusters. Three repositories and ten workdays remain coverage
floors, not proof that cluster inference has enough independent units.

Before enrollment, the actual sampling frame still needs design-specific
simulation of coverage at all five null boundaries and joint power at declared
alternatives. It must reflect repository/workday clustering or their crossed
dependence, imbalance, within-cluster correlation, family weights, pass
correlation, and heavy token/cost tails. Require at least 80% joint power or
classify the study as pilot/inconclusive. The 234-episode alpha-0.05 example
and 398-episode alpha-0.01 binary planning result are IID single-endpoint
illustrations, not a product sample-size calculation. The statistical basis
and links are in the [product-proof protocol](product-proof-design-20260927.md),
including the [few-cluster inference study](https://onlinelibrary.wiley.com/doi/10.1111/ectj.12107)
and [multiway clustering paper](https://www.nber.org/papers/t0327).

## Current host and route gates

The fresh sample measured 3,044.4 / 32,701.8 MiB free RAM (9.31%),
15,234 / 16,311 MiB free VRAM on the NVIDIA GeForce RTX 5060 Ti, and
140,508,729,344 bytes free on C:. No Wrench training, inference, benchmark,
test, or packaging process was found. RAM is below the 10% run floor and the
25% fit-03 launch gate. No model work or delegation ran.

The owner directed use of the existing SubRoute setup at
`http://127.0.0.1:4000`. Its reviewed forced `openrouter` alias maps to
MiniMax M3 and declares streaming but not native tool calling. No provider
generation was sent: a numeric campaign cap and durable caller-side
reservation/settlement with usage and billed-cost receipts are still absent.
Do not ask for the cap again. Preserve this route for future matched
comparisons after the spend boundary is implemented.

Storage was `WITHIN_LIMIT` at 10,991,411,353 bytes actual plus 8,253,000 bytes
in active reservations before this report was accounted. This documentation
work used reservation `WRENCH-95-5-CLUSTER-RATIO-ITER065-20260928`; release it
after the final file accounting and record the post-release status.

The 0.8B Qwen candidate remains the narrow LoRA controller/compactor for
bounded proposals, context selection, and abstention. The separately pinned
4B candidate remains a possible code worker only after its own package review,
download/fit admission, and repository-task evaluation. Neither is proven to
meet product quality. Keep held-out task data sealed and synthetic checks
mechanics-only.

## Work performed and remaining proof

Updated the product-proof protocol and this iteration record. No tests,
provider requests, credential reads, model downloads, inference, training,
benchmark, or delegation ran. The user-specified SubRoute at port 4000 is
recorded as the comparator route; the experiment did not claim a measured
comparison.

Still unproven: the trained Wrench LoRA, representative 95/5 task mix,
frontier-only success retention, 95% frontier-token reduction, 95% all-in
cost reduction, and sustained all-day engineering. Fit 03 remains closed by
the free-RAM gates and missing fresh exact-hash package review. Provider calls
remain closed by the missing campaign cap and caller-side ledger. No product
acceptance claim is made.
\n