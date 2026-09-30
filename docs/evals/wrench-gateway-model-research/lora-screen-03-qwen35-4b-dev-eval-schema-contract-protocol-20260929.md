# Qwen3.5-4B dev preflight revision: expose the bounded output contract

Status: proposed exact-hash evaluator revision. It permits only a fresh
one-prompt preflight after independent static review, storage reservation, and
live resource admission. It does not admit the 64-row score unless both arms
pass preflight. It does not open held-out data or permit provider requests.

## Motivation and exact change

Iteration 181 preflight 07 returned valid JSON in both arms under the
non-thinking configuration, but the scorer rejected enum values. The system
message named JSON fields without showing the allowed route, operation, and
reason-code values. This revision adds one fixed schema-contract sentence to
the model-visible system context for **both** frozen-base and LoRA arms. It
lists the same enum values enforced by the scorer, requires evidence IDs to
come from the request, and says `retrieve_more` is boolean. The exact task/user
message, answer labels, parser, validator, decoding, thinking-mode setting, and
96-token output cap stay fixed. The contract describes the interface and does
not reveal the expected per-example decision.

This is development tuning on the dev split. The prompt projection bytes and
manifest remain hash-pinned and immutable; the scorer makes a copy in memory
and appends the fixed contract only after verifying those source hashes. The
scorer SHA binds the contract text and transform. Its per-prediction input hash
is computed over the actual transformed messages. Report the resulting local
prompt-token count, including the contract overhead. Keep the held-out split
sealed and do not use its rows to refine this contract.

## Frozen package and gates

All unchanged identities and controls carry forward from the
[screen-03 development evaluation protocol](lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md)
and [instruct-mode revision](lora-screen-03-qwen35-4b-dev-eval-nonthinking-protocol-20260929.md):
pinned Qwen3.5-4B revision and inventory; frozen 96-step inactive adapter;
answer-blind 64-row prompt projection; separate oracle-only projection;
exact Windows runtime and RTX 5060 Ti; 10% RAM/VRAM floor; bounded local-only
outputs; sealed predictions before any oracle read; no provider client; and
one-shot job IDs and artifact paths.

Before the one-prompt preflight, require an independent exact-hash review of
the current scorer and this protocol, a fresh `check_wrench_storage_budget.py
status`, a unique reservation of at least 500,000,000 bytes including every
external Wrench root, at least 5 GiB destination-volume free space, and fresh
10% RAM/VRAM admission. Check resources while the run is live and account for
all output bytes before releasing the reservation.

Use the current scorer with `--mode preflight` and a new
`WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-NN` ID. Both arms must complete below
the cap and pass the unchanged validator. A failure stays sealed and does not
admit full scoring. A passing preflight still requires a separately reviewed
64-row score package and a separate storage reservation. Held-out data remains
closed.

## Interpretation boundary

The schema addition is deterministic Wrench mechanics, not LoRA capability.
The paired base/LoRA comparison measures any additional decision benefit under
the same supplied contract. A synthetic dev pass does not establish coding
effectiveness, 95/5 routing, Frontier usage or savings, all-in cost, or
sustained engineering. Local tokenizer counts are not provider billing. No
provider calls, activation, or production routing are permitted.
