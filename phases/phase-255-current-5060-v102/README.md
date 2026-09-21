# Phase 255: current v103 5060 Ti package job

This manifest is for the independent RTX 5060 Ti preflight of the current
Experimental Preview Hub revision. It is deliberately separate from the
older pending v97 job `wrench-5060ti-hf-package-20260921-01`.

- Source commit: `6d25fc8`
- Hugging Face revision: `966a1720d84b330d90b6ad38f22e883e749448f3`
- Hub repo: `stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-Experimental-Preview`
- Workload: pinned package download, structure validation, mechanical smoke,
  resource receipt, and cross-host receipt verification
- Provider spending: disabled
- Resource reserve: at least 10% host RAM and VRAM free

No result is claimed until the worker moves this exact job through the queue
and uploads a verified receipt. The local manifest is prepared, but the Drive
upload has not been verified in the current BrowserOS session.
