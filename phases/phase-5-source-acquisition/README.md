# Phase 5: guarded source acquisition

The official unquantized source is 26 safetensor shards totaling
71,903,645,408 bytes. This phase is intentionally a guarded operator action.

The command refuses to run unless the exact official revision is selected, at
least the recorded byte count is expected, there is an additional 10 GiB of
free space, and the operator passes `--confirm-71gb`:

```powershell
py -3 tools/acquire_qwen_source.py `
  --output D:\models\Qwen3.6-35B-A3B `
  --confirm-71gb
```

After acquisition, run the Phase 1 inspector against the new directory and
compare the resulting configuration and shard index to
`phases/phase-3-source-feasibility/official-source.json`. No pruning command
is valid until those checks pass.
