# ToolBeHonest input

This folder holds the public English evaluation data pinned to Hugging Face
dataset revision `524ef5422f63899e7c1a97c791197c37ace0e051` and the upstream
MIT license.

## Pinned input

- File: `data/test_en.json`
- JSON records: `350`
- Paired task variants: `700`
- Bytes: `1078934`
- SHA-256: `51495dc14e5403ccc56d7430253cf41a1e5aa30ce7e35ae9b207fce667ea7a2a`
- Scenarios: missing necessary tools, potential tools, limited functionality
- Levels: seven `subtask` values, 50 records each

Each record contains a task with its tool list and an unsolvable counterpart
with a corresponding tool list. The Wrench adapter should preserve those
pairs, case IDs, and the original `subtask` label.

## Wrench projection

Use only the Level-1 solvability decision for the primary Wrench comparison:
solvable maps to `not_abstain`; unsolvable maps to `abstain`. Report exact
match and false-solvable rate separately for each scenario. Wrench does not
emit the benchmark's multi-step plan or missing-tool explanation, so those
levels are outside this comparison.

The original ToolBH tools are not Wrench's six authorized developer actions.
This run therefore measures transfer of the abstain/continue gate over an
external tool list. It is a component result, not end-to-end Wrench task
success. Do not count a benchmark tool call as a supported Wrench action.

The data file is ignored by Git. Run `fetch.ps1` to download the pinned
revision and verify its SHA-256.

## Completed Wrench component run

The frozen Wrench gate processed all 700 variants at
`runs/wrench-qwen-head-v1/` using the pinned data SHA-256
`51495dc14e5403ccc56d7430253cf41a1e5aa30ce7e35ae9b207fce667ea7a2a`.

| Wrench projection | Result |
| --- | ---: |
| Abstract Level-1 binary accuracy | 53.6% (375/700) |
| Solvable cases continued | 16.0% (56/350) |
| Unsolvable cases continued | 8.9% (31/350) |
| Paired records with both variants exact | 11.7% (41/350) |
| Unsupported Wrench-menu continuations | 12.4% (87/700) |
| Model-decision latency p50/p95 | 204/274 ms |

The abstract and allowlist views answer different questions. The abstract view
tests Level-1 solvability transfer. In the policy view all 700 menus contain
foreign tool names, so Wrench should abstain on every row; its observed 87
continuations are boundary errors. Published GPT-4o and Llama-3-8B results use
the original ToolBH output protocol and are outside reference points, not
matched Wrench comparisons. The run generated no tokens, made no provider
calls, and executed no tools. RAM and VRAM stayed above the repository's 10%
reserve.
