import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, test } from "node:test";
import {
  MAX_SESSION_STATE_BYTES,
  WRENCH_STORAGE_ROOT,
  WrenchRootSessionStateStore,
} from "./wrench_root_session_store.mjs";

const testDirectory = fs.mkdtempSync(path.join(WRENCH_STORAGE_ROOT, "artifacts", "tool-profile-store-iter134-"));
const namespace = path.relative(WRENCH_STORAGE_ROOT, testDirectory).replaceAll("\\", "/");
const moduleUrl = new URL("./wrench_root_session_store.mjs", import.meta.url).href;

after(() => {
  fs.rmSync(testDirectory, { recursive: true, force: true });
});

function key(number) {
  return `session-profile/${BigInt(number).toString(16).padStart(64, "0")}`;
}

function makeStore(options = {}) {
  return new WrenchRootSessionStateStore({
    namespace,
    maxStoreBytes: 2 * 1024 * 1024,
    minimumFreeBytes: 0,
    ...options,
  });
}

test("claims are unique, capacity-bounded, and state survives restart", async () => {
  const testNamespace = `${namespace}/crud`;
  const store = makeStore({ namespace: testNamespace, maxSessionClaims: 2 });
  const first = key(1);
  const second = key(2);
  assert.equal(await store.claim(first, 2), "created");
  assert.equal(await store.claim(first, 2), "existing");
  assert.equal(await store.get(first), undefined);
  await store.set(first, { schema: "test.v1", profile_id: "read" });
  assert.equal(await store.claim(second, 2), "created");
  assert.equal(await store.claim(key(3), 2), "capacity");
  store.close();

  const reopened = makeStore({ namespace: testNamespace, maxSessionClaims: 2 });
  assert.deepEqual(await reopened.get(first), { schema: "test.v1", profile_id: "read" });
  assert.equal(await reopened.claim(first, 2), "existing");
  assert.equal(await reopened.claim(key(3), 2), "capacity");
  reopened.close();
});

test("concurrent Node processes share one atomic claim limit", async () => {
  const testNamespace = `${namespace}/concurrent`;
  const parent = makeStore({ namespace: testNamespace, maxSessionClaims: 32 });
  parent.close();

  const source = `
    import { WrenchRootSessionStateStore } from ${JSON.stringify(moduleUrl)};
    const namespace = process.argv[1];
    const worker = Number(process.argv[2]);
    const store = new WrenchRootSessionStateStore({ namespace, maxSessionClaims: 32, maxStoreBytes: 2 * 1024 * 1024, minimumFreeBytes: 0 });
    let created = 0, capacity = 0;
    for (let i = 0; i < 16; i += 1) {
      const n = worker * 16 + i + 100;
      const result = await store.claim('session-profile/' + BigInt(n).toString(16).padStart(64, '0'), 32);
      if (result === 'created') created += 1;
      else if (result === 'capacity') capacity += 1;
      else throw new Error('unexpected_existing_claim');
    }
    store.close();
    console.log(JSON.stringify({ created, capacity }));
  `;

  const results = await Promise.all(Array.from({ length: 4 }, (_, worker) => new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["--input-type=module", "-e", source, testNamespace, String(worker)], {
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8").on("data", (chunk) => { stdout += chunk; });
    child.stderr.setEncoding("utf8").on("data", (chunk) => { stderr += chunk; });
    child.once("error", reject);
    child.once("close", (code) => {
      if (code !== 0) reject(new Error(`claim_worker_failed:${code}:${stderr.slice(-500)}`));
      else {
        try { resolve(JSON.parse(stdout.trim().split(/\r?\n/).at(-1))); }
        catch { reject(new Error(`claim_worker_output_invalid:${stdout.slice(-500)}:${stderr.slice(-500)}`)); }
      }
    });
  })));

  assert.equal(results.reduce((sum, item) => sum + item.created, 0), 32);
  assert.equal(results.reduce((sum, item) => sum + item.capacity, 0), 32);
  const reopened = makeStore({ namespace: testNamespace, maxSessionClaims: 32 });
  assert.equal(await reopened.claim(key(101), 32), "existing");
  reopened.close();
});

test("state validation and explicit storage authorization fail closed", async () => {
  assert.throws(
    () => new WrenchRootSessionStateStore({ storageRoot: os.tmpdir(), namespace: "bad" }),
    { code: "session_store_root_must_be_wrench_storage_root" },
  );
  assert.throws(() => makeStore({ namespace: "../escape" }), { code: "session_store_namespace_invalid" });
  assert.throws(() => makeStore({ freeSpaceProbe: () => 1 }), { code: "session_store_free_space_floor_breached" });
  const corruptDirectory = path.join(testDirectory, "corrupt");
  fs.mkdirSync(corruptDirectory);
  fs.writeFileSync(path.join(corruptDirectory, "session-state.sqlite"), "not a sqlite database");
  assert.throws(
    () => makeStore({ namespace: `${namespace}/corrupt` }),
    { code: "session_store_database_open_or_schema_invalid" },
  );

  const store = makeStore({ namespace: `${namespace}/validation`, maxSessionClaims: 1 });
  await assert.rejects(store.set(key(9), { profile_id: "unclaimed" }), { code: "session_store_key_not_claimed" });
  await assert.rejects(store.claim("session-profile/not-a-digest", 1), { code: "session_store_key_invalid" });
  await assert.rejects(store.set(key(10), { data: "x".repeat(MAX_SESSION_STATE_BYTES) }), { code: "session_store_state_byte_limit_exceeded" });
  store.close();
});
