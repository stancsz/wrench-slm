# Phase 43: live artifact re-verification

The current external quantized artifacts were re-read from `D:\models` and
their manifests were checked again. The compact safety-calibrated 8E tier is
3,423,498,186 directory bytes, 3,402,495,976 packed weight bytes, and
3,881,244,016 parameters. The larger 16E tier is 3,991,755,140 directory
bytes, 3,970,041,576 packed weight bytes, and 4,888,532,336 parameters.

Both are actual W4A16 NVFP4 text-only artifacts with eight routed experts per
token. The catalog still marks them experimental, and the larger safety
candidate remains unpromoted because task acceptance regressed. The receipt is
`catalog.json`.
