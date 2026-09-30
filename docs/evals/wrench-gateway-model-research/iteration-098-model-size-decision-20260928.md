# Iteration 098: model-size decision and savings priority reset

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-GW-MODEL-SIZE-DECISION-098-20260928`  
Status: **research decision recorded; Wrench effectiveness remains unproven**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Owner update applied

The active [gateway goal](../../goal/wrench-gateway-model-research/GOAL.md)
now records the requested 0.5B-12B research band, the highest-verifiable
full-lifecycle frontier-token-savings priority, the 2B gateway-controller
hypothesis, and the order to resume existing engineering work after the
research decision. The 10B-12B range is research-only under this update; the
prior sub-10B staged-experiment authority and all storage, hardware, data, and
spend gates remain unchanged.

This goal edit invalidated the previous hash binding in Fit-03's Iteration 087
package review. That package must be reviewed against the new goal identity
before a fit; no training occurred. The sealed held-out set was not opened.

## Research result

The selected gateway lead is **Qwen3.5-2B with a Wrench-specific LoRA**, for
bounded evidence extraction and context decisions. Its case combines an
already pinned 2,274,069,824-parameter / 4,571,274,023-byte snapshot, stronger
same-family tool-use scores than 0.8B, and a separate 2B LoRA paper that
measures the directly relevant tool-output pruning task. The paper's 92%
removal is per tool observation, with 0.86 recall and 0.80 F1 on 618 curated
test observations, not full-agent success or total frontier savings.

Keep 0.8B as a control; use 4B as the first capacity challenger only after a
named 2B failure. Qwen3.5-9B and Gemma 4 12B are coding-capability ceiling
comparisons, not default gateway choices. If the requirement is that the
local model itself perform all-day repository engineering, current evidence
does not select any model in the size band.

The report compares model sizes and roles, records official and paper evidence,
reconciles published compression claims with Wrench's measured proxy, and sets
the next evidence gates: [model-size decision report](../../reports/wrench-gateway-model-research/model-size-decision-20260928.md).

## Observations and limits

- Wrench's strongest existing measurement is 12.11% ratio-of-sums reduction
  on five synthetic selected-context input pairs; two positive evidence
  failures were recorded. Actual matched frontier-token savings remain N/A.
- External task-conditioned tool-output pruning reports 92% of individual
  observations removed. StateComp reports 38.89% savings on its Code slice.
  SKILL.state reports 97.57% less cumulative token use than its stateful
  baseline on a 200-step synthetic warehouse task; none is a Wrench result.
- Read-only GETs to `127.0.0.1:4000` returned HTTP 200 for
  `/health/liveliness`, `/models`, and `/api/active-model`. The active route
  remains `openrouter`, `force`, policy 4. No completion, provider call,
  credential read, or route modification occurred.
- The latest RAM sample during this iteration was 8.07% free; the RTX 5060 Ti
  sample was 14,844 / 16,311 MiB free. Four long-lived Python processes did
  not match the Wrench/test/train command-line filter and were left running.
  Runtime work remains closed below the 10% RAM floor; Fit-03 additionally
  requires 25% free RAM.
- The storage checker, including the Docker model volume, Wrench automation
  directories, sibling/worker repositories, and legacy temporary roots,
  reported `WITHIN_LIMIT`: 22,400,500,488 actual bytes, 7,603,000 reserved,
  22,408,103,488 projected against 50,000,000,000 bytes. The report job has a
  1,000,000-byte reservation. C: had 143,675,453,440 bytes free at admission.

## Verification and next step

This iteration was read-only research and documentation. No tests, model
download, inference, benchmark, training, package, held-out evaluation, or
provider request ran. The goal and report were updated; source implementation
work was not changed by this iteration.

Resume Iteration 097's stable-source E0 path with source review first. Run its
focused tests only after a fresh resource sample is at or above 10% free RAM,
and account for scratch with the existing Iteration 097 reservation. Do not
start Fit-03 until its exact package has been refreshed for the new goal hash
and its 25% RAM, storage, output-path, and destination-space gates all pass.

## Sources

- [Qwen3.5-2B pinned card and tool benchmark table](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/README.md)
- [Squeez paper](https://arxiv.org/html/2604.04979)
- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Qwen3.5-9B pinned model card](https://huggingface.co/Qwen/Qwen3.5-9B/blob/cc5442c03a5c0bff0bd4c6888d9a40029c637733/README.md)
- [Gemma 4 benchmark card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [SKILL.state paper](https://arxiv.org/html/2608.26263)
- [StateComp paper](https://arxiv.org/abs/2609.27298)
