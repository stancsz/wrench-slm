import assert from "node:assert/strict";
import test from "node:test";
import {
  createNoProviderHttpHook,
  createSyntheticRequestObserver,
  createSyntheticResponseObserver,
  MAX_RESPONSE_BYTES,
  syntheticJsonSha256,
  SyntheticCaptureError,
  SUBROUTE_URL,
} from "./observer.mjs";
import { SYNTHETIC_FIXTURE } from "./synthetic-fixtures.mjs";

function makePayload({ marker = `WRENCH_SYNTHETIC_FIXTURE:${SYNTHETIC_FIXTURE.run_id}`, history = [] } = {}) {
  return {
    model: SYNTHETIC_FIXTURE.model_alias,
    messages: [
      { role: "system", content: "synthetic-only system prompt" },
      ...history,
      { role: "user", content: marker },
    ],
    tools: [{ type: "function", function: { name: "read_file", parameters: {} } }],
  };
}

function makeEvent({
  url = SUBROUTE_URL,
  kind = "primary",
  marker = `WRENCH_SYNTHETIC_FIXTURE:${SYNTHETIC_FIXTURE.run_id}`,
  history = [],
  rawBody,
} = {}) {
  const payload = makePayload({ marker, history });
  const request = new Request(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: rawBody ?? JSON.stringify(payload),
  });
  return { request, kind, sessionID: "synthetic-session-001" };
}

function makeResponseEvent({ kind = "primary", rawBody, contentType = "application/json" } = {}) {
  const body = rawBody ?? JSON.stringify({
    id: "synthetic-response-001",
    model: "synthetic-frontier-model",
    choices: [{ message: { content: "synthetic answer" } }],
    usage: {
      prompt_tokens: 42,
      completion_tokens: 8,
      total_tokens: 50,
      prompt_tokens_details: { cached_tokens: 12 },
    },
  });
  return {
    kind,
    sessionID: "synthetic-session-001",
    response: new Response(body, {
      status: 200,
      headers: { "content-type": contentType },
    }),
  };
}

function makeObserver(overrides = {}) {
  const receipts = [];
  const observe = createSyntheticRequestObserver({
    enabled: true,
    arm: "wrench",
    state: { sessionID: null },
    emit: async (receipt) => receipts.push(receipt),
    ...overrides,
  });
  return { observe, receipts };
}

function makeResponseObserver(overrides = {}) {
  const receipts = [];
  const observe = createSyntheticResponseObserver({
    enabled: true,
    arm: "wrench",
    state: { sessionID: "synthetic-session-001" },
    emit: async (receipt) => receipts.push(receipt),
    ...overrides,
  });
  return { observe, receipts };
}

test("reviewed fixture digest is bound to the exact synthetic request", () => {
  assert.equal(
    syntheticJsonSha256(makePayload()),
    SYNTHETIC_FIXTURE.normalized_request_sha256,
  );
});

test("disabled observer is inert", async () => {
  const observe = createSyntheticRequestObserver({ enabled: false });
  const result = await observe(makeEvent());
  assert.deepEqual(result, { captured: false, reason: "disabled" });
});

test("captures content-free metadata and leaves request body intact", async () => {
  const { observe, receipts } = makeObserver();
  const event = makeEvent();
  const originalBytes = new Uint8Array(await event.request.clone().arrayBuffer());
  const result = await observe(event);
  const afterBytes = new Uint8Array(await event.request.clone().arrayBuffer());
  const receiptText = JSON.stringify(receipts);

  assert.equal(result.captured, true);
  assert.equal(receipts.length, 1);
  assert.equal(receipts[0].route_identity, SUBROUTE_URL);
  assert.equal(receipts[0].model_alias, SYNTHETIC_FIXTURE.model_alias);
  assert.equal(receipts[0].fixture_id, SYNTHETIC_FIXTURE.fixture_id);
  assert.equal(receipts[0].pair_id, SYNTHETIC_FIXTURE.pair_id);
  assert.equal(receipts[0].arm, "wrench");
  assert.equal(receipts[0].body_bytes, originalBytes.byteLength);
  assert.equal(receipts[0].tool_schema_count, 1);
  assert.equal(receipts[0].input_tokens, null);
  assert.equal(receipts[0].provider, null);
  assert.equal(receipts[0].billed_cost, null);
  assert.equal("request_sha256" in receipts[0], false);
  assert.equal("session_id_sha256" in receipts[0], false);
  assert.deepEqual(afterBytes, originalBytes);
  assert.equal(receiptText.includes("synthetic-only system prompt"), false);
  assert.equal(receiptText.includes(`WRENCH_SYNTHETIC_FIXTURE:${SYNTHETIC_FIXTURE.run_id}`), false);
});

test("refuses wrong route, non-primary, mismarked, historical, and changed templates", async () => {
  const { observe, receipts } = makeObserver();
  const cases = [
    makeEvent({ url: "http://127.0.0.1:4000/v1/responses" }),
    makeEvent({ kind: "title" }),
    makeEvent({ marker: "real user task text" }),
    makeEvent({ history: [{ role: "assistant", content: "previous turn" }] }),
    makeEvent({ rawBody: JSON.stringify({ ...makePayload(), temperature: 0.1 }) }),
  ];
  for (const event of cases) await assert.rejects(observe(event), SyntheticCaptureError);
  assert.equal(receipts.length, 0);
});

test("refuses duplicate JSON keys that could mask non-synthetic content", async () => {
  const { observe, receipts } = makeObserver();
  const marker = `WRENCH_SYNTHETIC_FIXTURE:${SYNTHETIC_FIXTURE.run_id}`;
  const rawBody =
    `{"model":"openrouter","messages":[{"role":"user","content":"real task"}],` +
    `"messages":[{"role":"user","content":"${marker}"}]}`;
  await assert.rejects(observe(makeEvent({ rawBody })), (error) =>
    error instanceof SyntheticCaptureError && error.code === "duplicate_json_key",
  );
  assert.equal(receipts.length, 0);
});

test("rejects oversized bodies before emitting a receipt", async () => {
  const { observe, receipts } = makeObserver();
  const request = new Request(SUBROUTE_URL, {
    method: "POST",
    headers: { "content-length": "1048577" },
    body: "x".repeat(1_048_577),
  });
  await assert.rejects(observe({ request, kind: "primary", sessionID: "synthetic-session-001" }), (error) =>
    error instanceof SyntheticCaptureError && error.code === "request_body_too_large",
  );
  assert.equal(receipts.length, 0);
});

test("no-provider hook rejects the mock event before its caller proceeds", async () => {
  const { observe, receipts } = makeObserver();
  const hook = createNoProviderHttpHook(observe);
  await assert.rejects(hook(makeEvent()), (error) =>
    error instanceof SyntheticCaptureError && error.code === "provider_transport_disabled",
  );
  assert.equal(receipts.length, 1);
  await assert.rejects(hook(makeEvent()), (error) =>
    error instanceof SyntheticCaptureError && error.code === "request_count_limit",
  );
});

test("captures bounded response usage while preserving the one-shot response", async () => {
  const { observe, receipts } = makeResponseObserver();
  const event = makeResponseEvent();
  const before = await event.response.clone().text();
  const result = await observe(event);
  const after = await event.response.clone().text();
  assert.equal(result.captured, true);
  assert.equal(receipts.length, 1);
  assert.equal(receipts[0].input_tokens, 42);
  assert.equal(receipts[0].output_tokens, 8);
  assert.equal(receipts[0].total_tokens, 50);
  assert.equal(receipts[0].cached_input_tokens, 12);
  assert.equal(receipts[0].response_model, "synthetic-frontier-model");
  assert.equal(receipts[0].provider, null);
  assert.equal(receipts[0].billed_cost, null);
  assert.equal(receipts[0].billing_verified, false);
  assert.deepEqual(after, before);
  assert.equal(JSON.stringify(receipts).includes("synthetic answer"), false);
  await assert.rejects(observe(makeResponseEvent()), (error) => error.code === "response_count_limit");
});

test("extracts usage only from the final OpenAI-compatible SSE chunk", async () => {
  const { observe, receipts } = makeResponseObserver();
  const stream = [
    'data: {"id":"chunk-1","model":"synthetic-frontier-model","choices":[{"delta":{"content":"secret answer"}}]}',
    "",
    'data: {"id":"chunk-2","model":"","choices":[],"usage":{"prompt_tokens":42,"completion_tokens":8,"total_tokens":50,"prompt_tokens_details":{"cached_tokens":12}}}',
    "",
    "data: [DONE]",
    "",
  ].join("\n");
  await observe(makeResponseEvent({ rawBody: stream, contentType: "text/event-stream" }));
  assert.equal(receipts.length, 1);
  assert.equal(receipts[0].input_tokens, 42);
  assert.equal(receipts[0].output_tokens, 8);
  assert.equal(receipts[0].response_model, "synthetic-frontier-model");
  assert.equal(JSON.stringify(receipts).includes("secret answer"), false);
});

test("response hook fails closed on absent usage, duplicate keys, wrong kind, and oversized body", async () => {
  const missingUsage = makeResponseObserver();
  await assert.rejects(
    missingUsage.observe(makeResponseEvent({ rawBody: JSON.stringify({ model: "m", choices: [] }) })),
    (error) => error.code === "provider_usage_missing",
  );
  assert.equal(missingUsage.receipts.length, 0);

  const missingStreamUsage = makeResponseObserver();
  await assert.rejects(
    missingStreamUsage.observe(makeResponseEvent({
      rawBody: 'data: {"model":"synthetic-frontier-model","choices":[]}\n\ndata: [DONE]\n\n',
      contentType: "text/event-stream",
    })),
    (error) => error.code === "provider_usage_missing",
  );
  assert.equal(missingStreamUsage.receipts.length, 0);

  const duplicate = makeResponseObserver();
  await assert.rejects(
    duplicate.observe(makeResponseEvent({ rawBody: '{"model":"m","usage":{},"usage":{}}' })),
    (error) => error.code === "duplicate_json_key",
  );
  assert.equal(duplicate.receipts.length, 0);

  const wrongKind = makeResponseObserver();
  await assert.rejects(
    wrongKind.observe(makeResponseEvent({ kind: "title" })),
    (error) => error.code === "response_kind_refused",
  );
  assert.equal(wrongKind.receipts.length, 0);

  const wrongSession = makeResponseObserver();
  await assert.rejects(
    wrongSession.observe({ ...makeResponseEvent(), sessionID: "different-session" }),
    (error) => error.code === "response_session_mismatch",
  );
  assert.equal(wrongSession.receipts.length, 0);

  const oversized = makeResponseObserver();
  await assert.rejects(
    oversized.observe(makeResponseEvent({ rawBody: "x".repeat(MAX_RESPONSE_BYTES + 1) })),
    (error) => error.code === "response_body_too_large",
  );
  assert.equal(oversized.receipts.length, 0);
});

test("refuses malformed observer configuration", () => {
  assert.throws(
    () => createSyntheticRequestObserver({ enabled: true, arm: "frontier", emit() {} }),
    SyntheticCaptureError,
  );
  assert.throws(() => createNoProviderHttpHook(null), SyntheticCaptureError);
});
