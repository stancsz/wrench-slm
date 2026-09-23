# Unsealed classifier training expansion

**Superseded for training.** A later file-size audit found at least 72
`accepted` examples whose stated byte cap was smaller than the substituted
file. The path substitution did not preserve the original label's verifier
outcome. Heads trained on this expansion remain useful as failed experiments,
but their calibration accuracy is not valid quality evidence. The corrected
[policy contrasts](../system-one-policy-contrasts-v3-20260922/README.md)
and the original unsealed calibration rows are the active training inputs.

`train-extra.jsonl` has 1,030 examples derived from the 118 authored contrast
examples in the preceding phase. The generator substitutes 12 distinct
tracked repository paths that are absent from the 5,600-case test suite's path
inventory. The intended contrast label was copied across substitutions, which
caused the file-size error above. The binary labels are stored as
`accepted` and `abstain` for the existing trainer. No examples are sourced
from the 60-case independent set or the sealed final split.

The [manifest](manifest.json) pins the source and expanded file hashes, label
counts and substitution paths. A separate audit found zero exact prompt
overlap with the 5,600-case suite. Path substitution increases surface
variety; it does not produce independent real user workflows. Do not use this
file for future fitting or calibration.
