# OpenCode session ID grammar audit

Job: `W2-NS-OC-SESSION-ID-FIX-20260924`

Nonce: `OCSFIX-A117`

OpenCode source pin: `v2.0.15`, commit `6f3639d82ed0760091792189b78f8eeb44f699b1`

## Decision

The local source-audit evidence does not establish a complete OpenCode session
ID grammar. The resolver and its fixtures are unchanged by this audit. No
suffix character class or regular expression is inferred from the `ses`
prefix.

## Evidence inspected

- `docs/goal/wrench-e0-opencode-context-adapter/GOAL.md` says the IDs must
  satisfy the pinned `ses` prefix and that fixtures cover the prefix. It does
  not state a suffix grammar.
- `docs/reports/wrench-e0-opencode-context-adapter/session-root-resolution.md`
  says the pinned schema provides a session `id` and records an exact ID
  match, but does not transcribe the ID schema's validation rule.
- `docs/evals/wrench-e0-opencode-context-adapter/review.md` confirms the
  tagged session fields and exact ID matching, without recording a complete
  ID pattern.
- The goal links the pinned session schema at
  `packages/schema/src/session.ts`; the schema content or its ID declaration
  is not stored in the inspected local audit evidence.

The current resolver accepts strings beginning with `ses`, subject to its
length and control-character checks. That is only a prefix check. It cannot be
described as full schema validation. The current fixtures use IDs such as
`ses_fixture123`, but those fixtures do not prove that their suffix form is
accepted by the pinned schema, nor identify a malformed suffix that the schema
rejects.

## Follow-up evidence needed

Before tightening the resolver, preserve the exact `SessionID` declaration or
equivalent validator from the pinned v2.0.15 schema, including any delegated
identifier implementation and tests that define accepted suffixes. Then add
source-supported valid and invalid fixture IDs. Until that is recorded, the
current prefix behavior remains a provisional boundary and must not be treated
as complete session ID validation.

## Scope

Read-only evidence inspection only. No resolver or test edits, tests, OpenCode
client, provider/model calls, network access, dependency installs, or data
capture were performed. Checkout HEAD at inspection was
`790207428ac58a96c93c4a2be8a29596b943248a`, later than the task's stated base
`405f72e`; existing user changes were preserved.
