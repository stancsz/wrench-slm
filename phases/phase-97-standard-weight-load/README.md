# Phase 97: native backend load and 64K direct input

This phase checks the real weight-serving path separately from the bundled
mechanical endpoint.

## Results

- The ordinary workstation Python has Transformers `4.57.1`, and the FreeToken
  environment has `5.16.1`. The package's standard HF verification requires
  `5.17.0+`, so standard Transformers full-weight loading is not claimed here.
- FreeToken successfully loaded the v24 NVFP4 package and allocated the 4M
  address space. Its log reported `8.69 GiB` for the KV cache under the
  selected native profile.
- A ready native endpoint accepted a direct 64K request with HTTP 200, actual
  prompt tokens `65,470`, no truncation, and 63 generated tokens.
- End-to-end latency was `77,205.615 ms`. The server log measured decode at
  approximately `0.52 token/s` under the NVFP4 offload profile.
- The attempted `fused` MoE profile was rejected by the runtime because this
  NVFP4 artifact requires `offload` or `cpu` expert serving.

The direct-input capacity gate passes at 64K for this backend. The throughput
gate does not pass. This is the authoritative reason the native model path is
not release-ready yet, even though the model-local mechanical endpoint is fast.
