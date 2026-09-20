# Phase 161: package-local exact patch retrieval

The package-local worker now recovers an exact unified diff from older
reference text when the newest intent asks for an unapplied review-only patch.
The route requires matching paths, a valid hunk, bounded diff size, and an
existing file. Missing or ambiguous patch content still abstains.

Evidence:

- `pytest -q`: full repository regression passed.
- `phase-161-reference-patch-package-validation.json`: fresh v64 package
  structural validation passed with no errors.
- Fresh v64 package smoke accepted the recovered `patch_draft` and reported
  `applied=false`.

Package source:
`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v64-reference-patch-docs`

This proves package-local retrieval behavior, not MiniMax parity or the
90%/95% workflow gates.
