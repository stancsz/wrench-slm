# Iteration 036: SubRoute model identity layers (2026-09-27)

## Question

Is the difference between SubRoute's configured model string
`openrouter/minimax/minimax-m3` and Wrench's pinned expected upstream model
`minimax/minimax-m3` an identity mismatch that would make the spend caller
reject a valid receipt?

## Finding

The source supports treating these as different layers, not as a mismatch.
SubRoute's LiteLLM configuration names its OpenRouter adapter with the
`openrouter/` prefix. Its adapter regression test calls the mapped
OpenRouter request with `model="minimax/minimax-m3"` and asserts that the
final outbound body retains that model string. The current Wrench caller
expects `minimax/minimax-m3` in the OpenRouter selected-endpoint receipt and
compares provider/model separately.

The current OpenRouter public endpoint catalog returns model ID
`minimax/minimax-m3` and lists a `Minimax` provider endpoint with that same
model ID. OpenRouter's API reference describes the chat response `model` as
the model that ended up being used. Its router-metadata example uses the
`provider`, `model`, and `selected` fields under
`openrouter_metadata.endpoints.available`, matching the Wrench receipt parser.
These sources support keeping the current canonical upstream pin and
case-insensitive provider check.

This is a source and public-contract check only. It does not prove what the
currently running SubRoute process loaded or what an actual paid completion
would return. No code change is indicated from the prefix difference alone.

## Exact identities inspected

Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
SubRoute HEAD: `51d262370b3de790ee97ec6b9d43c33e4b44a2ee`

| File | SHA-256 |
| --- | --- |
| Wrench `tools/subroute_budget_guard.py` | `dab8b7212e91c2687e13f53ab619e296bae3fb91e10b716ad57ec4c4933fb00b` |
| Wrench `tools/capture_subroute_teacher_traces.py` | `8852ded137d07a5cf7e47f93e38ca310272ef0ce0e0b0eea131a347925dc9ae6` |
| Wrench `tests/test_subroute_budget_guard.py` | `62b8c3bfe58a0d46be2189c766df1fb348540a9a5b1a6363e64df5076a8801b9` |
| SubRoute `config/litellm.yaml` | `05b40c8a4b95e7d9703dd88102f4d981f760cbf17da30d2def781ef958ef0735` |
| SubRoute `tests/test_openrouter_request_controls.py` | `56474aef1cceb773afdd1cb2a4d065c4c67d22b94e102e71a6b66a8b0461d1e9` |

## Limits and next gate

The latest host sample was 9.69% free RAM, below the 10% runtime floor. No
tests, training, inference, SubRoute POST, provider call, or spend occurred.
The final eight-case Wrench campaign-ledger suite remains pending exact-hash
runtime verification. After that suite passes and the separate no-provider
request-boundary test passes, a future capped study must still verify the
actual returned provider, model, token usage, generation ID, and billed cost.
No numeric aggregate spend cap has been supplied, so generation remains
closed.

## Sources

- [OpenRouter MiniMax M3 public endpoint catalog](https://openrouter.ai/api/v1/models/minimax/minimax-m3/endpoints), read 2026-09-27.
- [OpenRouter API response schema](https://openrouter.ai/docs/api_reference/overview), including the response `model` field.
- [OpenRouter router-metadata example](https://openrouter.ai/docs/guides/features/guardrails/overview), showing `openrouter_metadata.endpoints.available` records with `provider`, `model`, and `selected` fields.
