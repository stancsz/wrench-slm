# Phase 297: fresh 5060Ti thread returned no execution evidence

After phase 296 bundled a complete current teacher receipt into `origin/main`,
a new same-directory remote thread was forked from the previously functioning
5060Ti task. The new thread received a self-contained payload requiring
`origin/main` at or after `77fdf44`, the current 220-case hash, the bundled
teacher receipt hash, exact replay commands, host identity, and 10% RAM/VRAM
reserve checks.

The remote task completed after 40.762 seconds with status `idle`, but the
completed turn contained no assistant message, no command execution, no
preflight output, and no external receipt. The remote host and thread IDs are
recorded in `fresh-thread-receipt.json`.

This is a control-plane failure, not a benchmark result. The new teacher input
is now present in the repository and locally validated, so the missing-input
condition is removed. The remaining 5060Ti gap is an authenticated remote
execution receipt from `DESKTOP-KET1SKP`; no claim is promoted from this empty
turn.
