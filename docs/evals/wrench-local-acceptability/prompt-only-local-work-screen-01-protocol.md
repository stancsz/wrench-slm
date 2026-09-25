# Prompt-only local work screen 01

Status: preregistered before inference. This is a small open-development screen
of direct, low-risk synthetic support tasks for the pinned local SLM. It is a
separate prompt-only diagnostic and cannot satisfy the local SLM gate in the
goal, which requires evidence from an actual tool result. It does not evaluate
Wrench tool routing, repository operations, real-work utility, or frontier-
token savings.

## Question and scope

Can the pinned Qwen 0.8B answer three narrow task classes directly from text
supplied in the same prompt, with exact evidence and safe abstention?

The classes are (1) mapping a visible exception line to one of four listed
categories, (2) extracting a unique configuration value, and (3) locating a
function in a supplied code excerpt that contains a named property access.
Each class has four answerable cases and two boundaries. The boundaries cover
no matching evidence and ambiguous evidence. The model receives no tools and
cannot read or modify files. Function localization requires evidence quotes
for both the function definition and the matching property access.

## Frozen identities and procedure

- Job ID: `W2-LOCAL-PROMPTONLY-SCREEN-20260925-01`
- Nonce: `PROMPTONLY-6C31`
- Model: `Qwen/Qwen3.5-0.8B@2fc06364715b967f1860aea9cf38778875588b17`
- Runtime, serializer, tokenizer and model file pins: inherited from
  `tools/run_local_synthetic_challenge.py` and its fixed local runtime lock.
- Fixture: `tests/fixtures/local_prompt_only_work_v1.json`
- Fixture SHA-256: `525f8cb9639d17633a466129fb7b386ea0cdd33594e4c9a34e10dd6de40ecf9e`
- Runner: `tools/measure_local_prompt_only_work.py`
- Runner SHA-256: `c0fe54bdfeb6a4829303fcd06999a28f4b3f753c9ab3e3a6bec99ccb55fef58a`
- Hard-deadline supervisor: `tools/run_local_prompt_only_work_with_deadline.py`
- Supervisor SHA-256: `4d3f6833ce41a6eb6002a30e234a176ae3f0d2d06ac044e1c1e89634ea35b275`
- Pinned loader/watchdog: `tools/run_local_synthetic_challenge.py`
- Loader/watchdog SHA-256: `417ee3574c48b7dc6efc0ab7f0add2e292611d1fead38b69ad5a14a76200f23e`
- Measurement code revision: `6b52aacaa1b34e1967fdff8c1b12f07da501c2da`; exact repository HEAD at run start is recorded in the receipt.
- Output: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\prompt-only-work-01.json`
- Network: disabled by the pinned local loader; no provider, client, or
  localhost request.
- Generation: greedy, batch size 1, at most 192 new tokens, a cooperative
  60-second generation limit, context at most 4096 tokens; one response per
  case, no retry. A completed response taking over 60 seconds fails its case.
  The supervisor terminates the whole child process after a hard 25-minute
  deadline if native generation does not return. The runner refuses direct
  invocation without the supervisor's process marker, and the supervisor marks
  the receipt as incomplete on hard timeout.
- Training and weight changes: none.

The fixture includes prompts and host-side exact answer/evidence oracles. The
runner sends only the class instruction and each case prompt to the model. It
records a response before scoring it. The exact answer, cited line(s) and
quote(s) must match the frozen oracle. Localization must cite both its function
definition and matching property access. Unknown cases must return the
expected reason, with no answer or evidence. Invalid JSON, missing fields,
extra fields, an incorrect answer, or an incorrect boundary is a case failure.

## Acceptance and reporting

A class passes this diagnostic only if all six cases pass, all four positive
answers exactly match, both boundaries abstain correctly, and there are no
runtime errors or prohibited actions. Any failed case fails that class on this
screen. A pass means only “passed this six-case synthetic prompt-only screen.”
It does not mean the class is generally locally acceptable. Report counts by
class and preserve raw responses in the local artifact receipt. Do not tune or
train against these exposed development cases.

This is an exposed diagnostic screen, not an estimate of task acceptance.
Its cases are closed-form text tasks, with four answerable prompts and only
missing/ambiguous boundaries per class; there is no held-out or independent
real-task oracle. Passing does not establish generalization, semantic code
repair, tool use, Wrench routing, a safe local agent, or production utility.
No frontier calls are part of either arm, so frontier-token savings remain
N/A.

## Stop conditions

Stop without retry if the runtime/model identity is not exact, RAM or VRAM free
falls below 10%, a response takes over 60 seconds, an output or log path
already exists, or the storage admission is no longer valid. The runner checks
the aggregate storage budget before every checkpoint and at 30-second resource
sampling intervals; the supervisor checks it before opening logs and when
marking a timeout. A native call that does not return is bounded by the
supervisor's hard 25-minute process deadline. The job reservation is
150,000,000 bytes; check destination free space and resources immediately
before inference and check storage again after the receipt is finalized, then
release the reservation.
