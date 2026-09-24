# Prompt serializer input mutation guard

Goal: [E0 serialized prompt budget gate](../../goal/wrench-e0-serialized-prompt-gate/GOAL.md)
Task: protect the prepared-message identity across serializer callbacks
Worker: root orchestrator
Job: `W2-NS-E0-SERIALIZER-MUTATION-20260925`

## Change

`compile_prompt` gives the serializer a recursively read-only JSON-shaped copy
of its bounded message list. Attempts to edit mappings or sequences raise a
tracked mutation error. The gate returns `SERIALIZER_MUTATED_INPUT` with no
routable prompt, prompt digest, or context insertion identity, including when
the callback catches the mutation exception and returns normally.

The serializer receives a recursive copy, so its writes cannot alter the
compiler-owned message whose digest was recorded. Ordinary Python mutation
methods on the supplied copy are rejected and recorded, even if the callback
catches the exception. A callback can bypass those overrides with unbound
`dict` or `list` base methods, which mutate only its private copy. More
fundamentally, a callback can return any bytes regardless of its input. The
gate therefore does not prove that arbitrary serializer output represents
the digest-bound messages or matches a downstream runtime.

## Verification

The focused evaluation records four relevant suites, the corrected scratch
setup, final source/test hashes, and limitations.
