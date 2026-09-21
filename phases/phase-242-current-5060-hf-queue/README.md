# Phase 242: direct Hugging Face 5060 Ti preflight

This queue item makes the worker download the public Wrench package directly
from Hugging Face at a pinned revision. It validates the package with the
current source tools, runs the bounded mechanical smoke, and records host RAM
and VRAM reserve checks before and after download.

This is an independent package and runtime preflight. It does not claim
MiniMax parity, dense-native 4M attention quality, retrieval quality, or
production readiness. The Hugging Face revision is the public NVFP4 package
currently available on the Hub, not the newer local v97 dense-native package.
