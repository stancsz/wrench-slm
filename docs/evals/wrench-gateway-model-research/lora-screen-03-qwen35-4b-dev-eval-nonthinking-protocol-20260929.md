# Qwen3.5-4B synthetic dev preflight revision: instruct mode

Status: proposed exact-hash evaluator revision. It permits only a fresh
one-prompt preflight after independent static review, storage reservation, and
live resource admission. It does not admit the 64-row score unless both arms
pass preflight. It does not open held-out data or permit provider requests.

## Reason for the revision

Iteration 180 preflight 06 used the exact frozen prompt and failed both arms:
each generated 96 tokens of non-JSON reasoning text and reached the output cap.
The pinned Qwen3.5 tokenizer template opens a thinking block by default and
closes it when its `enable_thinking` template variable is false. The official
[Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B) documents
thinking mode as the default and describes instruct/non-thinking mode. The
[Transformers chat-template docs](https://huggingface.co/docs/transformers/chat_templating_writing)
state that extra keyword arguments to `apply_chat_template` are exposed as
template variables.

This revision sets `enable_thinking=False` in the local template call for both
the frozen-base and LoRA arms. It does not edit examples, messages, labels,
model weights, tokenizer files, decoding determinism, parsing, validation, or
the 96-token output cap. This tests one generation-configuration hypothesis;
it does not presume the model will produce valid decisions.

## Frozen package and admission

All unchanged identities and fail-closed controls carry forward from the
[screen-03 development evaluation protocol](lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md):
pinned Qwen3.5-4B revision and 14-file inventory; frozen 96-step adapter;
answer-blind 64-row prompt projection; separate oracle-only projection;
exact Windows runtime and RTX 5060 Ti; 10% RAM/VRAM floor; bounded local-only
outputs; sealed predictions before any reference access; no provider client;
and one-shot job IDs and artifact paths. The existing preflight 06 and its
failed prediction files remain immutable and are not inputs to this revision.

Before the one-prompt preflight, require:

1. Independent static review of the current scorer, this revision, and the
   unchanged protocol/pins, with all hashes recorded before and after review.
2. Fresh `check_wrench_storage_budget.py status` and a unique
   `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-NN` reservation of at least
   500,000,000 bytes, including every external Wrench root. Verify 5 GiB of
   destination-volume free space after the reservation.
3. Fresh hardware admission with at least 10% RAM and VRAM free. Recheck while
   the job runs and account output bytes before releasing its reservation.

Use the current scorer with `--mode preflight` and the unique reservation ID.
Both arms must have no errors or timeout, produce nonempty output below 96
tokens, and pass the unchanged JSON schema validator. Any failure stays sealed
as a failed diagnostic. Only a completed preflight admits a separately
reserved, separately reviewed 64-row dev score under the original protocol's
full-score gates. Neither step may inspect held-out payloads.

## Interpretation boundary

This is synthetic development evidence, not coding-agent effectiveness,
Frontier token usage, billed savings, 95/5 routing, all-in cost, or sustained
engineering evidence. Local tokenizer counts remain local counts. The adapter
remains inactive and the route remains unchanged.
