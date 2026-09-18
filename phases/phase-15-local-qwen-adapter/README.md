# Phase 15: bounded local Qwen adapter

This phase adds a standard-library client for the local FreeToken OpenAI-style
endpoint. It permits only localhost HTTP `/v1/chat/completions`, rejects
redirects and remote endpoints, bounds token and response sizes, checks the
returned model identity, and routes response content through the strict Phase
14 parser.

The integration test uses a local mock server and verifies accepted proposal
execution plus remote-endpoint rejection. It does not spend provider budget or
claim Qwen task quality.
