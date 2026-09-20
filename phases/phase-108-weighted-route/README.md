# Phase 108: corrected weighted mechanical-route score

The first run of the frontier-mass scorer incorrectly counted any non-`None`
return from `mechanical_route()` as mechanical coverage. That included fast
abstentions, so under-specified patch requests were falsely counted as saved
frontier work.

The scorer now counts only a concrete proposal as mechanical coverage. A
deterministic abstention is reported separately as `fast_abstain` and remains
fallback-required for the North Star savings calculation.

Against the existing 220-case diagnostic trace manifest:

- eligible cases: `120`
- concrete mechanical routes: `100`
- eligible case coverage: `85.42%`
- teacher frontier-token mass covered: `25,038,756 / 31,694,660`
- frontier-token mass coverage: `79.00%`
- read_file, read_lines, literal_search, git_read_status, health_read:
  `100%` family coverage
- patch_draft: `0/20` concrete routes in this fixture

The patch prompts in this historical fixture mostly name a file but do not
specify a requested change. Wrench now fails those closed as
`patch_content_missing` instead of inventing a diff. This is an honest gap,
not a production-value pass. The next quality work must use matched patch
traces with an actual requested edit and verify the resulting diff.

Receipt: `weighted-route-score-v2.json`.
