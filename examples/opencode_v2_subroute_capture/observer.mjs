import { createHash } from "node:crypto";
import { lstat, mkdir, open, realpath } from "node:fs/promises";
import path from "node:path";
import { SYNTHETIC_FIXTURE } from "./synthetic-fixtures.mjs";

export const OPENCODE_VERSION = "2.0.12";
export const SUBROUTE_URL = SYNTHETIC_FIXTURE.route_identity;
export const MAX_REQUEST_BYTES = 1_048_576;
export const MAX_RESPONSE_BYTES = 65_536;
export const MAX_RECEIPT_BYTES = 2 * 1_048_576;

const RECEIPT_ROOT = String.raw`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\opencode-http-capture`;
const RECEIPT_PATHS = Object.freeze({
  baseline: path.join(RECEIPT_ROOT, "opencode-v2-0-12-preflight-baseline.jsonl"),
  wrench: path.join(RECEIPT_ROOT, "opencode-v2-0-12-preflight-wrench.jsonl"),
});
const RESPONSE_RECEIPT_PATHS = Object.freeze({
  baseline: path.join(RECEIPT_ROOT, "opencode-v2-0-12-response-baseline.jsonl"),
  wrench: path.join(RECEIPT_ROOT, "opencode-v2-0-12-response-wrench.jsonl"),
});
const MAX_RECEIPT_LINE_BYTES = 4096;

export class SyntheticCaptureError extends Error {
  constructor(code) {
    super(code);
    this.name = "SyntheticCaptureError";
    this.code = code;
  }
}

export function syntheticJsonSha256(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new SyntheticCaptureError("request_shape_invalid");
  }
  return sha256(new TextEncoder().encode(JSON.stringify(body)));
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function routeIsExact(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return false;
  }
  return parsed.href === SUBROUTE_URL;
}

async function assertNoPathLinks(targetPath) {
  const absolutePath = path.resolve(targetPath);
  const { root } = path.parse(absolutePath);
  const components = path.relative(root, absolutePath).split(path.sep).filter(Boolean);
  let currentPath = root;
  for (const component of components) {
    currentPath = path.join(currentPath, component);
    let details;
    try {
      details = await lstat(currentPath);
    } catch (error) {
      if (error?.code === "ENOENT") return;
      throw new SyntheticCaptureError("receipt_path_unavailable");
    }
    if (details.isSymbolicLink()) {
      throw new SyntheticCaptureError("receipt_path_redirected");
    }
    let resolvedPath;
    try {
      resolvedPath = await realpath(currentPath);
    } catch {
      throw new SyntheticCaptureError("receipt_path_unavailable");
    }
    const comparable = (value) => value.replace(/^\\\\\?\\/, "").replace(/[\\/]+$/, "").toLowerCase();
    if (comparable(resolvedPath) !== comparable(currentPath)) {
      throw new SyntheticCaptureError("receipt_path_redirected");
    }
  }
}

function assertNoDuplicateJsonKeys(text) {
  let index = 0;
  const skipWhitespace = () => {
    while (index < text.length && " \t\r\n".includes(text[index])) index += 1;
  };
  const readString = () => {
    const start = index;
    index += 1;
    while (index < text.length) {
      if (text[index] === "\\") {
        index += 2;
        continue;
      }
      if (text[index] === '"') {
        index += 1;
        return JSON.parse(text.slice(start, index));
      }
      index += 1;
    }
    throw new SyntheticCaptureError("request_json_invalid");
  };
  const readValue = () => {
    skipWhitespace();
    if (text[index] === '"') {
      readString();
      return;
    }
    if (text[index] === "{") {
      index += 1;
      skipWhitespace();
      const keys = new Set();
      if (text[index] === "}") {
        index += 1;
        return;
      }
      while (index < text.length) {
        skipWhitespace();
        if (text[index] !== '"') throw new SyntheticCaptureError("request_json_invalid");
        const key = readString();
        if (keys.has(key)) throw new SyntheticCaptureError("duplicate_json_key");
        keys.add(key);
        skipWhitespace();
        if (text[index] !== ":") throw new SyntheticCaptureError("request_json_invalid");
        index += 1;
        readValue();
        skipWhitespace();
        if (text[index] === "}") {
          index += 1;
          return;
        }
        if (text[index] !== ",") throw new SyntheticCaptureError("request_json_invalid");
        index += 1;
      }
      throw new SyntheticCaptureError("request_json_invalid");
    }
    if (text[index] === "[") {
      index += 1;
      skipWhitespace();
      if (text[index] === "]") {
        index += 1;
        return;
      }
      while (index < text.length) {
        readValue();
        skipWhitespace();
        if (text[index] === "]") {
          index += 1;
          return;
        }
        if (text[index] !== ",") throw new SyntheticCaptureError("request_json_invalid");
        index += 1;
      }
      throw new SyntheticCaptureError("request_json_invalid");
    }
    const start = index;
    while (index < text.length && !" \t\r\n,]}".includes(text[index])) index += 1;
    if (index === start) throw new SyntheticCaptureError("request_json_invalid");
  };

  readValue();
  skipWhitespace();
  if (index !== text.length) throw new SyntheticCaptureError("request_json_invalid");
}

async function readBoundedBody(request) {
  if (!request.body) throw new SyntheticCaptureError("request_body_missing");
  const declaredLength = request.headers.get("content-length");
  if (/^\d+$/.test(declaredLength || "") && Number(declaredLength) > MAX_REQUEST_BYTES) {
    throw new SyntheticCaptureError("request_body_too_large");
  }
  const reader = request.clone().body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_REQUEST_BYTES) {
        void reader.cancel().catch(() => {});
        throw new SyntheticCaptureError("request_body_too_large");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

async function readBoundedResponse(response) {
  if (!(response instanceof Response) || !response.body) {
    throw new SyntheticCaptureError("response_body_missing");
  }
  const declaredLength = response.headers.get("content-length");
  if (/^\d+$/.test(declaredLength || "") && Number(declaredLength) > MAX_RESPONSE_BYTES) {
    throw new SyntheticCaptureError("response_body_too_large");
  }
  const reader = response.clone().body.getReader();
  const chunks = [];
  let totalBytes = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    totalBytes += value.byteLength;
    if (totalBytes > MAX_RESPONSE_BYTES) {
      void reader.cancel().catch(() => {});
      throw new SyntheticCaptureError("response_body_too_large");
    }
    chunks.push(value);
  }
  const body = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

function parseResponseJson(text) {
  assertNoDuplicateJsonKeys(text);
  try {
    return JSON.parse(text);
  } catch {
    throw new SyntheticCaptureError("response_json_invalid");
  }
}

function responsePayloads(text, isEventStream) {
  if (!isEventStream) return [parseResponseJson(text)];
  const payloads = [];
  let dataLines = [];
  const flush = () => {
    if (dataLines.length === 0) return;
    const data = dataLines.join("\n").trim();
    dataLines = [];
    if (!data || data === "[DONE]") return;
    payloads.push(parseResponseJson(data));
  };
  for (const line of text.split(/\r?\n/u)) {
    if (line === "") {
      flush();
      continue;
    }
    if (line.startsWith(":")) continue;
    if (line.startsWith("data:")) {
      const value = line.slice(5);
      dataLines.push(value.startsWith(" ") ? value.slice(1) : value);
    }
  }
  flush();
  return payloads;
}

function parseSyntheticBody(bytes) {
  let body;
  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    assertNoDuplicateJsonKeys(text);
    body = JSON.parse(text);
  } catch (error) {
    if (error instanceof SyntheticCaptureError && error.code === "duplicate_json_key") throw error;
    throw new SyntheticCaptureError("request_json_invalid");
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new SyntheticCaptureError("request_shape_invalid");
  }
  if (syntheticJsonSha256(body) !== SYNTHETIC_FIXTURE.normalized_request_sha256) {
    throw new SyntheticCaptureError("synthetic_template_hash_mismatch");
  }
  if (body.model !== SYNTHETIC_FIXTURE.model_alias || !Array.isArray(body.messages)) {
    throw new SyntheticCaptureError("synthetic_template_mismatch");
  }
  const roleCounts = Object.create(null);
  for (const message of body.messages) {
    if (!message || typeof message !== "object" || Array.isArray(message)) {
      throw new SyntheticCaptureError("message_invalid");
    }
    if (!["system", "developer", "user"].includes(message.role)) {
      throw new SyntheticCaptureError("non_synthetic_history_refused");
    }
    roleCounts[message.role] = (roleCounts[message.role] || 0) + 1;
  }
  const userMessages = body.messages.filter((message) => message.role === "user");
  if (
    userMessages.length !== 1 ||
    userMessages[0].content !== `WRENCH_SYNTHETIC_FIXTURE:${SYNTHETIC_FIXTURE.run_id}`
  ) {
    throw new SyntheticCaptureError("synthetic_marker_mismatch");
  }
  if (body.tools !== undefined && !Array.isArray(body.tools)) {
    throw new SyntheticCaptureError("tools_invalid");
  }
  return {
    modelAlias: SYNTHETIC_FIXTURE.model_alias,
    messageCount: body.messages.length,
    roleCounts: Object.fromEntries(Object.entries(roleCounts).sort(([a], [b]) => a.localeCompare(b))),
    toolSchemaCount: Array.isArray(body.tools) ? body.tools.length : 0,
  };
}

export function createSyntheticRequestObserver({ enabled, arm, emit, state }) {
  if (!enabled) return async () => ({ captured: false, reason: "disabled" });
  if (arm !== "baseline" && arm !== "wrench") {
    throw new SyntheticCaptureError("arm_invalid");
  }
  if (typeof emit !== "function") throw new SyntheticCaptureError("receipt_sink_missing");
  if (!state || typeof state !== "object") throw new SyntheticCaptureError("capture_state_missing");
  let captured = false;

  return async (event) => {
    if (captured) throw new SyntheticCaptureError("request_count_limit");
    if (!event || event.kind !== "primary") {
      throw new SyntheticCaptureError("request_kind_refused");
    }
    if (typeof event.sessionID !== "string" || !event.sessionID || event.sessionID.length > 256) {
      throw new SyntheticCaptureError("session_id_invalid");
    }
    const request = event.request;
    if (!(request instanceof Request) || request.method !== "POST" || !routeIsExact(request.url)) {
      throw new SyntheticCaptureError("route_or_method_refused");
    }
    const bytes = await readBoundedBody(request);
    const parsed = parseSyntheticBody(bytes);
    const receipt = {
      schema_version: "wrench.opencode-http-hook-receipt.v1",
      opencode_version: OPENCODE_VERSION,
      route_identity: SUBROUTE_URL,
      fixture_id: SYNTHETIC_FIXTURE.fixture_id,
      run_id: SYNTHETIC_FIXTURE.run_id,
      pair_id: SYNTHETIC_FIXTURE.pair_id,
      arm,
      request_ordinal: 1,
      body_bytes: bytes.byteLength,
      model_alias: parsed.modelAlias,
      message_count: parsed.messageCount,
      role_counts: parsed.roleCounts,
      tool_schema_count: parsed.toolSchemaCount,
      input_tokens: null,
      provider: null,
      billed_cost: null,
    };
    captured = true;
    await emit(receipt);
    state.sessionID = event.sessionID;
    return { captured: true, receipt };
  };
}

export function createSyntheticResponseObserver({ enabled, arm, emit, state }) {
  if (!enabled) return async () => ({ captured: false, reason: "disabled" });
  if (arm !== "baseline" && arm !== "wrench") {
    throw new SyntheticCaptureError("arm_invalid");
  }
  if (typeof emit !== "function") throw new SyntheticCaptureError("receipt_sink_missing");
  if (!state || typeof state !== "object") throw new SyntheticCaptureError("capture_state_missing");
  let captured = false;

  return async (event) => {
    if (captured) throw new SyntheticCaptureError("response_count_limit");
    if (!event || event.kind !== "primary") {
      throw new SyntheticCaptureError("response_kind_refused");
    }
    if (!state.sessionID || event.sessionID !== state.sessionID) {
      throw new SyntheticCaptureError("response_session_mismatch");
    }
    const response = event.response;
    if (!(response instanceof Response) || response.status !== 200) {
      throw new SyntheticCaptureError("response_status_or_shape_refused");
    }
    const bytes = await readBoundedResponse(response);
    let payloads;
    try {
      const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
      const contentType = response.headers.get("content-type") || "";
      const isEventStream = contentType.toLowerCase().includes("text/event-stream")
        || text.trimStart().startsWith("data:");
      payloads = responsePayloads(text, isEventStream);
    } catch (error) {
      if (error instanceof SyntheticCaptureError && error.code === "duplicate_json_key") throw error;
      throw new SyntheticCaptureError("response_json_invalid");
    }
    let responseModel;
    let usage;
    for (const payload of payloads) {
      if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        throw new SyntheticCaptureError("response_object_required");
      }
      if (typeof payload.model === "string" && payload.model) responseModel = payload.model;
      else if (payload.model !== undefined && payload.model !== "") {
        throw new SyntheticCaptureError("response_model_invalid");
      }
      if (payload.usage !== undefined && payload.usage !== null) {
        if (usage !== undefined) throw new SyntheticCaptureError("provider_usage_duplicate");
        usage = payload.usage;
      }
    }
    if (!usage || typeof usage !== "object" || Array.isArray(usage)) {
      throw new SyntheticCaptureError("provider_usage_missing");
    }
    const validCount = (value) => Number.isSafeInteger(value) && value >= 0;
    if (!validCount(usage.prompt_tokens) || !validCount(usage.completion_tokens)) {
      throw new SyntheticCaptureError("provider_usage_invalid");
    }
    const totalTokens = usage.prompt_tokens + usage.completion_tokens;
    if (!Number.isSafeInteger(totalTokens)) {
      throw new SyntheticCaptureError("provider_total_tokens_invalid");
    }
    if (usage.total_tokens !== undefined && usage.total_tokens !== totalTokens) {
      throw new SyntheticCaptureError("provider_total_tokens_mismatch");
    }
    const details = usage.prompt_tokens_details ?? {};
    if (!details || typeof details !== "object" || Array.isArray(details)) {
      throw new SyntheticCaptureError("provider_usage_details_invalid");
    }
    const cachedInputTokens = details.cached_tokens ?? 0;
    if (!validCount(cachedInputTokens) || cachedInputTokens > usage.prompt_tokens) {
      throw new SyntheticCaptureError("provider_cached_tokens_invalid");
    }
    if (typeof responseModel !== "string" || !responseModel || responseModel.length > 256 || /[\u0000-\u001f\u007f]/u.test(responseModel)) {
      throw new SyntheticCaptureError("response_model_invalid");
    }
    const receipt = {
      schema_version: "wrench.opencode-http-response-usage-receipt.v1",
      opencode_version: OPENCODE_VERSION,
      fixture_id: SYNTHETIC_FIXTURE.fixture_id,
      run_id: SYNTHETIC_FIXTURE.run_id,
      pair_id: SYNTHETIC_FIXTURE.pair_id,
      arm,
      response_ordinal: 1,
      http_status: response.status,
      response_model: responseModel,
      input_tokens: usage.prompt_tokens,
      output_tokens: usage.completion_tokens,
      total_tokens: totalTokens,
      cached_input_tokens: cachedInputTokens,
      response_metadata_sha256: sha256(new TextEncoder().encode(JSON.stringify({
        model: responseModel,
        usage,
        http_status: response.status,
      }))),
      provider: null,
      billed_cost: null,
      billing_verified: false,
    };
    captured = true;
    await emit(receipt);
    return { captured: true, receipt };
  };
}

export function createNoProviderHttpHook(observer) {
  if (typeof observer !== "function") throw new SyntheticCaptureError("observer_missing");
  return async (event) => {
    await observer(event);
    throw new SyntheticCaptureError("provider_transport_disabled");
  };
}

export function createBoundedReceiptSink(arm) {
  if (arm !== "baseline" && arm !== "wrench") {
    throw new SyntheticCaptureError("arm_invalid");
  }
  const outputPath = RECEIPT_PATHS[arm];
  const rootPrefix = `${path.resolve(RECEIPT_ROOT)}${path.sep}`;
  if (!path.resolve(outputPath).startsWith(rootPrefix)) {
    throw new SyntheticCaptureError("receipt_path_invalid");
  }
  let written = false;

  return {
    async emit(receipt) {
      if (written) throw new SyntheticCaptureError("request_count_limit");
      const line = `${JSON.stringify(receipt)}\n`;
      const lineBytes = Buffer.byteLength(line, "utf8");
      if (lineBytes > MAX_RECEIPT_LINE_BYTES || lineBytes > MAX_RECEIPT_BYTES) {
        throw new SyntheticCaptureError("receipt_byte_limit");
      }
      written = true;
      await assertNoPathLinks(RECEIPT_ROOT);
      await mkdir(RECEIPT_ROOT, { recursive: true });
      await assertNoPathLinks(RECEIPT_ROOT);
      const handle = await open(outputPath, "wx");
      try {
        await handle.writeFile(line, { encoding: "utf8" });
      } finally {
        await handle.close();
      }
    },
  };
}

export function createBoundedResponseReceiptSink(arm) {
  if (arm !== "baseline" && arm !== "wrench") {
    throw new SyntheticCaptureError("arm_invalid");
  }
  const outputPath = RESPONSE_RECEIPT_PATHS[arm];
  const rootPrefix = `${path.resolve(RECEIPT_ROOT)}${path.sep}`;
  if (!path.resolve(outputPath).startsWith(rootPrefix)) {
    throw new SyntheticCaptureError("receipt_path_invalid");
  }
  let written = false;

  return {
    async emit(receipt) {
      if (written) throw new SyntheticCaptureError("response_count_limit");
      const line = `${JSON.stringify(receipt)}\n`;
      const lineBytes = Buffer.byteLength(line, "utf8");
      if (lineBytes > MAX_RECEIPT_LINE_BYTES || lineBytes > MAX_RECEIPT_BYTES) {
        throw new SyntheticCaptureError("receipt_byte_limit");
      }
      written = true;
      await assertNoPathLinks(RECEIPT_ROOT);
      await mkdir(RECEIPT_ROOT, { recursive: true });
      await assertNoPathLinks(RECEIPT_ROOT);
      const handle = await open(outputPath, "wx");
      try {
        await handle.writeFile(line, { encoding: "utf8" });
      } finally {
        await handle.close();
      }
    },
  };
}
