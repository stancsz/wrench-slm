# Phase 124: v41 frontier coverage diagnosis

The current deterministic route was joined against the existing historical
MiniMax-labelled trace manifest using the v41 route implementation and the
phase-120 fixture root.

Receipt: `current-route.json`.

- eligible case coverage: 85.4235%
- eligible frontier-token mass coverage: 78.9999%
- read_file: 100% family mass
- read_lines: 100% family mass
- literal_search: 100% family mass
- git_read_status: 100% family mass
- health_read: 100% family mass
- patch_draft: 0% family mass

The patch family is not a runtime failure. All 20 historical eligible patch
prompts omit the concrete diff or content change needed to produce a valid
review-only patch. The fail-closed route therefore preserves them for the
stronger fallback model. The verifier must not be relaxed to turn an invented
or empty diff into a mechanical accept.

This is diagnostic only. The historical trace manifest remains
`pending_human_approval`, the teacher identity is endpoint-recorded rather than
independently identity-bound, and this receipt does not establish the North
Star workflow gates.
