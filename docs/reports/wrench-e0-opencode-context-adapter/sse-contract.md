# OpenCode-compatible Chat Completions SSE encoder contract

Job: `W2-NS-OPENCODE-SSE-CONTRACT-20260924`
Nonce: `OSC-1D7B`
Repository base: `c1342ef`
Status: socket-free encoder fixture added; focused server suite passed

## Outcome

Check that Wrench's existing `_completion_stream_chunks` encoder emits the
role, content, stop, and terminal `[DONE]` events expected by the pinned
OpenCode v2.0.15 OpenAI-compatible Chat Completions path. The adjacent
[request-lowering source audit](request-lowering-source-audit.md) pins the
OpenCode source tag and describes its request-lowering limits. The
[mock-runtime preflight](mock-runtime-preflight.md) identifies the installed
configuration's Chat Completions route and records the tagged OpenAI Chat
stream schema references and canned SSE contract.

## Change and acceptance

`tests/test_wrench_server.py` now has a pure fixture test that calls
`_completion_stream_chunks` directly with one synthetic, non-tool completion.
It checks four correctly framed SSE events: an assistant role delta, the
synthetic content delta, an empty delta with `finish_reason: "stop"`, and the
terminal `data: [DONE]` event. The test does not open a socket or invoke
OpenCode.

The production encoder in `src/wrench_harness/server.py` was not changed. No
incompatibility was found for this non-tool success shape. Malformed completion
objects and empty message content are outside this fixture's coverage.

## Verification

The focused suite passed with the provisioned Python 3.11.16 interpreter and
cached pytest 8.4.2. No packages were installed.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONPATH='C:\Users\stanc\github\wrench-slm\src;C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -q -p no:cacheprovider --basetemp='C:\wrench-slm-data\tmp\W2-NS-OPENCODE-SSE-CONTRACT-20260924' tests/test_wrench_server.py
```

Result: **18 passed in 9.39s**. `git diff --check` passed; Git emitted only its
usual LF-to-CRLF conversion warning for the edited test file.

SHA-256 identities at review time:

- `src/wrench_harness/server.py`: `7333e43eb0000181cd269eb613d9d6318086d96238d1df487006e503a7483082`
- `tests/test_wrench_server.py`: `76bbb63552d936e134e6fa6f5a604f13a3cde0544ba6bb7cd4729008d3621759`

Storage status after the focused run was `WITHIN_LIMIT`: actual
2,286,910,647 bytes, active reservations 20,103,000 bytes, projected
2,307,013,647 bytes, and 47,692,986,352 bytes of headroom. Pytest's scratch
tree under the admitted job path contained 9 files totaling 755 bytes at that
check. The existing `uv.lock` and other concurrent worktree changes were
preserved.

## Limits

This is source-contract and fixture evidence for the encoder's local output.
The new test itself is socket-free, although other existing tests in
`tests/test_wrench_server.py` use ephemeral loopback servers. No OpenCode
process, request, port 4000/43117 access, provider, or model was used. Passing
this unit test does not establish installed-client parsing, successful route
selection, transport behavior, context-hook enforcement, or full E0 acceptance.

The next transport characterization remains separately gated by the existing
[mock-runtime preflight](mock-runtime-preflight.md), including its confinement
and authorization requirements.
