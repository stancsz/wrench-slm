# Phase 11: unquantized source acquisition gate

This phase performs only the guarded preflight for the official Qwen3.6
unquantized source. The checkpoint is absent from `D:\\models\\Qwen3.6-35B-A3B`.
The target drive has sufficient free space for the pinned 71.9 GB payload plus
the guard's 10 GiB headroom requirement.

The acquisition command refused to download because the operator confirmation
flag was not supplied, and it created no output directory. No network transfer
or external model mutation occurred. Structural pruning remains disabled until
the operator explicitly authorizes the download and the resulting files pass
the official-index inspection.
