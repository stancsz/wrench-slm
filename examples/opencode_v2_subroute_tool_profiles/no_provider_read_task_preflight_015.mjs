import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const TOOL_PROFILES = path.join(ROOT, "examples", "opencode_v2_subroute_tool_profiles", "tool_profiles.mjs");
const APPROVED_ROOT = String.raw`C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp`;
const JOB_ROOT = path.join(APPROVED_ROOT, "opencode-read-task-015-20260928");
const RECEIPT_PATH = path.join(APPROVED_ROOT, "opencode-read-task-015.json");
const OPENCODE_BIN = String.raw`C:\Users\stanc\.local\tools\node-v24.19.0-win-x64\node_modules\@opencode\cli\bin\opencode.exe`;
const PYTHON = String.raw`C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe`;
const MAX_REQUEST_BYTES = 4 * 1024 * 1024;
const TASK_SOURCE = "MAX_RETRY_DELAY_SECONDS = 37\nBACKOFF_SECONDS = (1, 2, 4, 8)\n";
const TASK_SOURCE_PATH = "src/retry_policy.py";
const MOCK_RESPONSE_TEXT = "MAX_RETRY_DELAY_SECONDS is 37 (line 1). BACKOFF_SECONDS sums to 15 (line 2).";
const SYNTHETIC_PROMPT = "Read src/retry_policy.py. Report MAX_RETRY_DELAY_SECONDS and the sum of BACKOFF_SECONDS, with exact line numbers.";
const PROFILE_KEEP = new Set(["read"]);

const sha256 = (value) => createHash("sha256").update(value).digest("hex");

async function appendJsonLine(filePath, value) {
  await writeFile(filePath, `${JSON.stringify(value)}\n`, { flag: "a", encoding: "utf8" });
}

function makeProviderConfig(baseUrl) {
  return {
    $schema: "https://opencode.ai/config.json",
    provider: {
      "wrench-subroute": {
        npm: "@ai-sdk/openai-compatible",
        name: "Wrench local no-provider test receiver",
        options: { baseURL: baseUrl, apiKey: "local-test-key-not-a-credential" },
        models: {
          openrouter: {
            name: "local-mock-only",
            limit: { context: 32768, output: 512 },
          },
        },
      },
    },
  };
}

function makeProbePluginSource(receiptPath, inventoryPath, eventShapePath) {
  const moduleUrl = pathToFileURL(TOOL_PROFILES).href;
  return `
import { createToolProfilePlugin } from ${JSON.stringify(moduleUrl)};
import { appendFile } from "node:fs/promises";
const append = async (file, value) => appendFile(file, JSON.stringify(value) + "\\n", "utf8");
const implementation = createToolProfilePlugin({
  enabled: true,
  providerID: "wrench-subroute",
  profiles: [{ id: "probe-placeholder-v1", inventorySha256: "${"0".repeat(64)}", allowedToolNames: ["read"] }],
  selectProfile: async (input) => {
    await append(${JSON.stringify(inventoryPath)}, {
      inventory_sha256: input.inventorySha256,
      tool_names: input.toolNames,
    });
    return null;
  },
  emitReceipt: async (receipt) => append(${JSON.stringify(receiptPath)}, receipt),
});
const describe = (value, depth = 0) => {
  if (value === null) return { kind: "null" };
  if (typeof value !== "object") return { kind: typeof value };
  const prototype = Object.getPrototypeOf(value);
  const kind = Array.isArray(value) ? "array" : prototype === null ? "null_prototype_object" : prototype === Object.prototype ? "plain_object" : "custom_object";
  const keys = Object.keys(value);
  const result = { kind, own_key_count: Reflect.ownKeys(value).length, enumerable_keys: keys.slice(0, 24) };
  if (Array.isArray(value)) result.length = value.length;
  if (depth < 2) {
    result.children = Object.fromEntries(keys.slice(0, 12).map((key) => {
      const descriptor = Object.getOwnPropertyDescriptor(value, key);
      return [key, !descriptor || !Object.hasOwn(descriptor, "value")
        ? { kind: "accessor" }
        : describe(descriptor.value, depth + 1)];
    }));
  }
  return result;
};
export default {
  id: implementation.id,
  async setup(context) {
    const session = Object.create(context.session);
    session.hook = async (hookName, callback, options) => context.session.hook(
      hookName,
      async (event) => {
        if (hookName === "context") {
          await append(${JSON.stringify(eventShapePath)}, {
            hook_name: hookName,
            agent: describe(event.agent),
            model: describe(event.model),
            system: describe(event.system),
            messages: describe(event.messages),
            tools: describe(event.tools),
            options: describe(event.options),
          });
        }
        return callback(event);
      },
      options,
    );
    const wrappedContext = Object.create(context);
    Object.defineProperty(wrappedContext, "session", { value: session });
    return implementation.setup(wrappedContext);
  },
};
`;
}

function makeFilteredPluginSource(profile, receiptPath) {
  const moduleUrl = pathToFileURL(TOOL_PROFILES).href;
  return `
import { createToolProfilePlugin } from ${JSON.stringify(moduleUrl)};
import { appendFile } from "node:fs/promises";
const profile = ${JSON.stringify(profile)};
const append = async (file, value) => appendFile(file, JSON.stringify(value) + "\\n", "utf8");
const implementation = createToolProfilePlugin({
  enabled: true,
  providerID: "wrench-subroute",
  profiles: [profile],
  selectProfile: async () => profile.id,
  emitReceipt: async (receipt) => append(${JSON.stringify(receiptPath)}, receipt),
});
export default { id: implementation.id, setup: implementation.setup };
`;
}

function responseFor(body, toolCall) {
  const id = "chatcmpl-wrench-read-task-015";
  const model = "local-mock-only";
  const choice = toolCall
    ? {
      index: 0,
      message: {
        role: "assistant",
        tool_calls: [{
          id: "call_wrench_read_task_015",
          type: "function",
          function: { name: "read", arguments: JSON.stringify(toolCall.arguments) },
        }],
      },
      finish_reason: "tool_calls",
    }
    : {
      index: 0,
      message: { role: "assistant", content: MOCK_RESPONSE_TEXT },
      finish_reason: "stop",
    };
  if (body.stream === true) {
    const chunks = toolCall
      ? [
        { role: "assistant" },
        { tool_calls: [{
          index: 0,
          id: "call_wrench_read_task_015",
          type: "function",
          function: { name: "read", arguments: JSON.stringify(toolCall.arguments) },
        }] },
        {},
      ]
      : [{ role: "assistant", content: MOCK_RESPONSE_TEXT }, {}];
    const finishReason = toolCall ? "tool_calls" : "stop";
    return chunks.map((delta, index) => {
      const chunk = {
        id,
        object: "chat.completion.chunk",
        created: 0,
        model,
        choices: [{ index: 0, delta, finish_reason: index === chunks.length - 1 ? finishReason : null }],
      };
      return `data: ${JSON.stringify(chunk)}\n\n`;
    }).join("") + "data: [DONE]\n\n";
  }
  return JSON.stringify({ id, object: "chat.completion", created: 0, model, choices: [choice] });
}

function startMockReceiver() {
  const captured = [];
  const verification = { baseline: [], filtered: [] };
  const rejections = [];
  let activeArm = null;
  const server = createServer(async (request, response) => {
    const peer = request.socket.remoteAddress;
    if (peer !== "127.0.0.1" && peer !== "::ffff:127.0.0.1") {
      response.writeHead(403).end();
      return;
    }
    if (request.method === "GET" && request.url === "/v1/models") {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify({ data: [{ id: "openrouter", object: "model" }] }));
      return;
    }
    if (request.method !== "POST" || request.url !== "/v1/chat/completions") {
      response.writeHead(404).end();
      return;
    }
    const chunks = [];
    let size = 0;
    request.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_REQUEST_BYTES) request.destroy(new Error("mock_request_limit_exceeded"));
      else chunks.push(chunk);
    });
    request.on("end", () => {
      try {
        if (!activeArm) throw new Error("unexpected_mock_request");
        const raw = Buffer.concat(chunks);
        const body = JSON.parse(raw.toString("utf8"));
        if (!Array.isArray(body.messages)) throw new Error("request_messages_missing");
        const requestIndex = captured.filter((row) => row.arm === activeArm).length;
        captured.push({ arm: activeArm, url: request.url, raw, body });
        const toolResult = body.messages.find((message) =>
          message?.role === "tool" || (message?.role === "function" && message?.name === "read"));
        let toolCall = null;
        if (toolResult) {
          const content = typeof toolResult.content === "string" ? toolResult.content : JSON.stringify(toolResult.content);
          const verified = content.includes("MAX_RETRY_DELAY_SECONDS = 37") &&
            content.includes("BACKOFF_SECONDS = (1, 2, 4, 8)");
          verification[activeArm].push({ phase: "tool_result", tool_name: "read", verified, result_sha256: sha256(content) });
          if (!verified) throw new Error("read_tool_result_did_not_contain_fixture_source");
        } else {
          const readTool = Array.isArray(body.tools)
            ? body.tools.find((tool) => tool?.function?.name === "read")
            : null;
          if (!readTool) throw new Error("read_tool_missing_from_request");
          const properties = readTool.function?.parameters?.properties ?? {};
          const pathKey = Object.keys(properties).find((name) => /^(file)?path$/i.test(name)) ??
            Object.keys(properties).find((name) => /file.*path|path/i.test(name));
          if (!pathKey) throw new Error("read_tool_path_argument_missing");
          const args = { [pathKey]: TASK_SOURCE_PATH };
          for (const name of readTool.function.parameters?.required ?? []) {
            if (Object.hasOwn(args, name)) continue;
            const property = properties[name] ?? {};
            if (["integer", "number"].includes(property.type)) args[name] = 1;
            else if (property.type === "boolean") args[name] = false;
            else throw new Error("unsupported_required_read_argument");
          }
          toolCall = { arguments: args };
          verification[activeArm].push({ phase: "tool_call", tool_name: "read", arguments_sha256: sha256(JSON.stringify(args)), request_index: requestIndex });
        }
        const payload = responseFor(body, toolCall);
        response.writeHead(200, {
          "content-type": body.stream === true ? "text/event-stream" : "application/json",
          "cache-control": "no-cache",
          connection: "close",
        });
        response.end(payload);
      } catch (error) {
        const reason = String(error?.message ?? "mock_request_rejected").replaceAll(/[\r\n]+/g, " ").slice(0, 160);
        rejections.push({ arm: activeArm, request_index: captured.filter((row) => row.arm === activeArm).length - 1, reason });
        failureDiagnostics = { mock_rejections: rejections };
        response.writeHead(400, { "content-type": "application/json" });
        response.end(JSON.stringify({ error: { message: "synthetic_preflight_rejected" } }));
      }
    });
  });
  return {
    captured,
    verification,
    rejections,
    setArm(value) { activeArm = value; },
    listen() {
      return new Promise((resolve, reject) => {
        server.once("error", reject);
        server.listen(0, "127.0.0.1", () => {
          server.removeListener("error", reject);
          resolve(server.address().port);
        });
      });
    },
    close() { return new Promise((resolve) => server.close(() => resolve())); },
  };
}

function isolatedEnvironment(home, configDir, tempDir) {
  const env = {};
  for (const key of ["SystemRoot", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "PROCESSOR_ARCHITECTURE"]) {
    if (process.env[key]) env[key] = process.env[key];
  }
  Object.assign(env, {
    USERPROFILE: home,
    HOME: home,
    APPDATA: path.join(home, "Roaming"),
    LOCALAPPDATA: path.join(home, "Local"),
    XDG_CONFIG_HOME: configDir,
    XDG_DATA_HOME: path.join(home, "data"),
    XDG_CACHE_HOME: path.join(home, "cache"),
    XDG_STATE_HOME: path.join(home, "state"),
    TEMP: tempDir,
    TMP: tempDir,
    OPENCODE_CONFIG_DIR: configDir,
    NPM_CONFIG_OFFLINE: "true",
    npm_config_offline: "true",
    NO_PROXY: "127.0.0.1,localhost",
    no_proxy: "127.0.0.1,localhost",
  });
  return env;
}

async function runOpenCode({ root, arm, baseUrl, pluginSource, inventoryPath, profileReceiptPath }) {
  const project = path.join(root, "shared", "project");
  const home = path.join(root, "shared", "home");
  const configDir = path.join(home, "config");
  const tempDir = path.join(home, "tmp");
  const pluginDir = path.join(project, ".opencode", "plugins", "wrench-tool-profiles");
  const receiptDir = path.join(project, "receipts");
  await Promise.all([
    mkdir(pluginDir, { recursive: true }),
    mkdir(configDir, { recursive: true }),
    mkdir(tempDir, { recursive: true }),
    mkdir(receiptDir, { recursive: true }),
    mkdir(path.join(project, "src"), { recursive: true }),
  ]);
  await writeFile(path.join(project, TASK_SOURCE_PATH), TASK_SOURCE);
  await writeFile(path.join(configDir, "opencode.json"), JSON.stringify({ autoupdate: false }));
  await writeFile(path.join(project, "opencode.json"), JSON.stringify(makeProviderConfig(baseUrl), null, 2));
  await writeFile(path.join(pluginDir, "index.ts"), pluginSource);
  const env = isolatedEnvironment(home, configDir, tempDir);
  if (inventoryPath) env.WRENCH_TOOL_PROFILE_INVENTORY_PATH = inventoryPath;
  env.WRENCH_TOOL_PROFILE_RECEIPT_PATH = profileReceiptPath;

  const args = [
    "run", "--standalone", "--format", "json", "--model", "wrench-subroute/openrouter",
    "--log-level", "debug", "--print-logs", "--title", `synthetic-${arm}`, SYNTHETIC_PROMPT,
  ];
  const stdout = [];
  const stderr = [];
  const startedAt = Date.now();
  const child = spawn(OPENCODE_BIN, args, { cwd: project, env, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
  let outputBytes = 0;
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    child.kill();
  }, 120_000);
  child.stdout.on("data", (chunk) => {
    outputBytes += chunk.length;
    if (outputBytes <= 128 * 1024) stdout.push(chunk);
    else child.kill();
  });
  child.stderr.on("data", (chunk) => {
    if (Buffer.concat(stderr).length < 32 * 1024) stderr.push(chunk);
  });
  const exitCode = await new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("close", (code) => resolve(code));
  }).finally(() => clearTimeout(timer));
  if (timedOut) throw new Error(`opencode_${arm}_timed_out`);
  if (outputBytes > 128 * 1024) throw new Error(`opencode_${arm}_output_limit_exceeded`);
  const outText = Buffer.concat(stdout).toString("utf8");
  const errText = Buffer.concat(stderr).toString("utf8");
  if (exitCode !== 0) {
    const suffix = errText.replaceAll(/[\r\n]+/g, " ").slice(-1500);
    throw new Error(`opencode_${arm}_exit_${exitCode}:${suffix || "no_stderr"}`);
  }
  if (!outText.includes(MOCK_RESPONSE_TEXT)) {
    throw new Error(`opencode_${arm}_mock_response_missing`);
  }
  const errorLines = errText.split(/\r?\n/)
    .filter((line) => /plugin|hook|error|warn|failed|module/i.test(line))
    .map((line) => line.replaceAll(/[\r\n]+/g, " ").slice(0, 500))
    .slice(-12);
  return {
    elapsed_ms: Date.now() - startedAt,
    exit_code: exitCode,
    isolated_home: true,
    stderr_bytes: Buffer.byteLength(errText),
    stderr_sha256: sha256(errText),
    error_lines: errorLines,
  };
}

function summarizeRequests(rows) {
  return rows.map(({ raw, body, url }) => ({
    request_path: url,
    exact_http_body_sha256: sha256(raw),
    http_body_bytes: raw.byteLength,
    message_count: body.messages.length,
    tool_count: Array.isArray(body.tools) ? body.tools.length : 0,
    tool_names: Array.isArray(body.tools)
      ? body.tools.map((tool) => tool?.function?.name).filter((name) => typeof name === "string").sort()
      : [],
    messages: body.messages,
    tools: Array.isArray(body.tools) ? body.tools : [],
  }));
}

function countWithPinnedTokenizer(arms) {
  const source = String.raw`
import json, sys
from collections.abc import Mapping
from tools.measure_synthetic_context_token_reduction import _load_tokenizer
tokenizer, versions = _load_tokenizer()
payload = json.load(sys.stdin)
result = {"runtime_package_versions": versions, "arms": {}}
for arm, requests in payload.items():
    counts = []
    for request in requests:
        tools = request.get("tools", [])
        encoded = tokenizer.apply_chat_template(
            request["messages"], tools=tools, tokenize=True,
            add_generation_prompt=True,
        )
        if isinstance(encoded, Mapping):
            if "input_ids" not in encoded:
                raise ValueError("tokenizer_output_missing_input_ids")
            encoded = encoded["input_ids"]
        if hasattr(encoded, "tolist"):
            encoded = encoded.tolist()
        if isinstance(encoded, tuple):
            encoded = list(encoded)
        if type(encoded) is not list:
            raise ValueError("tokenizer_input_ids_not_a_list")
        if encoded and type(encoded[0]) is list:
            if len(encoded) != 1:
                raise ValueError("tokenizer_returned_multiple_conversations")
            encoded = encoded[0]
        if any(type(token) is not int for token in encoded):
            raise ValueError("tokenizer_input_ids_not_integer_sequence")
        if not encoded:
            raise ValueError("tokenizer_input_ids_empty")
        counts.append(len(encoded))
    result["arms"][arm] = {"request_count": len(counts), "input_token_counts": counts, "input_tokens": sum(counts)}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
`;
  const child = spawn(OPENCODE_TOKENIZER_PYTHON, ["-c", source], {
    cwd: ROOT,
    windowsHide: true,
    env: isolatedEnvironment(
      path.join(JOB_ROOT, "tokenizer-home"),
      path.join(JOB_ROOT, "tokenizer-home", "config"),
      path.join(JOB_ROOT, "tokenizer-home", "tmp"),
    ),
    stdio: ["pipe", "pipe", "pipe"],
  });
  const output = [];
  const errors = [];
  child.stdout.on("data", (chunk) => output.push(chunk));
  child.stderr.on("data", (chunk) => errors.push(chunk));
  child.stdin.end(JSON.stringify(arms));
  return new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("close", (code) => {
      if (code !== 0) return reject(new Error(`tokenizer_count_failed:${Buffer.concat(errors).toString("utf8").slice(-1000)}`));
      try { resolve(JSON.parse(Buffer.concat(output).toString("utf8"))); }
      catch { reject(new Error("tokenizer_count_json_invalid")); }
    });
  });
}

const OPENCODE_TOKENIZER_PYTHON = PYTHON;
let failureDiagnostics = null;

async function main() {
  await mkdir(APPROVED_ROOT, { recursive: true });
  await mkdir(path.dirname(JOB_ROOT), { recursive: true });
  await mkdir(JOB_ROOT, { recursive: false });
  const receiver = startMockReceiver();
  let receipt;
  try {
    const port = await receiver.listen();
    const baseUrl = `http://127.0.0.1:${port}/v1`;
    const baselineInventoryPath = path.join(JOB_ROOT, "baseline-inventory.jsonl");
    const baselineReceiptPath = path.join(JOB_ROOT, "baseline-profile-receipt.jsonl");
    const baselineEventShapePath = path.join(JOB_ROOT, "baseline-event-shape.jsonl");
    const filteredReceiptPath = path.join(JOB_ROOT, "filtered-profile-receipt.jsonl");
    const fixtureSourceSha256 = sha256(TASK_SOURCE);

    receiver.setArm("baseline");
    const baselinePlugin = makeProbePluginSource(baselineReceiptPath, baselineInventoryPath, baselineEventShapePath);
    const baselineRun = await runOpenCode({
      root: JOB_ROOT,
      arm: "baseline",
      baseUrl,
      pluginSource: baselinePlugin,
      inventoryPath: baselineInventoryPath,
      profileReceiptPath: baselineReceiptPath,
    });
    const baselineRequests = receiver.captured.filter((row) => row.arm === "baseline");
    const inventoryText = await readFile(baselineInventoryPath, "utf8").catch(() => null);
    const profileReceiptText = await readFile(baselineReceiptPath, "utf8").catch(() => null);
    const eventShapeText = await readFile(baselineEventShapePath, "utf8").catch(() => null);
    if (inventoryText === null) {
      failureDiagnostics = {
        baseline_run: baselineRun,
        mock_requests_seen: baselineRequests.length,
        inventory_file_written: false,
        profile_receipt_file_written: profileReceiptText !== null,
        profile_receipt_lines: profileReceiptText?.trim().split(/\r?\n/).slice(0, 4) ?? [],
        event_shape_file_written: eventShapeText !== null,
        event_shape_lines: eventShapeText?.trim().split(/\r?\n/).slice(0, 2) ?? [],
      };
      throw new Error(`baseline_inventory_missing:${JSON.stringify(failureDiagnostics).slice(0, 2500)}`);
    }
    const inventoryLines = inventoryText.trim().split(/\r?\n/);
    if (inventoryLines.length !== baselineRequests.length) {
      throw new Error(`baseline_inventory_capture_count_invalid:${JSON.stringify(baselineRun.error_lines)}`);
    }
    const inventoryRows = inventoryLines.map(JSON.parse);
    const inventory = inventoryRows[0];
    if (inventoryRows.some((row) => row.inventory_sha256 !== inventory.inventory_sha256 || JSON.stringify(row.tool_names) !== JSON.stringify(inventory.tool_names))) {
      throw new Error("baseline_tool_inventory_changed_during_session");
    }
    const baselineProfileReceipts = (await readFile(baselineReceiptPath, "utf8")).trim().split(/\r?\n/).map(JSON.parse);
    if (
      baselineProfileReceipts.length !== baselineRequests.length ||
      baselineProfileReceipts.some((receipt) => receipt.outcome !== "pass_through" || receipt.inventory_sha256 !== inventory.inventory_sha256)
    ) {
      throw new Error("baseline_context_hook_receipt_invalid");
    }
    const inventoryNames = inventory.tool_names;
    const allowedToolNames = inventoryNames.filter((name) => PROFILE_KEEP.has(name));
    if (allowedToolNames.length === 0 || allowedToolNames.length >= inventoryNames.length) {
      throw new Error("read_only_profile_not_a_strict_tool_subset");
    }

    const profile = {
      id: "synthetic-read-only-single-tool-v1",
      inventorySha256: inventory.inventory_sha256,
      allowedToolNames,
    };
    const filteredPlugin = makeFilteredPluginSource(profile, filteredReceiptPath);
    receiver.setArm("filtered");
    const filteredRun = await runOpenCode({
      root: JOB_ROOT,
      arm: "filtered",
      baseUrl,
      pluginSource: filteredPlugin,
      inventoryPath: null,
      profileReceiptPath: filteredReceiptPath,
    });
    const filteredProfileReceipts = (await readFile(filteredReceiptPath, "utf8")).trim().split(/\r?\n/).map(JSON.parse);
    if (
      filteredProfileReceipts.length !== 2 ||
      filteredProfileReceipts.some((receipt) =>
        receipt.outcome !== "filtered" ||
        receipt.reason !== "profile_applied" ||
        receipt.profile_id !== profile.id ||
        receipt.inventory_sha256 !== inventory.inventory_sha256)
    ) {
      throw new Error("filtered_context_hook_receipt_invalid");
    }
    const filteredRequests = receiver.captured.filter((row) => row.arm === "filtered");
    if (baselineRequests.length !== 2 || filteredRequests.length !== 2) {
      throw new Error("expected_tool_call_and_followup_request_per_arm");
    }
    const baselinePayloads = baselineRequests.map((row) => row.body);
    const filteredPayloads = filteredRequests.map((row) => row.body);
    const toolNamesFor = (payload) => Array.isArray(payload.tools)
      ? payload.tools.map((tool) => tool?.function?.name).filter((name) => typeof name === "string").sort()
      : [];
    const baselineToolNames = toolNamesFor(baselinePayloads[0]);
    const filteredToolNames = toolNamesFor(filteredPayloads[0]);
    if (baselinePayloads.some((payload) => JSON.stringify(toolNamesFor(payload)) !== JSON.stringify(inventoryNames))) {
      throw new Error("baseline_openai_tool_names_do_not_match_context_inventory");
    }
    if (filteredPayloads.some((payload) => JSON.stringify(toolNamesFor(payload)) !== JSON.stringify(allowedToolNames))) {
      throw new Error("filtered_lowered_tool_names_mismatch");
    }
    const taskVerification = receiver.verification;
    for (const arm of ["baseline", "filtered"]) {
      const phases = taskVerification[arm].map((row) => row.phase);
      if (phases.join(",") !== "tool_call,tool_result" || taskVerification[arm][1].verified !== true) {
        throw new Error(`${arm}_read_tool_round_trip_unverified:${JSON.stringify(taskVerification[arm])}`);
      }
    }
    const nonSystemMessages = (messages) => messages.filter((message) => message?.role !== "system");
    const pairedNonSystemMessagesEqual = baselinePayloads.every((payload, index) =>
      JSON.stringify(nonSystemMessages(payload.messages)) === JSON.stringify(nonSystemMessages(filteredPayloads[index].messages)));
    if (!pairedNonSystemMessagesEqual) {
      failureDiagnostics = {
        baseline_message_payload_sha256: baselinePayloads.map((payload) => sha256(JSON.stringify(payload.messages))),
        filtered_message_payload_sha256: filteredPayloads.map((payload) => sha256(JSON.stringify(payload.messages))),
      };
      throw new Error("paired_non_system_request_messages_changed_between_arms");
    }

    const counts = await countWithPinnedTokenizer({
      baseline: summarizeRequests(baselineRequests),
      filtered: summarizeRequests(filteredRequests),
    });
    const baselineTokens = counts.arms.baseline.input_tokens;
    const filteredTokens = counts.arms.filtered.input_tokens;
    receipt = {
      schema: "wrench.opencode-no-provider-request-preflight.v1",
      status: "complete",
      opencode_version: "2.0.12",
      opencode_binary_sha256: sha256(await readFile(OPENCODE_BIN)),
      tool_profile_source_sha256: sha256(await readFile(TOOL_PROFILES)),
      provider_route: "loopback mock receiver only; SubRoute :4000 was not called",
      provider_calls: 0,
      local_mock_http_requests: receiver.captured.length,
      mock_request_capture: "in-memory only; receipt stores exact body hashes/counts, not messages or schemas",
      egress_scope: "isolated OpenCode config and home, local mock model URL, scrubbed child environment, offline package resolution; no OS-wide firewall change",
      task: "synthetic read-only source lookup; loopback mock scripted one read call and final answer after verifying exact fixture source in the tool result",
      task_fixture_source_sha256: fixtureSourceSha256,
      task_execution: {
        synthetic_task_oracle: "both arms completed one OpenCode read-tool cycle and the mock verified the exact fixture contents before returning the scripted answer",
        baseline: taskVerification.baseline,
        filtered: taskVerification.filtered,
        model_reasoning_or_success: "not measured; no model generated either response",
      },
      profile_id: profile.id,
      inventory_sha256: inventory.inventory_sha256,
      baseline_tool_names: baselineToolNames,
      filtered_tool_names: filteredToolNames,
      paired_non_system_message_payload_equal: true,
      paired_system_message_payload_equal_per_request: baselinePayloads.map((payload, index) =>
        JSON.stringify(payload.messages.filter((message) => message?.role === "system")) ===
        JSON.stringify(filteredPayloads[index].messages.filter((message) => message?.role === "system"))),
      baseline_message_payload_sha256: baselinePayloads.map((payload) => sha256(JSON.stringify(payload.messages))),
      filtered_message_payload_sha256: filteredPayloads.map((payload) => sha256(JSON.stringify(payload.messages))),
      input_token_counting: "MiniMax M3 pinned chat template over exact lowered messages and function tools; local tokenizer count, not provider usage",
      tokenizer_revision: "MiniMaxAI/MiniMax-M3@f0e1c1e04d40177e4673a22097036854f536e9c0",
      tokenizer_inventory_sha256: "86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c",
      runtime_package_versions: counts.runtime_package_versions,
      baseline: {
        open_code_elapsed_ms: baselineRun.elapsed_ms,
        request_count: baselineRequests.length,
        lowered_request_sha256: baselineRequests.map((row) => sha256(row.raw)),
        lowered_request_bytes: baselineRequests.reduce((total, row) => total + row.raw.byteLength, 0),
        tool_count: baselineToolNames.length,
        target_token_input_count: baselineTokens,
        per_request_input_tokens: counts.arms.baseline.input_token_counts,
      },
      filtered: {
        open_code_elapsed_ms: filteredRun.elapsed_ms,
        request_count: filteredRequests.length,
        lowered_request_sha256: filteredRequests.map((row) => sha256(row.raw)),
        lowered_request_bytes: filteredRequests.reduce((total, row) => total + row.raw.byteLength, 0),
        tool_count: filteredToolNames.length,
        target_token_input_count: filteredTokens,
        per_request_input_tokens: counts.arms.filtered.input_token_counts,
      },
      target_token_input_reduction_percent: baselineTokens > 0
        ? Number((100 * (1 - filteredTokens / baselineTokens)).toFixed(4))
        : null,
      task_completion: null,
      billed_cost: null,
      claims_not_established: [
        "frontier provider usage or billed-token savings",
        "verified coding-task utility or success retention",
        "LoRA selection quality, 95/5 routing, or all-day engineering",
      ],
    };
    await writeFile(RECEIPT_PATH, `${JSON.stringify(receipt, null, 2)}\n`, { flag: "wx", encoding: "utf8" });
    process.stdout.write(`${JSON.stringify(receipt)}\n`);
  } finally {
    await receiver.close();
    await rm(JOB_ROOT, { recursive: true, force: true });
  }
}

main().catch(async (error) => {
  const failure = {
    schema: "wrench.opencode-no-provider-request-preflight.v1",
    status: "failed_closed",
    error: String(error?.message ?? "runtime_preflight_failed").slice(0, 1000),
    provider_calls: 0,
    diagnostics: failureDiagnostics,
  };
  try {
    await writeFile(RECEIPT_PATH, `${JSON.stringify(failure, null, 2)}\n`, { flag: "wx", encoding: "utf8" });
  } catch {}
  process.stderr.write(`${JSON.stringify(failure)}\n`);
  process.exitCode = 1;
});
