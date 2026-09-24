# V2 reference review

Checked: 2026-09-23 (America/Edmonton). This was a primary-source documentation
and metadata review. No competing product, model or benchmark was run.

## Primary product reference

[Headroom's repository](https://github.com/headroomlabs-ai/headroom) documents
a local content-aware compression layer, proxy/library/MCP surfaces and cached
originals retrievable through CCR. It also describes cache alignment. This
matches Wrench's context-preparation job closely. Its claimed savings are
vendor results and vary by content; no matched Wrench superiority is established.

Compare installation/reversal, exact recovery, context usefulness, task success,
token/cost accounting, cache behavior, latency and inspectability on the same
tasks. Headroom now documents additional memory/learning features, so do not
claim Wrench uniquely learns from usage based only on the older design notes.

## Supporting patterns

- [Aider repository maps](https://aider.chat/docs/repomap.html) select relevant
  signatures and repository relationships using graph ranking within a token
  budget. Borrow structural candidate selection, then retrieve exact code.
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) supports incremental
  syntax parsing. [Sourcegraph precise navigation](https://sourcegraph.com/docs/code-navigation/precise-code-navigation)
  uses semantic indexing. Syntax and resolved definitions/references are
  complementary; current Wrench Python AST helpers do not provide both.
- [Anthropic advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use)
  describes deferred tool discovery and programmatic orchestration. In Wrench,
  discovering a schema must remain separate from granting execution authority.
- [Qwen3.5-0.8B model card](https://huggingface.co/Qwen/Qwen3.5-0.8B) identifies
  a post-trained checkpoint with a vision encoder. Use the complete
  [pinned file manifest](model-candidate.json), not the parameter label, for
  storage planning. Published upstream benchmarks are not Wrench measurements.
- [PEFT mixed adapters](https://huggingface.co/docs/peft/developer_guides/mixed_models)
  distinguishes same-type adapters from mixed methods and cautions that
  training PeftMixedModel is untested/not recommended. Do not assume that
  loading two LoRAs establishes correct simultaneous training and freezing.
  [PEFT model merging](https://huggingface.co/docs/peft/developer_guides/model_merging)
  documents multiple merge strategies; they are not interchangeable with
  the exact additive composition required by our design.

## What the research changes

Use native small weights, external source memory, a deterministic baseline,
recoverable context references and independently versioned adapters. Prove
backend composition before training. Evaluate complete tasks and the costs
of learning instead of copying isolated published accuracy/savings numbers.

The [owner notes](inputs/README.md) retain the wider prior-art survey and its
links, including retrieval/routing research. That survey is historical design
input. This page only calls the references above freshly reviewed; it does
not certify every numerical claim in the supplied notes.
