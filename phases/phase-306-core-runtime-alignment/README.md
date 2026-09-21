# Phase 306: v103 executable core alignment

The materialized v103 package's executable runtime was compared byte-for-byte
with the current repository `HEAD`:

- server, worker, prefill, mechanical router, verifier core, toolbelt, and
  wrapper entrypoints all matched
- status: `PASS_CORE_RUNTIME_ALIGNED_WITH_HEAD`
- core manifest SHA-256: `bf3d918ee104d46d2519ac2fbbcd086e0772ac344ad148489748823c850e3224`
- no tracked core source files are dirty

Receipt: `core-alignment.json`

This isolates the remaining release-candidate warning to unrelated shared
worktree dirt and publication authorization. It does not promote the artifact
to HF, and it does not prove 5060Ti current-source verification, MiniMax
parity, dense-native decoder quality, or production readiness.
