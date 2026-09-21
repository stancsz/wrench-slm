# Phase 247: compact v97 DeepSeek Harness integration

Status: DeepSeek Harness local smoke passed on the RTX 5070 Ti development
host. Claude Code current-v97 routing is not accepted as evidence in this
phase because the installed CLI continued to use its first-party provider
despite the local endpoint variables, and no Wrench trace was received.

## DeepSeek Harness result

The current compact NVFP4 v97 package was connected to the real `dsh --profile
headless` client with a temporary v97 patch overlay. The client:

1. issued the session-title preflight;
2. sent its multi-user-role wrapper bundle to Wrench;
3. received a structured `read` proposal for `README.md`;
4. executed the local read tool and returned the tool result;
5. received Wrench's deterministic settlement and final text.

The Wrench trace records `mechanical_fast_path=true`,
`embedded-mechanical-settlement`, zero model calls, and a 4M raw context
limit. No repository file was edited.

## Claude Code boundary

Two isolated attempts were deliberately not promoted. The CLI returned
first-party `claude-sonnet-5` usage and a nonzero provider cost, while the
v97 Wrench trace stayed empty. This means the local endpoint injection was not
effective for this installed CLI configuration. No further Claude attempts
were made. The older v94 Claude receipt remains historical evidence only.

This phase is not independent RTX 5060 Ti evidence, learned MiniMax parity,
dense-native decoder quality, or production authorization.

Evidence:

- `receipt.json`
- `compact-v97-dsh-trace.jsonl`
- `dsh-v97.patch.yml`
