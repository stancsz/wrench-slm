import { randomUUID } from "node:crypto";
import { lstat, open } from "node:fs/promises";

const mode = process.env.WRENCH_HOOK_PROBE_MODE;
const receiptPath = process.env.WRENCH_HOOK_PROBE_RECEIPT;
const MAX_RECEIPT_BYTES = 32 * 1024;
let receiptBytes = 0;

const Probe = {
  id: "wrench-loopback-http-hook-runtime-probe-v1",
  async setup(ctx) {
    if (!["block", "observe"].includes(mode)) throw new Error("probe_mode_invalid");
    if (!receiptPath) throw new Error("probe_receipt_path_missing");
    const registrations = [];
    try {
      registrations.push(await ctx.session.hook("http.request", async (event) => {
        if (mode === "block") throw new Error("wrench_loopback_probe_blocked");
        const id = randomUUID();
        event.request.headers.set("x-wrench-probe-id", id);
      }));
      registrations.push(await ctx.session.hook("http.response", async (event) => {
        const response = event.response;
        if (!(response instanceof Response)) throw new Error("probe_response_missing");
        const text = await response.clone().text();
        if (Buffer.byteLength(text, "utf8") > 64 * 1024) throw new Error("probe_response_too_large");
        let usage = null;
        try {
          const json = JSON.parse(text);
          usage = json.usage ?? null;
        } catch {
          for (const line of text.split(/\r?\n/u)) {
            if (!line.startsWith("data:")) continue;
            const value = line.slice(5).trim();
            if (!value || value === "[DONE]") continue;
            try {
              usage = JSON.parse(value).usage ?? usage;
            } catch {
              // Ignore non-JSON SSE lines in this bounded local probe.
            }
          }
        }
        const record = {
          schema: "wrench.opencode-loopback-http-hook-probe.v1",
          mode,
          session_id: event.sessionID,
          kind: event.kind ?? null,
          request_id: response.headers.get("x-wrench-probe-id"),
          response_status: response.status,
          usage,
          response_bytes: Buffer.byteLength(text, "utf8"),
          provider: null,
          billed_cost: null,
          billing_verified: false,
        };
        const line = `${JSON.stringify(record)}\n`;
        const bytes = Buffer.byteLength(line, "utf8");
        if (receiptBytes + bytes > MAX_RECEIPT_BYTES) throw new Error("probe_receipt_limit");
        try {
          const info = await lstat(receiptPath);
          if (info.isSymbolicLink()) throw new Error("probe_receipt_path_link");
        } catch (error) {
          if (error.code !== "ENOENT") throw error;
        }
        const file = await open(receiptPath, "a");
        try {
          await file.write(line, null, "utf8");
          receiptBytes += bytes;
        } finally {
          await file.close();
        }
      }));
    } catch (error) {
      await Promise.allSettled(registrations.map((registration) => registration.dispose?.()));
      throw error;
    }
    return async () => Promise.all(registrations.map((registration) => registration.dispose()));
  },
};

export default Probe;
