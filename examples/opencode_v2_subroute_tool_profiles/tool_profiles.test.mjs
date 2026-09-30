import assert from "node:assert/strict";
import test from "node:test";

import {
  createToolExpansionDefinition,
  createToolProfileHook,
  createToolProfilePlugin,
  toolInventorySha256,
} from "./tool_profiles.mjs";

function makeTools() {
  return {
    read: {
      description: "Read a file",
      input: { type: "object", properties: { path: { type: "string" } } },
    },
    edit: {
      description: "Edit a file",
      input: { type: "object", properties: { path: { type: "string" } } },
    },
    grep: {
      description: "Search files",
      input: { type: "object", properties: { query: { type: "string" } } },
    },
  };
}

function makeProfile(tools, allowedToolNames = ["read"]) {
  return {
    id: "read-only",
    inventorySha256: toolInventorySha256(tools),
    allowedToolNames,
  };
}

function makeSessionTools() {
  return {
    ...makeTools(),
    wrench_expand_tools: createToolExpansionDefinition(),
  };
}

function makeSessionEvent(tools, sessionID = "session-1") {
  return { ...makeEvent(tools), sessionID };
}

function makeSessionStateStore({ failSet = false } = {}) {
  const records = new Map();
  const claims = new Set();
  return {
    records,
    async get(key) {
      const value = records.get(key);
      return value === undefined ? undefined : structuredClone(value);
    },
    async set(key, value) {
      if (failSet) throw new Error("storage unavailable");
      records.set(key, structuredClone(value));
    },
    async claim(key, capacity) {
      if (claims.has(key)) return "existing";
      if (claims.size >= capacity) return "capacity";
      claims.add(key);
      return "created";
    },
  };
}

function makeEvent(tools = makeTools()) {
  return {
    agent: "build",
    model: { providerID: "wrench-subroute", id: "openrouter" },
    system: [{ type: "text", text: "system text" }],
    messages: [{ role: "user", content: "Read a file" }],
    tools,
    options: {},
  };
}

test("tool inventory hash ignores object-key order and binds schemas", () => {
  const first = { read: { description: "Read", input: { type: "object", required: ["path"] } } };
  const reordered = {
    read: { input: { required: ["path"], type: "object" }, description: "Read" },
  };
  const changed = { read: { description: "Read", input: { type: "object" } } };

  assert.equal(toolInventorySha256(first), toolInventorySha256(reordered));
  assert.notEqual(toolInventorySha256(first), toolInventorySha256(changed));
});

test("tool inventory hashing enforces an aggregate byte limit", () => {
  const oversized = {
    read: {
      description: "x".repeat(600_000),
      input: { pattern: "y".repeat(600_000) },
    },
  };

  assert.throws(() => toolInventorySha256(oversized), /tool_inventory_byte_limit/);
});

test("exact profile removes only non-allowlisted schemas for this event", async () => {
  const tools = makeTools();
  const retained = tools.read;
  const receipts = [];
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectProfile: async (input) => {
      assert.equal(Object.isFrozen(input), true);
      assert.equal(Object.isFrozen(input.messages), true);
      assert.throws(() => {
        input.messages[0].content = "changed";
      }, TypeError);
      return "read-only";
    },
    emitReceipt: async (receipt) => receipts.push(receipt),
  });
  const event = makeEvent(tools);

  await hook(event);

  assert.deepEqual(Object.keys(event.tools), ["read"]);
  assert.equal(event.tools.read, retained);
  assert.equal(receipts.length, 1);
  assert.equal(receipts[0].outcome, "filtered");
  assert.equal(receipts[0].tool_count_before, 3);
  assert.equal(receipts[0].tool_count_after, 1);
  assert.equal(JSON.stringify(receipts[0]).includes("Read a file"), false);
});

test("selector snapshots omit undefined object fields and stay immutable", async () => {
  const tools = makeTools();
  const event = makeEvent(tools);
  event.messages[0].optional = undefined;
  const receipts = [];
  let snapshot;
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectProfile: async (input) => {
      snapshot = input.messages;
      return "read-only";
    },
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(event);

  assert.equal(Object.hasOwn(snapshot[0], "optional"), false);
  assert.equal(Object.isFrozen(snapshot[0]), true);
  assert.equal(receipts[0].outcome, "filtered");
});

test("selector snapshots enumerable data from OpenCode message instances", async () => {
  class OpenCodeMessage {
    constructor() {
      this.id = "message-1";
      this.role = "user";
      this.content = [{ type: "text", text: "Read a file" }];
    }
  }
  const tools = makeTools();
  const event = makeEvent(tools);
  event.messages = [new OpenCodeMessage()];
  const receipts = [];
  let snapshot;
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectProfile: async (input) => {
      snapshot = input.messages;
      return "read-only";
    },
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(event);

  assert.deepEqual(snapshot, [{
    id: "message-1",
    role: "user",
    content: [{ type: "text", text: "Read a file" }],
  }]);
  assert.equal(Object.getPrototypeOf(snapshot[0]), Object.prototype);
  assert.equal(receipts[0].outcome, "filtered");
});

test("selector snapshot rejects accessors without invoking them", async () => {
  const tools = makeTools();
  const event = makeEvent(tools);
  let getterCalls = 0;
  Object.defineProperty(event.messages[0], "unsafe", {
    enumerable: true,
    get() {
      getterCalls += 1;
      return "must not be read";
    },
  });
  const receipts = [];
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectProfile: async () => "read-only",
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(event);

  assert.equal(getterCalls, 0);
  assert.deepEqual(Object.keys(tools).sort(), ["edit", "grep", "read"]);
  assert.equal(receipts[0].reason, "selector_input_invalid");
});

test("inventory mismatch passes the full tool map through", async () => {
  const tools = makeTools();
  const receipts = [];
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [{ ...makeProfile(tools), inventorySha256: "0".repeat(64) }],
    selectProfile: async () => "read-only",
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(makeEvent(tools));

  assert.deepEqual(Object.keys(tools).sort(), ["edit", "grep", "read"]);
  assert.equal(receipts[0].reason, "inventory_mismatch");
});

test("profile with a missing tool passes the full tool map through", async () => {
  const tools = makeTools();
  const receipts = [];
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools, ["read", "missing"])],
    selectProfile: async () => "read-only",
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(makeEvent(tools));

  assert.deepEqual(Object.keys(tools).sort(), ["edit", "grep", "read"]);
  assert.equal(receipts[0].reason, "profile_tool_unavailable");
});

test("selector failure passes the full tool map through", async () => {
  const tools = makeTools();
  const receipts = [];
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectProfile: async () => {
      throw new Error("private selector detail");
    },
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(makeEvent(tools));

  assert.deepEqual(Object.keys(tools).sort(), ["edit", "grep", "read"]);
  assert.equal(receipts[0].reason, "selector_failed");
  assert.equal(JSON.stringify(receipts[0]).includes("private selector detail"), false);
});

test("selector timeout passes the full tool map through", async () => {
  const tools = makeTools();
  const receipts = [];
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectionTimeoutMs: 5,
    selectProfile: () => new Promise(() => {}),
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(makeEvent(tools));

  assert.deepEqual(Object.keys(tools).sort(), ["edit", "grep", "read"]);
  assert.equal(receipts[0].reason, "selector_timeout");
});

test("unknown profile passes the full tool map through", async () => {
  const tools = makeTools();
  const receipts = [];
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectProfile: async () => "not-registered",
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  await hook(makeEvent(tools));

  assert.deepEqual(Object.keys(tools).sort(), ["edit", "grep", "read"]);
  assert.equal(receipts[0].reason, "profile_unknown");
  assert.equal(receipts[0].profile_id, null);
});

test("receipt failure restores the original tool map and rejects dispatch hook", async () => {
  const tools = makeTools();
  const originalDescriptors = Object.getOwnPropertyDescriptors(tools);
  const hook = createToolProfileHook({
    enabled: true,
    profiles: [makeProfile(tools)],
    selectProfile: async () => "read-only",
    emitReceipt: async () => {
      throw new Error("sink unavailable");
    },
  });

  await assert.rejects(hook(makeEvent(tools)), /tool_profile_receipt_failed/);
  assert.deepEqual(Object.getOwnPropertyDescriptors(tools), originalDescriptors);
});

test("disabled plugin does not register a hook", async () => {
  const plugin = createToolProfilePlugin({ enabled: false });

  await plugin.setup({});
});

test("enabled plugin scopes context hook to the configured provider and disposes it", async () => {
  const tools = makeTools();
  const registrations = [];
  let disposeCount = 0;
  const plugin = createToolProfilePlugin({
    enabled: true,
    providerID: "wrench-subroute",
    profiles: [makeProfile(tools)],
    selectProfile: async () => "read-only",
    emitReceipt: async () => {},
  });
  const cleanup = await plugin.setup({
    session: {
      hook: async (...args) => {
        registrations.push(args);
        return { dispose: async () => { disposeCount += 1; } };
      },
    },
  });

  assert.equal(registrations.length, 1);
  assert.equal(registrations[0][0], "context");
  assert.equal(registrations[0][2].providerID, "wrench-subroute");
  await cleanup();
  await cleanup();
  assert.equal(disposeCount, 1);
});

test("session-scoped hook freezes one profile and restores bounded schemas on demand", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const receipts = [];
  const sessionStateStore = makeSessionStateStore();
  let selections = 0;
  const hook = createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    profiles: [profile],
    selectProfile: async () => {
      selections += 1;
      return profile.id;
    },
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  const first = makeSessionEvent(makeSessionTools());
  await hook(first);
  assert.deepEqual(Object.keys(first.tools).sort(), ["read", "wrench_expand_tools"]);

  const second = makeSessionEvent(makeSessionTools());
  second.messages = [{ role: "user", content: "Now edit the file" }];
  await hook(second);
  assert.deepEqual(Object.keys(second.tools).sort(), ["read", "wrench_expand_tools"]);
  assert.equal(selections, 1);

  const discovery = await hook.requestExpansion({
    sessionID: "session-1",
    toolNames: ["__list_available__"],
  });
  assert.deepEqual(discovery.availableToolNames, ["edit", "grep"]);
  await assert.rejects(
    hook.requestExpansion({ sessionID: "session-1", toolNames: ["__list_available__"] }),
    /tool_profile_expansion_discovery_limit_reached/,
  );

  const expansion = await hook.requestExpansion({ sessionID: "session-1", toolNames: ["edit"] });
  assert.deepEqual(expansion.toolNames, ["edit"]);
  const third = makeSessionEvent(makeSessionTools());
  await hook(third);
  assert.deepEqual(Object.keys(third.tools).sort(), ["edit", "read", "wrench_expand_tools"]);
  assert.equal(selections, 1);
  assert.equal(receipts.some((receipt) => receipt.outcome === "schema_expansion"), true);
  assert.equal(receipts.some((receipt) => receipt.outcome === "schema_discovery"), true);
});

test("persistent session state survives plugin restart without rerunning selection", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const sessionStateStore = makeSessionStateStore();
  let selections = 0;
  const makeHook = () => createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    profiles: [profile],
    selectProfile: async () => {
      selections += 1;
      return profile.id;
    },
    emitReceipt: async () => {},
  });

  const firstHook = makeHook();
  await firstHook(makeSessionEvent(makeSessionTools()));
  const discovery = await firstHook.requestExpansion({
    sessionID: "session-1",
    toolNames: ["__list_available__"],
  });
  assert.deepEqual(discovery.availableToolNames, ["edit", "grep"]);
  await firstHook.requestExpansion({ sessionID: "session-1", toolNames: ["edit"] });

  const storedKeys = [...sessionStateStore.records.keys()];
  assert.equal(storedKeys.length, 1);
  assert.match(storedKeys[0], /^session-profile\/[a-f0-9]{64}$/);
  assert.equal(JSON.stringify([...sessionStateStore.records.values()]).includes("session-1"), false);

  const restartedHook = makeHook();
  const resumed = makeSessionEvent(makeSessionTools());
  await restartedHook(resumed);
  assert.deepEqual(Object.keys(resumed.tools).sort(), ["edit", "read", "wrench_expand_tools"]);
  assert.equal(selections, 1);
  const nextExpansion = await restartedHook.requestExpansion({
    sessionID: "session-1",
    toolNames: ["grep"],
  });
  assert.deepEqual(nextExpansion.toolNames, ["grep"]);
});

test("persisted session inventory drift passes through after restart without reselection", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const sessionStateStore = makeSessionStateStore();
  let selections = 0;
  const makeHook = () => createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    profiles: [profile],
    selectProfile: async () => {
      selections += 1;
      return profile.id;
    },
    emitReceipt: async () => {},
  });

  await makeHook()(makeSessionEvent(makeSessionTools()));
  const changedTools = makeSessionTools();
  changedTools.edit.description = "Changed inventory after restart";
  const changed = makeSessionEvent(changedTools);
  await makeHook()(changed);

  assert.equal(Object.keys(changed.tools).length, 4);
  assert.equal(selections, 1);
});

test("session storage write failure rejects the hook before filtering tools", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const hook = createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore: makeSessionStateStore({ failSet: true }),
    profiles: [profile],
    selectProfile: async () => profile.id,
    emitReceipt: async () => {},
  });
  const event = makeSessionEvent(makeSessionTools());

  await assert.rejects(hook(event), /session_profile_storage_failed/);
  assert.equal(Object.keys(event.tools).length, 4);
});

test("session identity and inventory drift fail through without reselection", async () => {
  const tools = makeSessionTools();
  const profile = makeProfile(tools, ["read", "wrench_expand_tools"]);
  const receipts = [];
  const sessionStateStore = makeSessionStateStore();
  let selections = 0;
  const hook = createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    profiles: [profile],
    selectProfile: async () => {
      selections += 1;
      return profile.id;
    },
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  const missingIdentity = makeEvent(makeSessionTools());
  await hook(missingIdentity);
  assert.equal(Object.keys(missingIdentity.tools).length, 4);
  assert.equal(selections, 0);

  const first = makeSessionEvent(makeSessionTools());
  await hook(first);
  const changedInventory = makeSessionTools();
  changedInventory.grep.description = "Changed after the session profile was frozen";
  const changed = makeSessionEvent(changedInventory);
  await hook(changed);
  assert.equal(Object.keys(changed.tools).length, 4);
  assert.equal(selections, 1);
  assert.equal(receipts.at(-1).reason, "session_inventory_changed");

  const changedAgain = makeSessionEvent(makeSessionTools());
  await hook(changedAgain);
  assert.equal(Object.keys(changedAgain.tools).length, 4);
  assert.equal(selections, 1);
});

test("session expansion limits reject unknown and excess schemas atomically", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const sessionStateStore = makeSessionStateStore();
  const hook = createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    profiles: [profile],
    expansionLimits: {
      maxToolNamesPerCall: 1,
      maxExpandedToolsPerSession: 1,
      maxCallsPerSession: 2,
      maxSchemaBytesPerSession: 10_000,
    },
    selectProfile: async () => profile.id,
    emitReceipt: async () => {},
  });
  await hook(makeSessionEvent(makeSessionTools()));

  await assert.rejects(
    hook.requestExpansion({ sessionID: "session-1", toolNames: ["missing"] }),
    /tool_profile_expansion_tool_outside_inventory/,
  );
  await hook.requestExpansion({ sessionID: "session-1", toolNames: ["edit"] });
  await assert.rejects(
    hook.requestExpansion({ sessionID: "session-1", toolNames: ["grep"] }),
    /tool_profile_expansion_session_tool_limit_reached/,
  );
  const next = makeSessionEvent(makeSessionTools());
  await hook(next);
  assert.deepEqual(Object.keys(next.tools).sort(), ["edit", "read", "wrench_expand_tools"]);
});

test("session cache capacity preserves existing sessions and passes new ones through", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const sessionStateStore = makeSessionStateStore();
  let selections = 0;
  const hook = createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    sessionCacheCapacity: 1,
    profiles: [profile],
    selectProfile: async () => {
      selections += 1;
      return profile.id;
    },
    emitReceipt: async () => {},
  });

  const first = makeSessionEvent(makeSessionTools(), "session-1");
  await hook(first);
  const second = makeSessionEvent(makeSessionTools(), "session-2");
  await hook(second);
  assert.deepEqual(Object.keys(second.tools).sort(), ["edit", "grep", "read", "wrench_expand_tools"]);
  const firstAgain = makeSessionEvent(makeSessionTools(), "session-1");
  await hook(firstAgain);
  assert.deepEqual(Object.keys(firstAgain.tools).sort(), ["read", "wrench_expand_tools"]);
  assert.equal(selections, 1);
});

test("session cache byte budget passes through oversized name indexes", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const receipts = [];
  const sessionStateStore = makeSessionStateStore();
  let selections = 0;
  const hook = createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    sessionCacheNameByteCapacity: 16,
    profiles: [profile],
    selectProfile: async () => {
      selections += 1;
      return profile.id;
    },
    emitReceipt: async (receipt) => receipts.push(receipt),
  });

  const event = makeSessionEvent(makeSessionTools());
  await hook(event);
  assert.deepEqual(Object.keys(event.tools).sort(), ["edit", "grep", "read", "wrench_expand_tools"]);
  assert.equal(selections, 0);
  assert.equal(receipts[0].reason, "session_cache_capacity_reached");
});

test("schema discovery byte limit is enforced and consumes its one attempt", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  const sessionStateStore = makeSessionStateStore();
  const hook = createToolProfileHook({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    profiles: [profile],
    expansionLimits: { maxDiscoveryNameBytesPerSession: 2 },
    selectProfile: async () => profile.id,
    emitReceipt: async () => {},
  });
  await hook(makeSessionEvent(makeSessionTools()));

  await assert.rejects(
    hook.requestExpansion({ sessionID: "session-1", toolNames: ["__list_available__"] }),
    /tool_profile_expansion_discovery_byte_limit_reached/,
  );
  await assert.rejects(
    hook.requestExpansion({ sessionID: "session-1", toolNames: ["__list_available__"] }),
    /tool_profile_expansion_discovery_limit_reached/,
  );
});

test("session plugin registers and disposes the bounded expansion tool", async () => {
  const inventory = makeSessionTools();
  const profile = makeProfile(inventory, ["read", "wrench_expand_tools"]);
  let registeredTool;
  let toolDisposals = 0;
  let hookDisposals = 0;
  const sessionStateStore = makeSessionStateStore();
  const plugin = createToolProfilePlugin({
    enabled: true,
    sessionScoped: true,
    sessionStateStore,
    profiles: [profile],
    selectProfile: async () => profile.id,
    emitReceipt: async () => {},
  });
  const cleanup = await plugin.setup({
    tool: {
      transform: async (transform) => {
        transform({ add: (tool) => { registeredTool = tool; } });
        return { dispose: async () => { toolDisposals += 1; } };
      },
    },
    session: {
      hook: async () => ({ dispose: async () => { hookDisposals += 1; } }),
    },
  });

  assert.equal(registeredTool.name, "wrench_expand_tools");
  assert.equal(registeredTool.input.properties.toolNames.maxItems, 8);
  assert.deepEqual(
    { description: registeredTool.description, input: registeredTool.input },
    createToolExpansionDefinition(),
  );
  await cleanup();
  assert.equal(toolDisposals, 1);
  assert.equal(hookDisposals, 1);
});
