import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { after, test } from "node:test";
import {
  createToolExpansionDefinition,
  createToolProfileHook,
  toolInventorySha256,
} from "./tool_profiles.mjs";
import { WRENCH_STORAGE_ROOT, WrenchRootSessionStateStore } from "./wrench_root_session_store.mjs";

const testDirectory = fs.mkdtempSync(path.join(WRENCH_STORAGE_ROOT, "artifacts", "tool-profile-store-integration-"));
const namespace = path.relative(WRENCH_STORAGE_ROOT, testDirectory).replaceAll("\\", "/");
const sessionID = "iter134-provider-free-restart-fixture";

after(() => {
  fs.rmSync(testDirectory, { recursive: true, force: true });
});

function makeTools() {
  return {
    read: { description: "Read", input: { type: "object", properties: { path: { type: "string" } } } },
    edit: { description: "Edit", input: { type: "object", properties: { path: { type: "string" } } } },
    wrench_expand_tools: createToolExpansionDefinition(),
  };
}

function makeEvent(tools) {
  return {
    agent: "build",
    model: { providerID: "wrench-subroute", id: "openrouter" },
    system: [{ type: "text", text: "system" }],
    messages: [{ role: "user", content: "Read one file" }],
    tools,
    options: {},
    sessionID,
  };
}

function makeHook(store, selectProfile) {
  const inventory = makeTools();
  return createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    profiles: [{
      id: "read-only",
      inventorySha256: toolInventorySha256(inventory),
      allowedToolNames: ["read", "wrench_expand_tools"],
    }],
    selectProfile,
    emitReceipt: async () => {},
    sessionStateStore: store,
  });
}

test("the OpenCode hook persists and restores a reviewed profile through the Wrench-root store", async () => {
  const firstStore = new WrenchRootSessionStateStore({ namespace, maxStoreBytes: 2 * 1024 * 1024, minimumFreeBytes: 0 });
  let firstSelectionCalls = 0;
  const firstHook = makeHook(firstStore, async () => {
    firstSelectionCalls += 1;
    return "read-only";
  });
  const firstEvent = makeEvent(makeTools());
  await firstHook(firstEvent);
  assert.equal(firstSelectionCalls, 1);
  assert.deepEqual(Object.keys(firstEvent.tools).sort(), ["read", "wrench_expand_tools"]);
  firstStore.close();

  const restartedStore = new WrenchRootSessionStateStore({ namespace, maxStoreBytes: 2 * 1024 * 1024, minimumFreeBytes: 0 });
  let restartedSelectionCalls = 0;
  const restartedHook = makeHook(restartedStore, async () => {
    restartedSelectionCalls += 1;
    return "read-only";
  });
  const restartedEvent = makeEvent(makeTools());
  await restartedHook(restartedEvent);
  assert.equal(restartedSelectionCalls, 0);
  assert.deepEqual(Object.keys(restartedEvent.tools).sort(), ["read", "wrench_expand_tools"]);
  restartedStore.close();
});
