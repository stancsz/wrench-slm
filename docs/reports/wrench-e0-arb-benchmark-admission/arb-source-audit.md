# ARB public benchmark source audit

Goal: [E0 ARB benchmark admission audit](../../goal/wrench-e0-arb-benchmark-admission/GOAL.md)
Task: source metadata, packaging, license scope, and oracle fit
Worker: root orchestrator; read-only subagent supervisor and three workers
Date: 2026-09-24 (America/Edmonton)
Repository revision: `b353e1a3d1bc81e11d08c8bbe7d3d22160694b1e`
Nonce: `ARB-SOURCE-AUDIT-7B4D`

## Decision

Keep ARB quarantined as a candidate public retrieval diagnostic. Do not
download, extract, train on, or use it for E4 utility claims yet. The current
published release metadata improves on the earlier inventory, but it does not
provide extracted peak bytes or complete source-rights provenance for the
current 25-repository benchmark.

## Pinned source metadata

- ARB GitHub repository current `main` at audit: commit
  `07014c986f3deadb1548c62b32c0ffbe6a81465d`.
- CLI release: tag `v0.2.1`, signed annotated tag object
  `0a91fcee206875e45c6f8c07563fbe280bb6bb5b`, resolving to commit
  `b487f3866cc13dd971819cb902517a6a50282404`.
- Hugging Face dataset revision: `5901e1ee3aff048290db72edf9c63bc498b79ea3`.
- Hugging Face dataset repo metadata labels its license `other` and last
  modified it on 2026-07-30. This is repository metadata, not a grant for every
  source file in the corpus.

The API metadata supplied the LFS SHA-256 and exact compressed bytes below.
Those hashes were read from metadata; no archive was downloaded and no local
digest was computed.

| Release | Published archive bytes | Published archive SHA-256 |
| --- | ---: | --- |
| `v2_code2test` | 443,641,745 | `387cdfb25835b176ba27707d43dc31cae6b31514231923af237ad04deef19c0b` |
| `v2_comment2context` | 278,591,728 | `be68161844d63c64e687e0c6da1d52434160fafcaf8932a5767fbe64b643b3f5` |
| `v2_trace2code` | 39,295,446 | `19b252e8cfff42107fedc74005dbb6972f2970af33651ce0c1571546819e41c4` |
| `v2_edit2ripple` | 128,720,663 | `a174196d69b531d176a65c76fea928b3f1c893710baa4efccc48e901ff404b2c` |
| `v2_abstention` | 171,536,521 | `bb358d6b65b7ef6aa36b417240cab4f2d51a8d69e699e573cf324ab339a5c1d8` |

The five primary archives total 1,061,786,103 compressed bytes. The current
README describes five self-contained subsets. It separately lists small
balanced and natural selective-retrieval sample-list releases, plus pilot and
trajectory artifacts. A stale monolithic archive is also present in the HF
tree at 441,222,815 bytes; do not confuse it with the five current subset
archives. The HF release manifest reports for `v2_trace2code`: 101 samples,
98 corpus rows, 356,074 chunks, and `all_gold_in_corpus=true`.

This reconciles the prior README concern that corpus instructions might depend
on other positive subset corpora. It does not independently verify the
contents or extracted size of any archive. A supervisor's intermediate note
miscounted six v2 archives by mixing the two selective sample-list releases
with the five primary data releases; the primary README, subset manifest and
complete HF tree show five primary releases plus separate selective lists.

## License and provenance findings

The repository's pinned `LICENSE` is MIT for the software and associated
documentation. Its data-license note separately says code, metadata, reports
and documentation are MIT-licensed, while redistributed source corpus chunks
retain their upstream licenses. That note's upstream-repository section
explicitly describes the V1 list of 13 repositories, while the current
benchmark README lists 25 sample-bearing repositories. The HF dataset license
label is `other`.

The metadata-only review did not establish a complete repository-at-base-
commit license and notice ledger for all current rows, or rights/provenance for
the query and workflow signals. Evaluation-only intent does not remove those
checks. Treat rights as unresolved until each included source and data field
has a documented basis.

## Oracle, leakage, and product fit

ARB evaluates next-file retrieval from coding workflow signals. It reports
file-level gold; `edit2ripple` has no span gold. Its canonical BCY is packed
under ARB's own tokenization convention, not an OpenCode/provider tokenizer.
The data notes positive samples use pre-resolution base commits. That reduces
one form of resolved-code leakage; it does not establish complete label
provenance, absence of model pretraining contamination, or task success.

The 50 natural no-gold cases and 32 wrong-repository counterfactuals are
different strata. The latter are easier controls and should not be pooled with
natural abstention. The documented grouped cross-validation is for an
abstention-threshold experiment; there is no general train/dev/test split.
Use no ARB data for Wrench training. If admitted later, report the four positive
tracks and two abstention strata separately as external retrieval diagnostics.
Do not convert file retrieval into user value or E4 outcome evidence.

`v2_trace2code` is the best initial external diagnostic match for Wrench's
failing-test/log-triage workflow and has the smallest primary-subset archive.
Its 39.3 MB compressed size does not establish the extracted size. The
storage checker reported `WITHIN_LIMIT` at 611,035,502 bytes before this
audit's documents, but a future archive job still needs complete output,
temporary and extraction accounting before reservation.

## Checks and handoff

- Read-only GitHub release, repository and Hugging Face metadata queries;
  no corpus bytes were fetched.
- Independent supervisor coordinated three read-only reviews of release
  inventory, licensing/provenance, and oracle/split fit.
- `git diff --check` passed for the working tree before commit. No benchmark,
  test, model, external provider, or client run was performed.
- Next: establish expanded archive size/member inventory and a complete
  base-commit repo/file license/provenance ledger. Only then prepare an
  artifact reservation. See the [evaluation review](../../evals/wrench-e0-arb-benchmark-admission/review.md).
