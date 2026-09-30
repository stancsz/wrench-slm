import { createHash } from "node:crypto";
import { copyFile, lstat, mkdir, readFile, readdir, realpath, rm, stat, writeFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createServer } from "node:http";

const EXAMPLE = dirname(fileURLToPath(import.meta.url));
const ARTIFACT_ROOT = "C:\\wrench-slm-data\\artifacts";
const MAX_CHILD_OUTPUT = 1024 * 1024;
const MAX_SERVER_BODY = 128 * 1024;
const MAX_FINAL_OUTPUT_BYTES = 1024 * 1024;
const MAX_SCRATCH_BYTES = 45_000_000;
const MAX_FAKE_REQUESTS = 16;
const CHILD_TIMEOUT_MS = 45_000;

function argument(name) {
  const index = process.argv.indexOf(name);
  if (index < 0 || !process.argv[index + 1]) throw new Error(`argument_required:${name}`);
  return process.argv[index + 1];
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

async function readBounded(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_SERVER_BODY) throw new Error("fake_endpoint_request_too_large");
    chunks.push(chunk);
  }
  return Buffer.concat(chunks, size);
}

function readBoundedChild(child, label) {
  let text = "";
  child.on(label, (chunk) => {
    text += chunk.toString("utf8");
    if (Buffer.byteLength(text, "utf8") > MAX_CHILD_OUTPUT) child.kill();
  });
  return () => text;
}

async function treeBytes(root, limit = MAX_FINAL_OUTPUT_BYTES) {
  const info = await lstat(root);
  if (info.isSymbolicLink()) throw new Error("probe_output_link_refused");
  if (info.isFile()) return info.size;
  if (!info.isDirectory()) throw new Error("probe_output_entry_type_refused");
  let total = 0;
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const child = join(root, entry.name);
    const childInfo = await lstat(child);
    if (childInfo.isSymbolicLink()) throw new Error("probe_output_link_refused");
    total += childInfo.isFile() ? childInfo.size : await treeBytes(child, limit);
    if (total > limit) throw new Error("probe_output_budget_exceeded");
  }
  return total;
}

async function safeDeleteOwnedProfile(profile, armDir) {
  const expected = resolve(armDir, "profile");
  if (resolve(profile).toLowerCase() !== expected.toLowerCase()) throw new Error("probe_cleanup_path_mismatch");
  const profileReal = await realpath(profile);
  if (profileReal.toLowerCase() !== expected.toLowerCase()) throw new Error("probe_cleanup_reparse_refused");
  await rm(profile, { recursive: true, force: false });
}

async function runOpenCode({ binary, cwd, profile, mode, endpoint, pluginPath, receiptPath }) {
  const config = {
    "$schema": "https://opencode.ai/config.json",
    provider: {
      "wrench-loopback": {
        npm: "@ai-sdk/openai-compatible",
        name: "Wrench in-process loopback fixture",
        options: { baseURL: `${endpoint}/v1`, apiKey: "local-fake-only" },
        models: { fake: { name: "Local fixture model", limit: { context: 32768, output: 64 } } },
      },
    },
    model: "wrench-loopback/fake",
  };
  await writeFile(join(profile, "opencode.json"), `${JSON.stringify(config, null, 2)}\n`, { flag: "wx" });
  const localPluginDir = join(cwd, ".opencode", "plugins", "wrench-probe");
  await mkdir(localPluginDir, { recursive: true });
  await copyFile(pluginPath, join(localPluginDir, "index.ts"));
  const env = {
    SystemRoot: process.env.SystemRoot || "C:\\Windows",
    WINDIR: process.env.WINDIR || "C:\\Windows",
    PATH: `${process.env.SystemRoot || "C:\\Windows"}\\System32`,
    TEMP: profile,
    TMP: profile,
    USERPROFILE: profile,
    HOME: profile,
    APPDATA: join(profile, "AppData", "Roaming"),
    LOCALAPPDATA: join(profile, "AppData", "Local"),
    WRENCH_HOOK_PROBE_MODE: mode,
    WRENCH_HOOK_PROBE_RECEIPT: receiptPath,
  };
  await mkdir(env.APPDATA, { recursive: true });
  await mkdir(env.LOCALAPPDATA, { recursive: true });
  const child = spawn(binary, ["run", "--standalone", "--print-logs", "--model", "wrench-loopback/fake", "Reply with OK"], {
    cwd,
    env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  const stdout = readBoundedChild(child, "stdout");
  const stderr = readBoundedChild(child, "stderr");
  const timeout = setTimeout(() => child.kill(), CHILD_TIMEOUT_MS);
  const result = await new Promise((resolveResult, reject) => {
    child.once("error", reject);
    child.once("close", (code, signal) => resolveResult({ code, signal }));
  }).finally(() => clearTimeout(timeout));
  const output = { ...result, stdout: stdout(), stderr: stderr() };
  await writeFile(join(profile, "stdout.txt"), output.stdout, { flag: "wx" });
  await writeFile(join(profile, "stderr.txt"), output.stderr, { flag: "wx" });
  return output;
}

async function main() {
  const binary = resolve(argument("--opencode"));
  const outputDir = resolve(argument("--output-dir"));
  if (!isAbsolute(outputDir)) throw new Error("output_dir_must_be_absolute");
  try {
    await stat(outputDir);
    throw new Error("output_dir_must_be_new");
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  const realArtifactRoot = await realpath(ARTIFACT_ROOT);
  if (dirname(outputDir).toLowerCase() !== realArtifactRoot.toLowerCase()) throw new Error("output_dir_must_be_direct_child_of_canonical_artifact_root");
  await mkdir(outputDir, { recursive: false });
  if ((await realpath(outputDir)).toLowerCase() !== outputDir.toLowerCase()) throw new Error("output_dir_reparse_refused");
  const pluginPath = resolve(EXAMPLE, "plugin.mjs");
  const source = await readFile(fileURLToPath(import.meta.url));
  const plugin = await readFile(pluginPath);
  const endpointCalls = [];
  const server = createServer(async (request, response) => {
    try {
      const body = await readBounded(request);
      if (request.method === "POST" && request.url === "/v1/chat/completions") {
        if (endpointCalls.length >= MAX_FAKE_REQUESTS) throw new Error("fake_endpoint_request_limit");
        const requestBody = JSON.parse(body.toString("utf8"));
        endpointCalls.push({
          request_id: request.headers["x-wrench-probe-id"] ?? null,
          request_bytes: body.length,
          body_sha256: sha256(body),
          stream: requestBody.stream === true,
        });
        if (requestBody.stream === true) {
          const chunks = [
            { id: "wrench-local-fake-completion", object: "chat.completion.chunk", created: 1, model: "fake", choices: [{ index: 0, delta: { role: "assistant", content: "OK" }, finish_reason: null }] },
            { id: "wrench-local-fake-completion", object: "chat.completion.chunk", created: 1, model: "fake", choices: [{ index: 0, delta: {}, finish_reason: "stop" }] },
            { id: "wrench-local-fake-completion", object: "chat.completion.chunk", created: 1, model: "fake", choices: [], usage: { prompt_tokens: 17, completion_tokens: 2, total_tokens: 19 } },
          ];
          const payload = `${chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`).join("")}data: [DONE]\n\n`;
          response.writeHead(200, {
            "content-type": "text/event-stream",
            "content-length": Buffer.byteLength(payload),
            "x-wrench-probe-id": request.headers["x-wrench-probe-id"] ?? "missing",
          });
          response.end(payload);
          return;
        }
        const payload = JSON.stringify({
          id: "wrench-local-fake-completion",
          object: "chat.completion",
          created: 1,
          model: "fake",
          choices: [{ index: 0, message: { role: "assistant", content: "OK" }, finish_reason: "stop" }],
          usage: { prompt_tokens: 17, completion_tokens: 2, total_tokens: 19 },
        });
        response.writeHead(200, {
          "content-type": "application/json",
          "content-length": Buffer.byteLength(payload),
          "x-wrench-probe-id": request.headers["x-wrench-probe-id"] ?? "missing",
        });
        response.end(payload);
        return;
      }
      if (request.method === "GET" && request.url === "/v1/models") {
        const payload = JSON.stringify({ data: [{ id: "fake", object: "model" }] });
        response.writeHead(200, { "content-type": "application/json", "content-length": Buffer.byteLength(payload) });
        response.end(payload);
        return;
      }
      response.writeHead(404, { "content-type": "application/json" });
      response.end(JSON.stringify({ error: { message: "local_probe_route_not_found" } }));
    } catch {
      response.writeHead(413);
      response.end();
    }
  });
  await new Promise((resolveListen, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolveListen);
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("loopback_bind_failed");
  const endpoint = `http://127.0.0.1:${address.port}`;
  const outcomes = [];
  try {
    for (const mode of ["block", "observe"]) {
      const armDir = join(outputDir, mode);
      const profile = join(armDir, "profile");
      await mkdir(armDir, { recursive: false });
      if ((await realpath(armDir)).toLowerCase() !== armDir.toLowerCase()) throw new Error("probe_arm_dir_reparse_refused");
      await mkdir(profile, { recursive: false });
      const receiptPath = join(armDir, "hook-receipts.jsonl");
      const callStart = endpointCalls.length;
      const result = await runOpenCode({
        binary,
        cwd: profile,
        profile,
        mode,
        endpoint,
        pluginPath,
        receiptPath,
      });
      const calls = endpointCalls.slice(callStart);
      const receipt = await readFile(join(armDir, "hook-receipts.jsonl")).catch(() => Buffer.alloc(0));
      const runtimeLogPath = join(profile, ".local", "share", "opencode", "log", "opencode.log");
      let logTail = "";
      try {
        const log = await readFile(runtimeLogPath, "utf8");
        logTail = log.slice(-2048);
      } catch (error) {
        if (error.code !== "ENOENT") throw error;
      }
      const scratchBytes = await treeBytes(armDir, MAX_SCRATCH_BYTES);
      outcomes.push({ mode, process: result, endpoint_completion_requests: calls.length, calls, receipt_bytes: receipt.length, scratch_peak_bytes: scratchBytes, runtime_log_tail: logTail });
      await safeDeleteOwnedProfile(profile, armDir);
    }
  } finally {
    await new Promise((resolveClose) => server.close(resolveClose));
  }
  const block = outcomes.find((item) => item.mode === "block");
  const observe = outcomes.find((item) => item.mode === "observe");
  const observeReceiptPath = join(outputDir, "observe", "hook-receipts.jsonl");
  let receiptRows = [];
  try {
    receiptRows = (await readFile(observeReceiptPath, "utf8")).trim().split(/\r?\n/u).filter(Boolean).map((line) => JSON.parse(line));
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  const callIDs = observe.calls.map((call) => call.request_id);
  const receiptIDs = receiptRows.map((row) => row.request_id);
  const assertions = {
    block_hook_prevented_transport: block.endpoint_completion_requests === 0,
    observe_reached_fake_endpoint: observe.endpoint_completion_requests >= 1,
    response_hook_recorded_correlated_usage: receiptRows.length === observe.endpoint_completion_requests &&
      new Set(callIDs).size === callIDs.length && new Set(receiptIDs).size === receiptIDs.length &&
      [...callIDs].sort().join("|") === [...receiptIDs].sort().join("|") && receiptRows.every((row) =>
        row.response_status === 200 && row.request_id &&
        row.usage?.prompt_tokens === 17 && row.usage?.completion_tokens === 2 && row.usage?.total_tokens === 19),
    no_external_route_configured: endpoint.startsWith("http://127.0.0.1:"),
  };
  const finalOutputBytes = await treeBytes(outputDir);
  if (finalOutputBytes > MAX_FINAL_OUTPUT_BYTES) throw new Error("probe_final_output_budget_exceeded");
  const result = {
    schema: "wrench.opencode-loopback-runtime-probe-result.v1",
    opencode_binary: binary,
    endpoint,
    plugin_sha256: sha256(plugin),
    runner_sha256: sha256(source),
    assertions,
    passed: Object.values(assertions).every(Boolean),
    outcomes,
    final_output_bytes: finalOutputBytes,
    final_output_limit_bytes: MAX_FINAL_OUTPUT_BYTES,
    synthetic_only: true,
    provider_calls: 0,
    provider: null,
    billed_cost: null,
    billing_verified: false,
  };
  const resultText = `${JSON.stringify(result, null, 2)}\n`;
  const currentOutputBytes = await treeBytes(outputDir);
  let resultBytes = Buffer.byteLength(resultText, "utf8");
  let projectedFinalOutputBytes = currentOutputBytes + resultBytes;
  for (let index = 0; index < 4; index += 1) {
    result.final_output_bytes = projectedFinalOutputBytes;
    result.result_record_bytes = resultBytes;
    resultBytes = Buffer.byteLength(`${JSON.stringify(result, null, 2)}\n`, "utf8");
    projectedFinalOutputBytes = currentOutputBytes + resultBytes;
  }
  if (projectedFinalOutputBytes > MAX_FINAL_OUTPUT_BYTES) throw new Error("probe_projected_final_output_budget_exceeded");
  result.final_output_bytes = projectedFinalOutputBytes;
  result.result_record_bytes = resultBytes;
  const finalResultText = `${JSON.stringify(result, null, 2)}\n`;
  if (Buffer.byteLength(finalResultText, "utf8") !== resultBytes) throw new Error("probe_result_size_projection_mismatch");
  await writeFile(join(outputDir, "result.json"), finalResultText, { flag: "wx" });
  const actualFinalOutputBytes = await treeBytes(outputDir);
  if (actualFinalOutputBytes !== projectedFinalOutputBytes) throw new Error("probe_final_output_accounting_mismatch");
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.passed) process.exitCode = 1;
}

main().catch((error) => {
  process.stderr.write(`${error?.stack ?? String(error)}\n`);
  process.exitCode = 1;
});
