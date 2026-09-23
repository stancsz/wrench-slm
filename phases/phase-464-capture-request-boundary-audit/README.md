# Phase 464: capture request-boundary audit

Date: 2026-09-23

## Scope

Read-only inspection of the Lean Router capture-writer source to determine
whether captured `prompt` fields identify an atomic current user request. No
capture rows, prompt text, context text, credentials, or provider data were
read. No replay, training, or provider call was made.

## Source identity

- Source: `C:\Users\stanc\github\lean-router\src\core\wrench_replay_capture.py`
- SHA-256: `96B83D50702D46F4DC233592DB2BC5835568BB65515FDC6686A012990D517AEE`
- Candidate capture: SHA-256 `3c6e1e549a57d8b02ff20f5dcc27d061766050fa862d542808d9b381387420fe`, as recorded in Phase 448.

## Findings

- The writer selects the last non-empty item whose role is `user` from the
  request's `messages` or list-form `input` and stores its text in `prompt`.
- It places the other message items, system/instructions, model, tool schemas,
  and tool choice in `context`.
- For string-form `input`, the whole string becomes `prompt`.
- The writer does not split a selected user message into a latest request and
  any quoted or serialized conversation history inside that message. Thus the
  `prompt` field is a transport-level user message, not a validated atomic
  task. Locator matches in prompt/context fields cannot by themselves identify
  current requests or Wrench-eligible work.
- The writer's deterministic redactor is limited to configured secret patterns
  and secret-like keys. Its `capture_redaction.status=complete` field does not
  certify general personal-data removal.

## Authorization and readiness

The owner has explicitly approved local review and preparation of this
hash-bound source, including the current instruction to proceed. This is owner
authorization only. It does not supply an independent rights, license, or
third-party consent receipt. Phase 448's privacy flags, lack of independent
task/verifier outcomes, and incomplete accounting remain unresolved. The
capture therefore remains ineligible for training and paired replay.

## Next useful step

If rights and consent evidence becomes available, review candidate rows under
an approved privacy protocol and join independent final-task and verifier
outcomes before preparing any replay workload. Keep raw prompt/context values
out of reports and manifests.
