# Patch-draft screen 01 follow-up

Date: 2026-09-25 (America/Edmonton)

After the failed [screen 01](patch-draft-screen-01.md), commit `21b25c3` fixed
two deterministic route defects exposed by its cases:

- The parser and review-only boundary now both recognize the `replacing`
  inflection.
- Insert-after generation no longer adds a blank line before an existing
  suffix. Multiline anchors now fall back rather than producing an ambiguous
  insertion.

The focused route and worker suite passed **33 tests** in 1.58 seconds. This
was implementation verification, not a repeat of screen 01. Its failure
remains the measured result; no patch-draft work family is accepted. Any next
measurement needs a separately frozen protocol and must remain open-development
evidence because the initial cases informed this repair.

The generic executor still accepts structurally plausible patch text without
proving the hunk applies to the source or that diff paths equal the proposal's
file list. Exact source-bound validation remains a separate gate for
model-authored or caller-supplied patch proposals.
