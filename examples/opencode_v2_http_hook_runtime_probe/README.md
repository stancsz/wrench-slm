# OpenCode v2 HTTP hook runtime probe

This bounded integration probe uses OpenCode v2.0.12 and an in-process loopback
fake OpenAI-compatible endpoint. It never contacts SubRoute, a model provider,
or the internet. The fake endpoint's token usage is test data, not provider
usage or billed usage.

Run it with a fresh output directory under
`C:\wrench-slm-data\artifacts`, after storage and resource admission:

```powershell
node examples/opencode_v2_http_hook_runtime_probe/run.mjs `
  --opencode C:\Users\stanc\.local\tools\node-v24.19.0-win-x64\node_modules\@opencode\cli\bin\opencode.exe `
  --output-dir C:\wrench-slm-data\artifacts\WRENCH-OPENCODE-HTTP-LOOPBACK-RUNTIME-VERIFY-20260929-01
```

The `block` arm asserts that a throwing request hook leaves the fake completion
endpoint at zero requests. The `observe` arm asserts that a real OpenCode
request and response traverse the hooks and that the response hook reads the
fake endpoint's usage object. Receipts mark provider and billing as unverified.
The probe does not establish usage capture for every provider, streaming mode,
WebSocket transport, retry pattern, or production billing.
