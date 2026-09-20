# Phase 163: public v66 launcher repair

The portable package was rebuilt after fixing the Windows FreeToken command
wrapper default and was published to the existing Hugging Face repository.

Evidence:

- Fresh v66 package structural validation: `PASS_STRUCTURAL_PACKAGE` with no
  errors.
- Package-local exact reference patch smoke: `patch_draft`, `applied=false`,
  `backend=embedded-mechanical`.
- Public Hub revision:
  `ffa6bce60508e34cb4db59ccdf434576e67955e3`.
- Fresh download hashes match local v66 for `serve_freetoken.ps1` and
  `wrench_mechanical.py`.
- Fresh download contains `FreeTokenExecutable = "ft.cmd"` and
  `reference_patch_route`.

This publishes the launcher repair and package-local retrieval behavior. It
does not claim native dense 4M generation or MiniMax workflow parity.
