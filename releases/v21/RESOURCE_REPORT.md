# Wrench-Pro v21 resource report

Measurements are from the packaged runtime on Windows 11 with an NVIDIA
GeForce RTX 5070 Ti and CUDA.

| Measurement | Observed value |
| --- | ---: |
| Fresh environment package load | 2.4463 to 2.5089 s |
| Quickstart first prediction | 1.8946 to 2.0909 s |
| Quickstart warm prediction | 1.3854 to 1.4741 s |
| Peak CUDA allocated | 1,076,785,152 bytes |
| Peak CUDA reserved | 1,153,433,600 bytes |
| Process-tree RSS | 1,858,539,520 to 1,890,676,736 bytes |
| Context suite p50 prediction | 1.1653 s |
| Context suite p95 prediction | 2.5747 s |
| Final holdout p50 prediction | 1.1754 s |
| Final holdout p95 prediction | 2.4662 s |

The process-tree values sum launcher and descendant RSS samples and may count
shared pages more than once. The ranges are observations from two final clean
verifier runs on one machine, not limits or service objectives. The package requires the approximately
988,097,824-byte pinned base weight plus the adapter and tokenizer files.
CPU availability is a functional option only; CPU latency and capacity were
not qualified for release claims.

The clean-environment receipt is
`artifacts/model-release/v21-release-verifier-final2/receipt.json` in the
repository.
