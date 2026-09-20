# Phase 98: native endpoint embedded route

This phase verifies the embedded mechanical route inside the real FreeToken
OpenAI-compatible endpoint, after fixing its stale-intent and usage-accounting
paths.

## Evidence

- The v25 package passed structural validation.
- A real FreeToken endpoint configured with a 4,000,000-token sequence limit
  accepted a 32,000,075-character raw request directly at
  `/v1/chat/completions`.
- The response reported `prompt_tokens=4,000,010`, preserved the newest intent,
  returned the expected `read_file` proposal, and made `model_calls=0`.
- The request completed in `454.852 ms`, including HTTP transport and JSON
  parsing. The native model was loaded in the same process, but the mechanical
  route intentionally avoided generation.

This closes the previous accounting defect where the native embedded route
reported `prompt_tokens=0`. It proves the direct model endpoint can accept and
account for a 4M raw payload while taking the fast mechanical path. It does not
prove native dense attention quality, learned retrieval quality, MiniMax parity,
or fast generation for ambiguous requests. The separate 64K native generation
probe took `77,205.615 ms` under NVFP4 expert offload.
