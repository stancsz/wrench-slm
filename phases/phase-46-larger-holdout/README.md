# Phase 46: larger 16E adaptive holdout after intent guards

The prior larger 16E text-only NVFP4 artifact was loaded through the working
CUDA FreeToken environment after both request-intent guards were added. On the
same 14-case family-disjoint holdout it accepted 7/14 cases, matched 12/14
expected outcomes, and produced zero prohibited accepts.

This confirms that the destructive-intent guard did not regress the larger
tier's corrected holdout result. It remains a synthetic local evaluation, not
real-workflow value or production evidence. The full receipt is
`runtime-16e-adaptive-holdout-v3.json`.
