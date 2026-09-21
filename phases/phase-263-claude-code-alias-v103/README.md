# Phase 263: Claude Code recognized-alias routing diagnostic

Status: `NOT_VERIFIED`.

Anthropic's gateway documentation describes `ANTHROPIC_BASE_URL` as the
unified endpoint setting and says custom gateway model names can be configured
through the provider's model configuration. The CLI reference also documents
using a recognized model alias such as `sonnet`.

This phase tested that documented shape against Claude Code 2.1.251 without
using an unknown Wrench model name. The child process used a fake local API
key, `ANTHROPIC_BASE_URL=http://127.0.0.1:28939`, `--bare`, the recognized
`sonnet` alias, and nonessential traffic disabled. A local v103 Wrench
Anthropic endpoint was listening with a metadata-only trace.

## Observed result

Claude Code initialized as `claude-sonnet-5`, but its final usage record still
reported `provider=firstParty`. The Wrench trace file was never created, so no
request reached the local endpoint. The run reported `$0.016196` provider
usage. This is not a Claude Code integration pass.

This confirms that the installed subscription-managed Claude Code build does
not honor the local `ANTHROPIC_BASE_URL` for this configuration. Further
provider attempts are stopped. The remaining path is a supported local Claude
launcher or a separately configured LLM gateway that owns provider selection.

References:

- https://docs.anthropic.com/en/docs/claude-code/llm-gateway
- https://docs.anthropic.com/en/docs/claude-code/cli-usage

Evidence:

- `receipt.json`
- `claude-alias-v103.trace.jsonl` is retained locally as diagnostic output and
  is intentionally not part of the release claim.
