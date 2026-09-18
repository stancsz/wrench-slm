# Phase 54: ideal INT4 versus actual packed size

The structural parameter counts imply ideal half-byte weight payloads of about
1.81 GiB for 8E and 2.28 GiB for 16E. The live text-only NVFP4 artifacts are
larger because the packed format includes scaling and quantization metadata,
non-expert tensors, model indexes, and runtime files.

The verified packed weights are 3.169 GiB for 8E and 3.697 GiB for 16E. Their
full text-only directories are 3.188 GiB and 3.718 GiB. Both therefore meet
the practical 3–4 GiB artifact target, but neither should be described as the
ideal payload estimate.
