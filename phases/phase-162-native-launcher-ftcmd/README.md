# Phase 162: native launcher executable and host-resource evidence

The portable native launcher default now uses `ft.cmd`, matching the current
Windows FreeToken installation. The previous `ft.exe` default failed before
FreeToken startup because only the command wrapper was installed.

Evidence:

- Materializer regression: `5 passed`.
- Fresh v65 package structural validation: `PASS_STRUCTURAL_PACKAGE`.
- Native launcher reached FreeToken and parsed the requested 4M settings:
  `max_seq_len_override=4000000`, `num_token_override=4000000`,
  `num_tokenizer=0`, and `expert_load=serial`.
- Native generation did not start. The host reported Windows `WinError 1455`
  while loading `cublas64_13.dll`, followed by CUDA OOM while allocating 490 MiB
  with about 1.31 GiB free on the RTX 5070 Ti.
- After launcher cleanup, ports 28960 and 28961 had no remaining listener.

This is a host-resource blocker for the native-direct probe, not evidence of
native long-context quality. The package-local MapReduce path remains the
practical long-context lane.
