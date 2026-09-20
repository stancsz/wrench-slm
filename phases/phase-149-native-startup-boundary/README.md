# Phase 149: real native startup boundary

This phase attempted to start the current NVFP4 portable Wrench package through
the installed FreeToken daemon, not a protocol stub.

## Attempts

1. 4M KV address space, `moe-cache-size=16`, `kv-reserve-tokens=1024`, port
   `28201`: backend child failed during Torch DLL loading with `WinError 1455`
   for `nvperf_host.dll`, followed by `shm.dll` initialization failure.
2. 4M max sequence with only 65,536 KV tokens, same bounded cache, port
   `28202`: backend child failed during Torch DLL loading with `WinError 1455`
   for `cufft64_12.dll`; the detokenizer then reported OpenBLAS memory
   allocation failure.

The daemon status after both attempts was `running=false`, `pid=null`. At the
time of the attempts Windows reported only about 1.84GB free physical memory
and 2.77GB free virtual memory while the RTX 5070 Ti reported 15,797MiB of
16,303MiB in use. No process was terminated by this phase.

## Meaning

This is a real native-runtime failure, not evidence against the Wrench model's
4M tokenizer or package format. It means this host cannot currently provide a
clean native generation measurement. The next valid measurement must use a
cleaner host state or the independent 5060Ti worker, with the same package,
runtime, tokenizer, and verifier hashes.
