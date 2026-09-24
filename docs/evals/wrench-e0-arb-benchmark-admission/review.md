# ARB source admission evaluation

## Decision

Do not admit a dataset download yet. ARB is relevant as a public, file-level
retrieval diagnostic, especially `v2_trace2code`; the current source pages and
metadata provide enough to pin the compressed archive but not enough to admit
the data or claim rights and resource safety.

## Critique

The source README now documents five self-contained primary releases, which
resolves the earlier documentation ambiguity about selective corpora. The
current license note still names only the 13 V1 repositories, while the
benchmark's current sample table covers 25. HF labels the dataset `other`, and
the corpus inherits upstream licenses. Per-repository and task/query
provenance is incomplete. The selected trace archive's expanded peak is also
unknown.

ARB gold evaluates file retrieval, not task completion. Its token budget uses
its own tokenizer. Natural and counterfactual no-gold cases must remain
separate. A future Wrench report should compare lexical/BM25 retrieval with
the same candidate universe, but keep this public set out of training and
separate from consented matched-task E4 results.

## Verification and limitations

The primary HF LFS metadata lists `v2_trace2code` at 39,295,446 compressed
bytes with archive SHA-256
`19b252e8cfff42107fedc74005dbb6972f2970af33651ce0c1571546819e41c4`.
The value has not been checked against downloaded bytes. No archive member
inventory, expanded size, per-file license ledger, benchmark run, or task
outcome was verified.

Read-only independent review covered release packaging, licenses/provenance,
and oracle/split fit. `git diff --check` is the local repository check; no
dataset tests ran. No downloads, installs, provider calls, or client runs.

## Sources

- [ARB README](https://github.com/eyuansu62/agent-retrieval-bench/tree/07014c986f3deadb1548c62b32c0ffbe6a81465d)
- [ARB repository LICENSE](https://github.com/eyuansu62/agent-retrieval-bench/blob/07014c986f3deadb1548c62b32c0ffbe6a81465d/LICENSE)
- [ARB DATA_LICENSE.md](https://github.com/eyuansu62/agent-retrieval-bench/blob/07014c986f3deadb1548c62b32c0ffbe6a81465d/DATA_LICENSE.md)
- [ARB CLI v0.2.1 release](https://github.com/eyuansu62/agent-retrieval-bench/releases/tag/v0.2.1)
- [Hugging Face dataset revision](https://huggingface.co/datasets/eyuansu71/agent_retrieval_bench/tree/5901e1ee3aff048290db72edf9c63bc498b79ea3)
- [Hugging Face subset release manifest](https://huggingface.co/datasets/eyuansu71/agent_retrieval_bench/blob/5901e1ee3aff048290db72edf9c63bc498b79ea3/reports/v2_subset_releases_manifest.json)
- [Hugging Face data-license note](https://huggingface.co/datasets/eyuansu71/agent_retrieval_bench/blob/5901e1ee3aff048290db72edf9c63bc498b79ea3/DATA_LICENSE.md)
