# Gateway experiment iteration 000: readiness

Date: 2026-09-27 (America/Edmonton)
Status: readiness only; no LoRA training, model generation, or benchmark run
Goal: [active gateway LoRA experiment](../../goal/wrench-gateway-model-research/GOAL.md)
Research: [model research addendum](../../reports/wrench-gateway-model-research/research-20260927.md)

## Owner authority

The owner requested a new study, a trained Wrench-specific LoRA, overall
effectiveness evidence, sustained engineering capability, and the subroute at
`http://127.0.0.1:4000`. This authorizes fresh Wrench-authored synthetic data
and a bounded local LoRA experiment when job admission passes. The request did
not set a dollar cap. Because the live route is a mutable force-mode OpenRouter
alias, no generation request was sent.

The existing 2026-09-26 closure of Qwen3.5-0.8B as a general OpenCode primary
or semantic controller remains intact. A new narrow LoRA screen is a different
hypothesis: finite context selection/compaction/escalation choices validated by
deterministic Wrench code. It cannot establish general coding or all-day work.

## Observed state

| Item | Observation | Admission result |
| --- | --- | --- |
| RTX 5060 Ti | 16,311 MiB total; 10,970 MiB used; 5,083 MiB free | 10% floor is 1,631 MiB; current additional safe allowance is at most about 3,452 MiB. Training fit unverified. |
| System RAM | 31.94 GiB total; 13.97 GiB free | Above the 10% floor at this sample; repeat during a job. |
| Storage | Checker `WITHIN_LIMIT`; actual 10,940,197,573 bytes; active reservations before this doc job 1,103,000 bytes; headroom 39,058,699,426 bytes | Documentation reservation created: `WRENCH-GATEWAY-EXPERIMENT-DOCS-20260927-01`, 10,485,760 bytes. Training reservation not created. |
| Small checkpoint | Qwen3.5-0.8B, revision `2fc06364715b967f1860aea9cf38778875588b17`, existing local snapshot 1,769,980,465 bytes / 13 files per prior report | Candidate only. Rehash all files and freeze a new manifest before training. |
| Larger checkpoint | Qwen3.5-4B public pinned tree 9.34 GB; no local download | Not admitted. Current safe GPU headroom is insufficiently evidenced for 4B LoRA. |
| Training stack | Python 3.13.15, Transformers 5.17.0, Torch 2.14.0+cu132; PEFT and bitsandbytes not present in checked environment | Dependency plan and exact compatible versions required. Existing inference environment should not be silently changed. |
| Gateway route | `GET /api/active-model` returned `active_model=openrouter`, `mode=force`, `policy_version=4`; prior audit maps the alias through OpenRouter/MiniMax M3 | Route is not an identified local model. User requested it, but no USD cap; no inference call. |

## Sol advisor consult

Consultation model: `codex-sol-advisor` through the available advisor route.
Usage: 559 prompt + 499 completion = 1,058 tokens. The decision changed: do
not start a 4B QLoRA run under current GPU occupancy; freeze the protocol and
storage plan first, then attempt only a monitored smaller-candidate feasibility
step if 10% RAM/VRAM can remain free. No unrelated process was stopped.

## Result

Readiness is **partial**. Disk headroom is sufficient for documentation, and
the smallest checkpoint is already local. Training is not admitted because the
PEFT stack, training peak, output manifest, fresh data split, and per-job
reservation are not yet established. Frontier generation is not admitted
because the active route can incur provider charges and the user has not set a
USD cap.

No metric rows are eligible. The 95% task-value retention, 95% all-in cost
reduction, 95% frontier-token reduction, and day-long engineering results all
remain **N/A**, not zero. No synthetic or old exposed screen was counted as a
pass.

## Next gates

1. Freeze the fresh synthetic-only data generator and split manifest, with a
   sealed held-out set excluded from all training/tuning.
2. Rehash the exact 0.8B snapshot; inspect adapter target modules and package
   compatibility without changing the existing runtime identity.
3. Reserve the measured peak (trainer environment/cache, temporary state,
   one adapter, logs) and check destination free space plus current RAM/VRAM.
4. Run a monitored single-step feasibility check only if the 10% reserve is
   available; continue to a small fit only if the check completes without a
   reserve breach. Do not download 4B under the current observation.
5. Obtain the user's USD cap, pin the active route and actual provider/model,
   define usage receipts, and only then run a matched frontier arm on synthetic
   tasks. Real workflow utility remains a later opt-in gate.
