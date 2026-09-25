# Whole-line removal mechanics proposal

Date: 2026-09-25 (America/Edmonton)

## Screen 02 wording decision

Screen 02 remains a failed exact-oracle screen. Its prompt says to remove the
unique setting `legacy=off` from a line-oriented settings file. The phrase is
somewhat ambiguous by itself, but ordinary task semantics support the frozen
whole-line target because a setting is a complete record. The source route
removed only the quoted substring and kept its newline. The oracle is
defensible, so the observed mismatch remains a real failure. The new screen
uses explicit whole-line wording and different paths, values and target bytes.
Because screen 02 exposed this behavior, the new screen is open-development
mechanics evidence, not a holdout.

## Proposed narrow measurement

The source route now recognizes `remove the entire line containing <quoted
text> from|in <path>`. It removes one uniquely matching line, preserving all
other UTF-8 LF bytes, and abstains with `patch_target_not_unique` when zero or
multiple lines match. Existing generic quoted-text removal retains its
substring semantics.

The draft protocol freezes three new positive cases at first, middle and final
line positions, plus six boundaries for duplicate and missing targets,
unterminated and CRLF files, an explicitly missing file, and an outside-root
path. Exact independent diff/application, deep verifier pass, review-only
metadata, fixture immutability, exact boundary reasons and zero runtime errors
are required for every case. This measures only explicit whole-line removal
mechanics. It cannot accept general patch drafting or establish production
utility or frontier savings.

## Execution status

Protocol and runner are freeze-ready. No test, screen, model, tokenizer,
client, provider, network or training job was run by this workstream. The
measurement requires a fresh storage `status` and a separate 8,000,000-byte
reservation under `LOCAL-PATCH-WHOLE-LINE-SCREEN-20260925-01`, plus C: free-
space and RAM/VRAM reserve checks. Execute only against the committed protocol
and runner at the frozen revision.
