import { createHash } from "node:crypto";

export const TOOL_PROFILE_HOOK_ID = "wrench-subroute-tool-profiles-v1";
export const TOOL_INVENTORY_SCHEMA = "wrench.opencode.tool-inventory.v1";
export const TOOL_PROFILE_RECEIPT_SCHEMA = "wrench.opencode.tool-profile-receipt.v1";
export const SESSION_PROFILE_STATE_SCHEMA = "wrench.opencode.session-profile-state.v1";

const MAX_TOOLS = 256;
const MAX_PROFILES = 64;
const MAX_JSON_DEPTH = 64;
const MAX_JSON_NODES = 20_000;
const MAX_INVENTORY_BYTES = 1_048_576;
const DEFAULT_SESSION_CACHE_CAPACITY = 256;
const DEFAULT_SESSION_CACHE_NAME_BYTE_CAPACITY = 1_048_576;
const SESSION_PROFILE_STORAGE_PREFIX = "session-profile/";
const MAX_SESSION_PROFILE_STATE_BYTES = 131_072;
const DEFAULT_EXPANSION_LIMITS = Object.freeze({
  maxToolNamesPerCall: 8,
  maxExpandedToolsPerSession: 24,
  maxCallsPerSession: 4,
  maxDiscoveryCallsPerSession: 1,
  maxDiscoveryNameBytesPerSession: 8_192,
  maxSchemaBytesPerSession: 32_768,
});
const MAX_EXPANSION_LIMITS = Object.freeze({
  maxToolNamesPerCall: 32,
  maxExpandedToolsPerSession: MAX_TOOLS,
  maxCallsPerSession: 64,
  maxDiscoveryCallsPerSession: 4,
  maxDiscoveryNameBytesPerSession: MAX_INVENTORY_BYTES,
  maxSchemaBytesPerSession: MAX_INVENTORY_BYTES,
});
const PROFILE_ID_PATTERN = /^[a-z][a-z0-9._-]{0,63}$/;
const SHA256_PATTERN = /^[a-f0-9]{64}$/;
const SELECTION_TIMEOUT = Symbol("selection_timeout");
const SELECTOR_FAILED = Symbol("selector_failed");
const BLOCK_REASON_PATTERN = /^[a-z0-9_]{1,64}$/;

function isPlainRecord(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function accountInputBytes(state, value) {
  state.inputBytes += Buffer.byteLength(value, "utf8");
  if (state.inputBytes > MAX_INVENTORY_BYTES) {
    throw new TypeError("tool_inventory_byte_limit");
  }
}

function canonicalJson(value, state = { nodes: 0, inputBytes: 0 }, depth = 0) {
  state.nodes += 1;
  if (state.nodes > MAX_JSON_NODES || depth > MAX_JSON_DEPTH) {
    throw new TypeError("tool_inventory_complexity_limit");
  }

  if (value === null) return "null";
  if (typeof value === "string") {
    accountInputBytes(state, value);
    return JSON.stringify(value);
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("tool_inventory_number_invalid");
    return JSON.stringify(value);
  }
  if (typeof value !== "object") throw new TypeError("tool_inventory_value_invalid");

  if (Array.isArray(value)) {
    if (Object.getOwnPropertySymbols(value).length !== 0) {
      throw new TypeError("tool_inventory_symbol_key_invalid");
    }
    const names = Object.getOwnPropertyNames(value);
    if (names.length !== value.length + 1 || !names.includes("length")) {
      throw new TypeError("tool_inventory_array_shape_invalid");
    }
    const items = [];
    for (let index = 0; index < value.length; index += 1) {
      const descriptor = Object.getOwnPropertyDescriptor(value, String(index));
      if (!descriptor || !descriptor.enumerable || !Object.hasOwn(descriptor, "value")) {
        throw new TypeError("tool_inventory_array_shape_invalid");
      }
      items.push(canonicalJson(descriptor.value, state, depth + 1));
    }
    return "[" + items.join(",") + "]";
  }

  if (!isPlainRecord(value) || Object.getOwnPropertySymbols(value).length !== 0) {
    throw new TypeError("tool_inventory_object_invalid");
  }
  const names = Object.getOwnPropertyNames(value);
  const keys = Object.keys(value).sort();
  if (names.length !== keys.length) throw new TypeError("tool_inventory_object_shape_invalid");
  const entries = [];
  for (const key of keys) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (!descriptor || !descriptor.enumerable || !Object.hasOwn(descriptor, "value")) {
      throw new TypeError("tool_inventory_object_shape_invalid");
    }
    accountInputBytes(state, key);
    entries.push(
      JSON.stringify(key) + ":" + canonicalJson(descriptor.value, state, depth + 1),
    );
  }
  return "{" + entries.join(",") + "}";
}

function selectorJson(value, state = { nodes: 0, inputBytes: 0 }, depth = 0, inArray = false) {
  state.nodes += 1;
  if (state.nodes > MAX_JSON_NODES || depth > MAX_JSON_DEPTH) {
    throw new TypeError("selector_input_complexity_limit");
  }
  if (value === undefined && inArray) return "null";
  if (value === null) return "null";
  if (typeof value === "string") {
    accountInputBytes(state, value);
    return JSON.stringify(value);
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("selector_input_number_invalid");
    return JSON.stringify(value);
  }
  if (typeof value !== "object" || value === undefined) {
    throw new TypeError("selector_input_value_invalid");
  }

  if (Array.isArray(value)) {
    if (Object.getOwnPropertySymbols(value).length !== 0) {
      throw new TypeError("selector_input_symbol_key_invalid");
    }
    const names = Object.getOwnPropertyNames(value);
    if (names.length !== value.length + 1 || !names.includes("length")) {
      throw new TypeError("selector_input_array_shape_invalid");
    }
    const items = [];
    for (let index = 0; index < value.length; index += 1) {
      const descriptor = Object.getOwnPropertyDescriptor(value, String(index));
      if (!descriptor || !descriptor.enumerable || !Object.hasOwn(descriptor, "value")) {
        throw new TypeError("selector_input_array_shape_invalid");
      }
      items.push(selectorJson(descriptor.value, state, depth + 1, true));
    }
    return "[" + items.join(",") + "]";
  }

  let prototype = Object.getPrototypeOf(value);
  let hasDataObjectPrototype = prototype === null || prototype === Object.prototype;
  let prototypeDepth = 0;
  while (!hasDataObjectPrototype && prototype !== null && prototypeDepth < MAX_JSON_DEPTH) {
    prototype = Object.getPrototypeOf(prototype);
    prototypeDepth += 1;
    hasDataObjectPrototype = prototype === Object.prototype;
  }
  if (
    (!isPlainRecord(value) && !hasDataObjectPrototype) ||
    Object.getOwnPropertySymbols(value).length !== 0
  ) {
    throw new TypeError("selector_input_object_invalid");
  }
  const entries = [];
  const names = Object.getOwnPropertyNames(value);
  const keys = Object.keys(value).sort();
  if (names.length !== keys.length || (!isPlainRecord(value) && keys.length === 0)) {
    throw new TypeError("selector_input_object_shape_invalid");
  }
  for (const key of keys) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (!descriptor || !descriptor.enumerable || !Object.hasOwn(descriptor, "value")) {
      throw new TypeError("selector_input_object_shape_invalid");
    }
    if (descriptor.value === undefined) continue;
    accountInputBytes(state, key);
    entries.push(
      JSON.stringify(key) + ":" + selectorJson(descriptor.value, state, depth + 1),
    );
  }
  return "{" + entries.join(",") + "}";
}

function deepFreeze(value) {
  if (value === null || typeof value !== "object" || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreeze(child);
  return Object.freeze(value);
}

function immutableJsonSnapshot(value) {
  const serialized = selectorJson(value);
  if (Buffer.byteLength(serialized, "utf8") > MAX_INVENTORY_BYTES) {
    throw new TypeError("selector_input_byte_limit");
  }
  return deepFreeze(JSON.parse(serialized));
}

export function toolInventorySha256(tools) {
  if (!isPlainRecord(tools) || Object.getOwnPropertySymbols(tools).length !== 0) {
    throw new TypeError("tool_inventory_record_invalid");
  }
  const names = Object.keys(tools).sort();
  if (names.length > MAX_TOOLS || Object.getOwnPropertyNames(tools).length !== names.length) {
    throw new TypeError("tool_inventory_count_or_shape_invalid");
  }
  const serialized = canonicalJson(tools);
  if (Buffer.byteLength(serialized, "utf8") > MAX_INVENTORY_BYTES) {
    throw new TypeError("tool_inventory_byte_limit");
  }
  return createHash("sha256")
    .update(TOOL_INVENTORY_SCHEMA + "\n" + serialized, "utf8")
    .digest("hex");
}

function validateProfiles(profiles, requiredToolNames = []) {
  if (!Array.isArray(profiles) || profiles.length === 0 || profiles.length > MAX_PROFILES) {
    throw new TypeError("tool_profiles_invalid");
  }
  const registry = new Map();
  for (const profile of profiles) {
    if (!isPlainRecord(profile)) throw new TypeError("tool_profile_invalid");
    const { id, inventorySha256, allowedToolNames } = profile;
    if (
      typeof id !== "string" ||
      !PROFILE_ID_PATTERN.test(id) ||
      typeof inventorySha256 !== "string" ||
      !SHA256_PATTERN.test(inventorySha256) ||
      !Array.isArray(allowedToolNames) ||
      allowedToolNames.length === 0 ||
      allowedToolNames.length > MAX_TOOLS
    ) {
      throw new TypeError("tool_profile_fields_invalid");
    }
    const names = new Set();
    for (const name of allowedToolNames) {
      if (typeof name !== "string" || name.length === 0 || names.has(name)) {
        throw new TypeError("tool_profile_allowlist_invalid");
      }
      names.add(name);
    }
    if (requiredToolNames.some((name) => !names.has(name))) {
      throw new TypeError("tool_profile_required_tool_missing");
    }
    if (registry.has(id)) throw new TypeError("tool_profile_id_duplicate");
    registry.set(
      id,
      Object.freeze({
        id,
        inventorySha256,
        allowedToolNames: Object.freeze([...names]),
      }),
    );
  }
  return registry;
}

function makeReceipt({ outcome, reason, inventorySha256, profileId, toolCountBefore, toolCountAfter, schemaExpansion, schemaDiscovery }) {
  const receipt = {
    schema: TOOL_PROFILE_RECEIPT_SCHEMA,
    outcome,
    reason,
    inventory_sha256: inventorySha256 ?? null,
    profile_id: profileId ?? null,
    tool_count_before: toolCountBefore,
    tool_count_after: toolCountAfter,
  };
  if (schemaExpansion !== undefined) {
    receipt.schema_expansion = Object.freeze({
      ...schemaExpansion,
      tool_names: Object.freeze([...(schemaExpansion.tool_names ?? [])]),
    });
  }
  if (schemaDiscovery !== undefined) {
    receipt.schema_discovery = Object.freeze({
      ...schemaDiscovery,
      tool_names: Object.freeze([...(schemaDiscovery.tool_names ?? [])]),
    });
  }
  return Object.freeze(receipt);
}

function validateExpansionLimits(limits) {
  if (!isPlainRecord(limits)) throw new TypeError("expansion_limits_invalid");
  const result = { ...DEFAULT_EXPANSION_LIMITS };
  for (const key of Object.keys(DEFAULT_EXPANSION_LIMITS)) {
    if (limits[key] === undefined) continue;
    const value = limits[key];
    if (!Number.isSafeInteger(value) || value < 1 || value > MAX_EXPANSION_LIMITS[key]) {
      throw new TypeError("expansion_limit_invalid");
    }
    result[key] = value;
  }
  return Object.freeze(result);
}

function sessionProfileStorageKey(sessionID) {
  const digest = createHash("sha256").update(sessionID, "utf8").digest("hex");
  return SESSION_PROFILE_STORAGE_PREFIX + digest;
}

function serializeSessionProfileState(state, overrides = {}) {
  const record = {
    schema: SESSION_PROFILE_STATE_SCHEMA,
    inventory_sha256: state.inventorySha256,
    profile_id: state.profileId ?? null,
    blocked_reason: state.blockedReason ?? null,
    expanded_tool_names: [...(overrides.expandedToolNames ?? state.expandedToolNames)].sort(),
    expansion_calls: overrides.expansionCalls ?? state.expansionCalls,
    discovery_calls: overrides.discoveryCalls ?? state.discoveryCalls,
    expanded_schema_bytes: overrides.expandedSchemaBytes ?? state.expandedSchemaBytes,
    discovered_tool_names: [...(overrides.discoveredToolNames ?? state.discoveredToolNames ?? [])],
  };
  if (Buffer.byteLength(JSON.stringify(record), "utf8") > MAX_SESSION_PROFILE_STATE_BYTES) {
    throw new TypeError("session_profile_state_byte_limit");
  }
  return record;
}

function validateStoredSessionProfileState(record, state, registry, limits) {
  if (!isPlainRecord(record) || record.schema !== SESSION_PROFILE_STATE_SCHEMA) {
    return { ok: false, reason: "persisted_state_invalid" };
  }
  const recordKeys = [
    "blocked_reason",
    "discovered_tool_names",
    "discovery_calls",
    "expanded_schema_bytes",
    "expanded_tool_names",
    "expansion_calls",
    "inventory_sha256",
    "profile_id",
    "schema",
  ];
  if (
    Object.getOwnPropertySymbols(record).length !== 0 ||
    Object.keys(record).sort().join("\n") !== recordKeys.join("\n") ||
    Buffer.byteLength(JSON.stringify(record), "utf8") > MAX_SESSION_PROFILE_STATE_BYTES
  ) {
    return { ok: false, reason: "persisted_state_invalid" };
  }
  if (record.inventory_sha256 !== state.inventorySha256) {
    return { ok: false, reason: "inventory_changed" };
  }
  if (
    !(record.profile_id === null || typeof record.profile_id === "string") ||
    !(record.blocked_reason === null ||
      (typeof record.blocked_reason === "string" && BLOCK_REASON_PATTERN.test(record.blocked_reason))) ||
    !Array.isArray(record.expanded_tool_names) ||
    !Array.isArray(record.discovered_tool_names) ||
    !Number.isSafeInteger(record.expansion_calls) ||
    record.expansion_calls < 0 ||
    record.expansion_calls > limits.maxCallsPerSession ||
    !Number.isSafeInteger(record.discovery_calls) ||
    record.discovery_calls < 0 ||
    record.discovery_calls > limits.maxDiscoveryCallsPerSession ||
    !Number.isSafeInteger(record.expanded_schema_bytes) ||
    record.expanded_schema_bytes < 0 ||
    record.expanded_schema_bytes > limits.maxSchemaBytesPerSession
  ) {
    return { ok: false, reason: "persisted_state_invalid" };
  }

  if (record.blocked_reason !== null) {
    if (
      record.profile_id !== null ||
      record.expanded_tool_names.length > 0 ||
      record.expansion_calls !== 0 ||
      record.discovery_calls !== 0 ||
      record.expanded_schema_bytes !== 0 ||
      record.discovered_tool_names.length !== 0
    ) {
      return { ok: false, reason: "persisted_state_invalid" };
    }
    return { ok: true, profileId: null, blockedReason: record.blocked_reason };
  }

  const profile = registry.get(record.profile_id);
  if (!profile || profile.inventorySha256 !== state.inventorySha256) {
    return { ok: false, reason: "persisted_state_invalid" };
  }
  const baseNames = new Set(profile.allowedToolNames);
  const expandedNames = new Set();
  for (const name of record.expanded_tool_names) {
    if (
      typeof name !== "string" ||
      name.length === 0 ||
      name.length > 256 ||
      expandedNames.has(name) ||
      baseNames.has(name) ||
      !state.inventoryToolNames.has(name)
    ) {
      return { ok: false, reason: "persisted_state_invalid" };
    }
    expandedNames.add(name);
  }
  if (
    expandedNames.size > limits.maxExpandedToolsPerSession ||
    expandedNames.size > record.expansion_calls * limits.maxToolNamesPerCall
  ) {
    return { ok: false, reason: "persisted_state_invalid" };
  }
  const expandedBytes = [...expandedNames].reduce(
    (sum, name) => sum + (state.schemaBytes.get(name) ?? 0),
    0,
  );
  if (expandedBytes !== record.expanded_schema_bytes) {
    return { ok: false, reason: "persisted_state_invalid" };
  }

  const discoveredNames = new Set();
  let discoveredBytes = 0;
  for (const name of record.discovered_tool_names) {
    if (
      typeof name !== "string" ||
      name.length === 0 ||
      discoveredNames.has(name) ||
      !state.inventoryToolNames.has(name) ||
      baseNames.has(name)
    ) {
      return { ok: false, reason: "persisted_state_invalid" };
    }
    discoveredNames.add(name);
    discoveredBytes += Buffer.byteLength(name, "utf8");
  }
  if (
    discoveredBytes > limits.maxDiscoveryNameBytesPerSession ||
    record.discovery_calls === 0 && record.discovered_tool_names.length > 0 ||
    record.discovery_calls > 0 && record.discovered_tool_names.length === 0 &&
      [...state.inventoryToolNames].some((name) => !baseNames.has(name) && !expandedNames.has(name))
  ) {
    return { ok: false, reason: "persisted_state_invalid" };
  }
  return {
    ok: true,
    profileId: profile.id,
    blockedReason: null,
    expandedToolNames: expandedNames,
    expansionCalls: record.expansion_calls,
    discoveryCalls: record.discovery_calls,
    expandedSchemaBytes: expandedBytes,
    discoveredToolNames: [...discoveredNames],
  };
}

function validateSessionStateStore(store) {
  if (
    store === null ||
    typeof store !== "object" ||
    typeof store.get !== "function" ||
    typeof store.set !== "function" ||
    typeof store.claim !== "function"
  ) {
    throw new TypeError("session_state_store_required");
  }
  return store;
}

function makeSessionState({ inventorySha256, names, tools, cacheNameBytes, storageKey }) {
  return {
    inventorySha256,
    inventoryToolNames: new Set(names),
    schemaBytes: new Map(
      names.map((name) => [name, Buffer.byteLength(canonicalJson(tools[name]), "utf8")]),
    ),
    profileId: null,
    proposedProfileId: null,
    selectionDone: false,
    selectionPromise: null,
    selectionController: null,
    blockedReason: null,
    expandedToolNames: new Set(),
    expansionCalls: 0,
    expandedSchemaBytes: 0,
    discoveryCalls: 0,
    discoveredToolNames: [],
    cacheNameBytes,
    storageKey,
    dirty: false,
  };
}

function blockSessionState(state, reason) {
  state.profileId = null;
  state.proposedProfileId = null;
  state.selectionPromise = null;
  state.selectionController?.abort();
  state.selectionController = null;
  state.selectionDone = true;
  state.blockedReason = reason;
  state.expandedToolNames.clear();
  state.expansionCalls = 0;
  state.expandedSchemaBytes = 0;
  state.discoveryCalls = 0;
  state.discoveredToolNames = [];
  state.dirty = true;
}

const EXPANSION_TOOL_DESCRIPTION =
  "Expose tool schemas from this session's original inventory for the next request. Use __list_available__ alone to discover omitted tool names.";

export function createToolExpansionDefinition(expansionLimits = DEFAULT_EXPANSION_LIMITS) {
  const limits = validateExpansionLimits(expansionLimits);
  return deepFreeze({
    description: EXPANSION_TOOL_DESCRIPTION,
    input: {
      type: "object",
      properties: {
        toolNames: {
          type: "array",
          items: { type: "string", minLength: 1, maxLength: 256 },
          minItems: 1,
          maxItems: limits.maxToolNamesPerCall,
          description: "Use original tool names to expand schemas, or the sole value __list_available__ to discover omitted names.",
        },
      },
      required: ["toolNames"],
      additionalProperties: false,
    },
  });
}

async function emitOrThrow(emitReceipt, receipt) {
  await emitReceipt(receipt);
}

function restoreRemovedTools(tools, removed) {
  for (const [name, descriptor] of removed) {
    Object.defineProperty(tools, name, descriptor);
  }
}

/**
 * Create an OpenCode context hook with optional per-session profile state.
 *
 * The selector receives the request context and must use a local-only Wrench
 * model. Its only accepted output is a profile ID from the immutable registry.
 * The hook never creates tools or edits permission rules.
 */
export function createToolProfileHook({
  enabled = false,
  profiles,
  selectProfile,
  emitReceipt,
  selectionTimeoutMs = 1500,
  sessionScoped = false,
  sessionStateStore,
  sessionCacheCapacity = DEFAULT_SESSION_CACHE_CAPACITY,
  sessionCacheNameByteCapacity = DEFAULT_SESSION_CACHE_NAME_BYTE_CAPACITY,
  expansionToolName = "wrench_expand_tools",
  expansionLimits = DEFAULT_EXPANSION_LIMITS,
}) {
  if (typeof enabled !== "boolean") throw new TypeError("enabled_must_be_boolean");
  if (!enabled) return async () => {};
  if (typeof sessionScoped !== "boolean") throw new TypeError("session_scoped_must_be_boolean");
  if (typeof selectProfile !== "function" || typeof emitReceipt !== "function") {
    throw new TypeError("tool_profile_callbacks_required");
  }
  if (
    !Number.isSafeInteger(selectionTimeoutMs) ||
    selectionTimeoutMs < 1 ||
    selectionTimeoutMs > 30_000
  ) {
    throw new TypeError("selection_timeout_invalid");
  }
  if (!Number.isSafeInteger(sessionCacheCapacity) || sessionCacheCapacity < 1 || sessionCacheCapacity > 10_000) {
    throw new TypeError("session_cache_capacity_invalid");
  }
  if (
    !Number.isSafeInteger(sessionCacheNameByteCapacity) ||
    sessionCacheNameByteCapacity < 1 ||
    sessionCacheNameByteCapacity > 64 * MAX_INVENTORY_BYTES
  ) {
    throw new TypeError("session_cache_name_byte_capacity_invalid");
  }
  if (
    sessionScoped &&
    (typeof expansionToolName !== "string" || expansionToolName.length === 0 || expansionToolName.length > 256)
  ) {
    throw new TypeError("expansion_tool_name_invalid");
  }
  const limits = validateExpansionLimits(expansionLimits);
  const registry = validateProfiles(profiles, sessionScoped ? [expansionToolName] : []);
  const stateStore = sessionScoped ? validateSessionStateStore(sessionStateStore) : null;
  const persistentSessionCapacity = Math.min(sessionCacheCapacity, DEFAULT_SESSION_CACHE_CAPACITY);
  const sessionCache = new Map();
  let sessionCacheNameBytes = 0;
  let admissionChain = Promise.resolve();

  const withAdmissionLock = (operation) => {
    const result = admissionChain.then(operation, operation);
    admissionChain = result.then(() => undefined, () => undefined);
    return result;
  };

  const persistSessionState = async (state) => {
    if (!state?.storageKey) throw new TypeError("session_state_key_missing");
    const record = serializeSessionProfileState(state);
    await stateStore.set(state.storageKey, record);
    state.dirty = false;
  };

  const admitSession = (sessionID, inventorySha256, names, tools) => withAdmissionLock(async () => {
    const cached = sessionCache.get(sessionID);
    if (cached) {
      if (cached.inventorySha256 !== inventorySha256) {
        blockSessionState(cached, "inventory_changed");
        await persistSessionState(cached);
        return { state: cached, drifted: true };
      }
      return { state: cached };
    }

    const cacheNameBytes =
      Buffer.byteLength(sessionID, "utf8") +
      names.reduce((sum, name) => sum + Buffer.byteLength(name, "utf8"), 0);
    if (
      sessionCache.size >= sessionCacheCapacity ||
      sessionCacheNameBytes + cacheNameBytes > sessionCacheNameByteCapacity
    ) {
      return { state: null, capacityReached: true };
    }

    const storageKey = sessionProfileStorageKey(sessionID);
    let stored = await stateStore.get(storageKey);
    if (stored === undefined) {
      const claim = await stateStore.claim(storageKey, persistentSessionCapacity);
      if (claim === "capacity") return { state: null, capacityReached: true };
      if (claim !== "created" && claim !== "existing") {
        throw new TypeError("session_state_claim_invalid");
      }
      if (claim === "existing") {
        stored = await stateStore.get(storageKey);
        if (stored === undefined) {
          // A previous process may have claimed this identity and stopped
          // before writing a profile. Reusing it would risk reselection.
          return { state: null, capacityReached: true };
        }
      }
    }
    const state = makeSessionState({ inventorySha256, names, tools, cacheNameBytes, storageKey });
    if (stored !== undefined) {
      const validation = validateStoredSessionProfileState(stored, state, registry, limits);
      if (!validation.ok) {
        blockSessionState(state, validation.reason);
      } else if (validation.blockedReason) {
        blockSessionState(state, validation.blockedReason);
      } else {
        state.profileId = validation.profileId;
        state.proposedProfileId = validation.profileId;
        state.selectionDone = true;
        state.expandedToolNames = validation.expandedToolNames;
        state.expansionCalls = validation.expansionCalls;
        state.discoveryCalls = validation.discoveryCalls;
        state.expandedSchemaBytes = validation.expandedSchemaBytes;
        state.discoveredToolNames = validation.discoveredToolNames;
      }
      // Do not overwrite an invalid or mismatched durable record. Keeping it
      // intact makes corruption and inventory drift visible after restart.
      state.dirty = false;
    } else {
      state.storageReserved = true;
    }
    sessionCache.set(sessionID, state);
    sessionCacheNameBytes += cacheNameBytes;
    return { state, stored: stored !== undefined };
  });

  const applyToolProfile = async function applyToolProfile(event) {
    const tools = event?.tools;
    let names;
    let inventorySha256;
    try {
      if (!isPlainRecord(tools)) throw new TypeError("tool_inventory_record_invalid");
      names = Object.keys(tools).sort();
      inventorySha256 = toolInventorySha256(tools);
    } catch {
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "inventory_invalid",
          toolCountBefore: Array.isArray(names) ? names.length : 0,
          toolCountAfter: Array.isArray(names) ? names.length : 0,
        }),
      );
      return;
    }

    let sessionID = null;
    let sessionState = null;
    if (sessionScoped) {
      if (typeof event.sessionID !== "string" || event.sessionID.length === 0 || event.sessionID.length > 256) {
        await emitOrThrow(
          emitReceipt,
          makeReceipt({
            outcome: "pass_through",
            reason: "session_identity_missing",
            inventorySha256,
            toolCountBefore: names.length,
            toolCountAfter: names.length,
          }),
        );
        return;
      }
      sessionID = event.sessionID;
      const admission = await admitSession(sessionID, inventorySha256, names, tools);
      sessionState = admission.state;
      if (!sessionState || admission.capacityReached) {
        await emitOrThrow(
          emitReceipt,
          makeReceipt({
            outcome: "pass_through",
            reason: "session_cache_capacity_reached",
            inventorySha256,
            toolCountBefore: names.length,
            toolCountAfter: names.length,
          }),
        );
        return;
      }
      if (sessionState.dirty) await persistSessionState(sessionState);
      if (admission.drifted) {
        await emitOrThrow(
          emitReceipt,
          makeReceipt({
            outcome: "pass_through",
            reason: "session_inventory_changed",
            inventorySha256,
            toolCountBefore: names.length,
            toolCountAfter: names.length,
          }),
        );
        return;
      }
      if (sessionState?.blockedReason) {
        await emitOrThrow(
          emitReceipt,
          makeReceipt({
            outcome: "pass_through",
            reason: sessionState.blockedReason,
            inventorySha256,
            profileId: sessionState.profileId,
            toolCountBefore: names.length,
            toolCountAfter: names.length,
          }),
        );
        return;
      }
    }

    let selectorInput;
    try {
      selectorInput = Object.freeze({
        sessionID,
        inventorySha256,
        agent: typeof event.agent === "string" ? event.agent : null,
        model: immutableJsonSnapshot(event.model ?? null),
        system: immutableJsonSnapshot(event.system ?? []),
        messages: immutableJsonSnapshot(event.messages ?? []),
        toolNames: Object.freeze([...names]),
      });
    } catch {
      if (sessionState) {
        blockSessionState(sessionState, "selector_input_invalid");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "selector_input_invalid",
          inventorySha256,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }

    let proposed;
    let timer;
    const controller = sessionState?.selectionController ?? new AbortController();
    if (sessionState?.selectionDone) {
      proposed = sessionState.proposedProfileId;
    } else {
      if (sessionState && !sessionState.selectionPromise) {
        sessionState.selectionController = controller;
        sessionState.selectionPromise = Promise.resolve()
          .then(() => selectProfile(selectorInput, { signal: controller.signal }))
          .then(
            (value) => {
              if (sessionCache.get(sessionID) === sessionState && !sessionState.blockedReason) {
                sessionState.proposedProfileId = value;
                sessionState.selectionDone = true;
              }
              return value;
            },
            () => SELECTOR_FAILED,
          );
      }
      const selection = sessionState
        ? sessionState.selectionPromise
        : Promise.resolve()
            .then(() => selectProfile(selectorInput, { signal: controller.signal }))
            .catch(() => SELECTOR_FAILED);
      try {
        proposed = await Promise.race([
          selection,
          new Promise((resolve) => {
            timer = setTimeout(() => resolve(SELECTION_TIMEOUT), selectionTimeoutMs);
          }),
        ]);
      } finally {
        if (timer !== undefined) clearTimeout(timer);
      }
      if (!sessionState && proposed === undefined) proposed = SELECTOR_FAILED;
    }

    if (proposed === SELECTION_TIMEOUT) {
      controller.abort();
      if (sessionState) {
        blockSessionState(sessionState, "selector_timeout");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "selector_timeout",
          inventorySha256,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }
    if (proposed === SELECTOR_FAILED) {
      if (sessionState) {
        blockSessionState(sessionState, "selector_failed");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "selector_failed",
          inventorySha256,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }
    if (typeof proposed !== "string" || !registry.has(proposed)) {
      if (sessionState) {
        blockSessionState(sessionState, "profile_unknown");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "profile_unknown",
          inventorySha256,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }

    const profile = registry.get(proposed);
    if (profile.inventorySha256 !== inventorySha256) {
      if (sessionState) {
        blockSessionState(sessionState, "inventory_mismatch");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "inventory_mismatch",
          inventorySha256,
          profileId: profile.id,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }
    if (profile.allowedToolNames.some((name) => !Object.hasOwn(tools, name))) {
      if (sessionState) {
        blockSessionState(sessionState, "profile_tool_unavailable");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "profile_tool_unavailable",
          inventorySha256,
          profileId: profile.id,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }
    if (
      sessionState &&
      (sessionState.blockedReason || sessionState.inventorySha256 !== inventorySha256)
    ) {
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: sessionState.blockedReason ?? "session_inventory_changed",
          inventorySha256,
          profileId: profile.id,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }

    const allowed = new Set(profile.allowedToolNames);
    if (sessionState) {
      for (const name of sessionState.expandedToolNames) allowed.add(name);
    }
    const removed = [];
    let currentInventorySha256;
    try {
      currentInventorySha256 = toolInventorySha256(tools);
    } catch {
      if (sessionState) {
        blockSessionState(sessionState, "inventory_invalid_after_selection");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "inventory_invalid_after_selection",
          inventorySha256,
          profileId: profile.id,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }
    if (currentInventorySha256 !== inventorySha256) {
      if (sessionState) {
        blockSessionState(sessionState, "inventory_changed_during_selection");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "inventory_changed_during_selection",
          inventorySha256,
          profileId: profile.id,
          toolCountBefore: names.length,
          toolCountAfter: Object.keys(tools).length,
        }),
      );
      return;
    }
    if (sessionState) {
      sessionState.profileId = profile.id;
      sessionState.proposedProfileId = profile.id;
      sessionState.selectionPromise = null;
      sessionState.selectionController = null;
      sessionState.selectionDone = true;
      sessionState.blockedReason = null;
      sessionState.dirty = true;
      try {
        await persistSessionState(sessionState);
      } catch {
        blockSessionState(sessionState, "storage_write_failed");
        try {
          await persistSessionState(sessionState);
        } catch {
          throw new Error("session_profile_storage_failed");
        }
        await emitOrThrow(
          emitReceipt,
          makeReceipt({
            outcome: "pass_through",
            reason: "storage_write_failed",
            inventorySha256,
            toolCountBefore: names.length,
            toolCountAfter: names.length,
          }),
        );
        return;
      }
    }
    try {
      for (const name of names) {
        if (allowed.has(name)) continue;
        const descriptor = Object.getOwnPropertyDescriptor(tools, name);
        if (!descriptor?.configurable) throw new TypeError("tool_entry_not_removable");
        if (!Reflect.deleteProperty(tools, name)) throw new TypeError("tool_entry_not_removable");
        removed.push([name, descriptor]);
      }
    } catch {
      restoreRemovedTools(tools, removed);
      if (sessionState) {
        blockSessionState(sessionState, "tool_map_not_mutable");
        await persistSessionState(sessionState);
      }
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: "pass_through",
          reason: "tool_map_not_mutable",
          inventorySha256,
          profileId: profile.id,
          toolCountBefore: names.length,
          toolCountAfter: names.length,
        }),
      );
      return;
    }

    try {
      await emitOrThrow(
        emitReceipt,
        makeReceipt({
          outcome: removed.length === 0 ? "unchanged" : "filtered",
          reason: removed.length === 0 ? "profile_keeps_all_tools" : "profile_applied",
          inventorySha256,
          profileId: profile.id,
          toolCountBefore: names.length,
          toolCountAfter: names.length - removed.length,
        }),
      );
    } catch {
      restoreRemovedTools(tools, removed);
      if (sessionState) {
        blockSessionState(sessionState, "receipt_failed");
        await persistSessionState(sessionState);
      }
      throw new Error("tool_profile_receipt_failed");
    }
  };

  if (sessionScoped) {
    applyToolProfile.requestExpansion = async ({ sessionID, toolNames } = {}) => {
      const state = typeof sessionID === "string" ? sessionCache.get(sessionID) : null;
      const profile = state ? registry.get(state.profileId ?? state.proposedProfileId) : null;
      const reject = async (reason, { countDiscovery = false } = {}) => {
        if (state && countDiscovery && profile) {
          const nextDiscoveryCalls = state.discoveryCalls + 1;
          const candidate = serializeSessionProfileState(state, {
            discoveryCalls: nextDiscoveryCalls,
          });
          await stateStore.set(state.storageKey, candidate);
          state.discoveryCalls = nextDiscoveryCalls;
        }
        if (state) {
          await emitOrThrow(
            emitReceipt,
            makeReceipt({
              outcome: "expansion_rejected",
              reason,
              inventorySha256: state.inventorySha256,
              profileId: profile?.id,
              toolCountBefore: (profile?.allowedToolNames.length ?? 0) + state.expandedToolNames.size,
              toolCountAfter: (profile?.allowedToolNames.length ?? 0) + state.expandedToolNames.size,
            }),
          );
        }
        throw new Error(`tool_profile_expansion_${reason}`);
      };

      if (!state || state.blockedReason || !profile || state.selectionPromise) {
        return reject("session_unavailable");
      }
      if (!Array.isArray(toolNames) || toolNames.length === 0 || toolNames.length > limits.maxToolNamesPerCall) {
        return reject("request_size_invalid");
      }
      const uniqueNames = new Set();
      for (const name of toolNames) {
        if (typeof name !== "string" || name.length === 0 || name.length > 256 || uniqueNames.has(name)) {
          return reject("tool_names_invalid");
        }
        uniqueNames.add(name);
      }
      const baseNames = new Set(profile.allowedToolNames);
      if (uniqueNames.size === 1 && uniqueNames.has("__list_available__")) {
        if (state.discoveryCalls >= limits.maxDiscoveryCallsPerSession) {
          return reject("discovery_limit_reached");
        }
        const availableToolNames = [...state.inventoryToolNames]
          .filter((name) => !baseNames.has(name) && !state.expandedToolNames.has(name))
          .sort();
        const discoveryNameBytes = availableToolNames.reduce(
          (sum, name) => sum + Buffer.byteLength(name, "utf8"),
          0,
        );
        if (discoveryNameBytes > limits.maxDiscoveryNameBytesPerSession) {
          return reject("discovery_byte_limit_reached", { countDiscovery: true });
        }
        const nextDiscoveryCalls = state.discoveryCalls + 1;
        const nextDiscoveredToolNames = new Set(state.discoveredToolNames);
        for (const name of availableToolNames) nextDiscoveredToolNames.add(name);
        await stateStore.set(state.storageKey, serializeSessionProfileState(state, {
          discoveryCalls: nextDiscoveryCalls,
          discoveredToolNames: [...nextDiscoveredToolNames],
        }));
        state.discoveryCalls = nextDiscoveryCalls;
        state.discoveredToolNames = [...nextDiscoveredToolNames];
        try {
          await emitOrThrow(
            emitReceipt,
            makeReceipt({
              outcome: "schema_discovery",
              reason: "bounded_inventory_name_listing",
              inventorySha256: state.inventorySha256,
              profileId: profile.id,
              toolCountBefore: baseNames.size + state.expandedToolNames.size,
              toolCountAfter: baseNames.size + state.expandedToolNames.size,
              schemaDiscovery: {
                call: nextDiscoveryCalls,
                tool_names: availableToolNames,
              },
            }),
          );
        } catch {
          blockSessionState(state, "receipt_failed");
          await persistSessionState(state);
          throw new Error("tool_profile_receipt_failed");
        }
        return Object.freeze({
          inventorySha256: state.inventorySha256,
          toolNames: Object.freeze([]),
          availableToolNames: Object.freeze(availableToolNames),
        });
      }
      if (state.expansionCalls >= limits.maxCallsPerSession) return reject("call_limit_reached");
      const additions = [...uniqueNames].filter((name) => !baseNames.has(name) && !state.expandedToolNames.has(name));
      if (additions.some((name) => !state.inventoryToolNames.has(name))) {
        return reject("tool_outside_inventory");
      }
      if (state.expandedToolNames.size + additions.length > limits.maxExpandedToolsPerSession) {
        return reject("session_tool_limit_reached");
      }
      const schemaBytes = additions.reduce((sum, name) => sum + (state.schemaBytes.get(name) ?? 0), 0);
      if (state.expandedSchemaBytes + schemaBytes > limits.maxSchemaBytesPerSession) {
        return reject("session_byte_limit_reached");
      }

      const nextExpandedToolNames = new Set(state.expandedToolNames);
      for (const name of additions) nextExpandedToolNames.add(name);
      const nextExpansionCalls = state.expansionCalls + 1;
      const nextExpandedSchemaBytes = state.expandedSchemaBytes + schemaBytes;
      await stateStore.set(state.storageKey, serializeSessionProfileState(state, {
        expandedToolNames: [...nextExpandedToolNames],
        expansionCalls: nextExpansionCalls,
        expandedSchemaBytes: nextExpandedSchemaBytes,
      }));
      state.expandedToolNames = nextExpandedToolNames;
      state.expansionCalls = nextExpansionCalls;
      state.expandedSchemaBytes = nextExpandedSchemaBytes;
      try {
        await emitOrThrow(
          emitReceipt,
          makeReceipt({
            outcome: additions.length === 0 ? "expansion_unchanged" : "schema_expansion",
            reason: additions.length === 0 ? "tools_already_available" : "bounded_on_demand_expansion",
            inventorySha256: state.inventorySha256,
            profileId: profile.id,
            toolCountBefore: baseNames.size + state.expandedToolNames.size - additions.length,
            toolCountAfter: baseNames.size + state.expandedToolNames.size,
            schemaExpansion: {
              call: nextExpansionCalls,
              added_count: additions.length,
              added_bytes: schemaBytes,
              tool_names: additions,
            },
          }),
        );
      } catch {
        blockSessionState(state, "receipt_failed");
        await persistSessionState(state);
        throw new Error("tool_profile_receipt_failed");
      }
      return Object.freeze({
        inventorySha256: state.inventorySha256,
        toolNames: Object.freeze(additions),
        expansionCallsRemaining: limits.maxCallsPerSession - nextExpansionCalls,
      });
    };
  }
  return applyToolProfile;
}

/**
 * Build a disabled-by-default plugin body; wrap it in Plugin.define at the
 * OpenCode entry point after a local selector and durable receipt sink exist.
 */
export function createToolProfilePlugin({
  enabled = false,
  providerID = "wrench-subroute",
  profiles,
  selectProfile,
  emitReceipt,
  selectionTimeoutMs = 1500,
  sessionScoped = false,
  sessionStateStore,
  expansionToolName = "wrench_expand_tools",
  sessionCacheCapacity = DEFAULT_SESSION_CACHE_CAPACITY,
  sessionCacheNameByteCapacity = DEFAULT_SESSION_CACHE_NAME_BYTE_CAPACITY,
  expansionLimits = DEFAULT_EXPANSION_LIMITS,
}) {
  if (typeof enabled !== "boolean") throw new TypeError("enabled_must_be_boolean");
  return {
    id: TOOL_PROFILE_HOOK_ID,
    async setup(context) {
      if (!enabled) return;
      if (typeof providerID !== "string" || providerID.length === 0) {
        throw new TypeError("provider_id_invalid");
      }
      if (typeof context?.session?.hook !== "function") {
        throw new TypeError("session_context_hook_unavailable");
      }
      const callback = createToolProfileHook({
        enabled: true,
        profiles,
        selectProfile,
        emitReceipt,
        selectionTimeoutMs,
        sessionScoped,
        sessionStateStore,
        expansionToolName,
        sessionCacheCapacity,
        sessionCacheNameByteCapacity,
        expansionLimits,
      });
      let toolRegistration;
      if (sessionScoped) {
        if (typeof context?.tool?.transform !== "function") {
          throw new TypeError("tool_transform_unavailable");
        }
        toolRegistration = await context.tool.transform((editor) => {
          const definition = createToolExpansionDefinition(expansionLimits);
          editor.add({
            name: expansionToolName,
            ...definition,
            execute: async (input, toolContext) => {
              const expanded = await callback.requestExpansion({
                sessionID: toolContext?.sessionID,
                toolNames: input?.toolNames,
              });
              const detail = expanded.availableToolNames
                ? `Omitted tool names: ${expanded.availableToolNames.join(", ")}. Call this tool again with the names to expose their schemas.`
                : expanded.toolNames.length
                  ? `Available on the next request: ${expanded.toolNames.join(", ")}.`
                  : "Those tools are already available in this session.";
              return { content: detail };
            },
          });
        });
        if (typeof toolRegistration?.dispose !== "function") {
          throw new TypeError("expansion_tool_registration_invalid");
        }
      }
      let registration;
      try {
        registration = await context.session.hook("context", callback, { providerID });
      } catch (error) {
        await toolRegistration?.dispose?.();
        throw error;
      }
      if (typeof registration?.dispose !== "function") {
        await toolRegistration?.dispose?.();
        throw new TypeError("context_hook_registration_invalid");
      }
      let disposed = false;
      return async () => {
        if (disposed) return;
        disposed = true;
        await registration.dispose();
        await toolRegistration?.dispose?.();
      };
    },
  };
}
