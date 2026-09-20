# Phase 109: bounded mechanical patch route

Wrench now handles a small review-only text-edit portfolio mechanically when
the request is explicit and the match is unique:

- replace one quoted string with another
- append one quoted line
- prepend one quoted line
- insert one quoted line after one quoted anchor
- remove one quoted string

The route reads the file, constructs a unified diff, and never writes it.
Repeated matches, missing files, ambiguous instructions, and under-specified
patch requests remain fallback or abstention cases. The independent verifier
now accepts valid addition-only and deletion-only unified diffs, while still
rejecting header-only or empty diffs.

Evidence:

- source route commit: `be7eb63`
- addition-only verifier fix: `1e0027b`
- full tests: `128 passed, 10 warnings`
- v11 package: `PASS_STRUCTURAL_PACKAGE`
- package append integration: accepted, review-only, `mutated=false`
- package 4M route: `4,000,000` requested tokens, `10.965 ms`, `0` model calls
- public HF revision: `c2e8150b05dca0327fee00cd675f08ee084a616d`

This improves practical mechanical coverage but does not prove the 90% weighted
frontier-token target. The historical 220 fixture still has under-specified
patch prompts, and matched MiniMax workflow evidence remains required.
