# Phase 322: current-head portable package binding

The portable package was rematerialized after commit `04090c1` so the native
verifier's Windows process-tree cleanup fix is included in the downloaded
artifact.

## Result

- Package: `D:\models\_wrench-release-candidate-04090c1`
- Materialization: `MATERIALIZED_PACKAGE_RUNTIME_EMBEDDED`
- Structural validation: `PASS_STRUCTURAL_PACKAGE`
- Bundled verifier: present
- Bundled cleanup fix: present
- Model and tokenizer bytes remain identical to the phase-321 tested package

This package is the current portable candidate binding for the next native,
4M direct-input, and 5060 Ti verification pass. It is not a publication or
production approval.

Evidence: `phases/phase-322-current-head-package-validation.json`.
