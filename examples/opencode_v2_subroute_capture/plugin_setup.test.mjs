import assert from "node:assert/strict";
import test from "node:test";
import {
  createNoProviderHttpHook,
  createSyntheticRequestObserver,
  createSyntheticResponseObserver,
  SUBROUTE_URL,
} from "./observer.mjs";
import { createCapturePlugin, PLUGIN_ID } from "./plugin_setup.mjs";
import { SYNTHETIC_FIXTURE } from "./synthetic-fixtures.mjs";

function makeEvent() {
  const body = {
    model: SYNTHETIC_FIXTURE.model_alias,
    messages: [
      { role: "system", content: "synthetic-only system prompt" },
      { role: "user", content: `WRENCH_SYNTHETIC_FIXTURE:${SYNTHETIC_FIXTURE.run_id}` },
    ],
    tools: [{ type: "function", function: { name: "read_file", parameters: {} } }],
  };
  return {
    kind: "primary",
    sessionID: "synthetic-session-001",
    request: new Request(SUBROUTE_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    }),
  };
}

function makeResponseEvent() {
  return {
    kind: "primary",
    sessionID: "synthetic-session-001",
    response: new Response(JSON.stringify({
      model: "synthetic-frontier-model",
      usage: { prompt_tokens: 12, completion_tokens: 3, total_tokens: 15 },
    }), { status: 200, headers: { "content-type": "application/json" } }),
  };
}

test("disabled plugin setup registers no HTTP hook", async () => {
  let registrations = 0;
  const plugin = createCapturePlugin({ enabled: false });
  assert.equal(plugin.id, PLUGIN_ID);
  const result = await plugin.setup({
    session: {
      async hook() {
        registrations += 1;
      },
    },
  });
  assert.equal(result, undefined);
  assert.equal(registrations, 0);
});

test("setup registers the no-provider callback and disposes it once", async () => {
  const receipts = [];
  const responseReceipts = [];
  const callbacks = new Map();
  let disposeCount = 0;
  const plugin = createCapturePlugin({
    enabled: true,
    arm: "wrench",
    createObserver: createSyntheticRequestObserver,
    createResponseObserver: createSyntheticResponseObserver,
    createNoProviderHttpHook,
    createReceiptSink: (arm) => {
      assert.equal(arm, "wrench");
      return { emit: async (receipt) => receipts.push(receipt) };
    },
    createResponseReceiptSink: (arm) => {
      assert.equal(arm, "wrench");
      return { emit: async (receipt) => responseReceipts.push(receipt) };
    },
  });

  const dispose = await plugin.setup({
    session: {
      async hook(name, callback) {
        callbacks.set(name, callback);
        return {
          async dispose() {
            disposeCount += 1;
          },
        };
      },
    },
  });

  assert.deepEqual([...callbacks.keys()], ["http.request", "http.response"]);
  assert.equal(typeof callbacks.get("http.request"), "function");
  assert.equal(typeof callbacks.get("http.response"), "function");
  let downstreamHandlerCalls = 0;
  await assert.rejects(
    async () => {
      await callbacks.get("http.request")(makeEvent());
      downstreamHandlerCalls += 1;
    },
    (error) => error?.code === "provider_transport_disabled",
  );
  assert.equal(downstreamHandlerCalls, 0);
  assert.equal(receipts.length, 1);
  assert.equal(receipts[0].provider, null);
  assert.equal(receipts[0].billed_cost, null);
  assert.equal(JSON.stringify(receipts).includes("synthetic-only system prompt"), false);

  // Exercise the registered response observer directly with a synthetic
  // Response. The request hook above still blocks before transport, so this
  // test does not send a provider request.
  await callbacks.get("http.response")(makeResponseEvent());
  assert.equal(responseReceipts.length, 1);
  assert.equal(responseReceipts[0].input_tokens, 12);
  assert.equal(responseReceipts[0].output_tokens, 3);
  assert.equal(responseReceipts[0].billing_verified, false);

  await dispose();
  await dispose();
  assert.equal(disposeCount, 2);
});

test("enabled setup rejects if OpenCode has no hook registration API", async () => {
  const plugin = createCapturePlugin({
    enabled: true,
    arm: "wrench",
    createObserver: createSyntheticRequestObserver,
    createResponseObserver: createSyntheticResponseObserver,
    createNoProviderHttpHook,
    createReceiptSink: () => ({ emit: async () => {} }),
    createResponseReceiptSink: () => ({ emit: async () => {} }),
  });
  await assert.rejects(
    plugin.setup({ session: {} }),
    (error) => error instanceof TypeError && error.message === "session_http_hook_unavailable",
  );
});
