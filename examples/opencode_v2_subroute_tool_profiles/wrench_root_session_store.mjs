import fs from "node:fs";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";

export const WRENCH_STORAGE_ROOT = "C:\\wrench-slm-data";
export const SESSION_PROFILE_STATE_SCHEMA = "wrench.opencode.session-profile-state.v1";
export const MAX_SESSION_CLAIMS = 256;
export const MAX_SESSION_STATE_BYTES = 128 * 1024;
export const MAX_SESSION_STORE_BYTES = 48 * 1024 * 1024;
export const MIN_FREE_SPACE_BYTES = 5_000_000_000;

const APPLICATION_ID = 0x57524e43;
const USER_VERSION = 1;
const PAGE_SIZE_BYTES = 4096;
const KEY_PATTERN = /^session-profile\/[a-f0-9]{64}$/;

function fail(code) {
  const error = new Error(code);
  error.code = code;
  throw error;
}

function validateNamespace(namespace) {
  if (typeof namespace !== "string" || namespace.length < 1 || namespace.length > 160) {
    fail("session_store_namespace_invalid");
  }
  const parts = namespace.replaceAll("\\", "/").split("/");
  if (parts.some((part) => !/^[A-Za-z0-9._-]{1,64}$/.test(part) || part === "." || part === "..")) {
    fail("session_store_namespace_invalid");
  }
  return parts;
}

function validateKey(key) {
  if (typeof key !== "string" || !KEY_PATTERN.test(key)) {
    fail("session_store_key_invalid");
  }
  return key;
}

function encodeState(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    fail("session_store_value_must_be_object");
  }
  let encoded;
  try {
    encoded = JSON.stringify(value);
  } catch {
    fail("session_store_value_not_json_serializable");
  }
  if (typeof encoded !== "string" || Buffer.byteLength(encoded, "utf8") > MAX_SESSION_STATE_BYTES) {
    fail("session_store_state_byte_limit_exceeded");
  }
  return encoded;
}

function ensureSafeDirectory(root, parts) {
  let current = root;
  const rootInfo = fs.lstatSync(current);
  if (!rootInfo.isDirectory() || rootInfo.isSymbolicLink()) fail("session_store_root_unsafe");
  for (const part of parts) {
    current = path.join(current, part);
    try {
      fs.mkdirSync(current);
    } catch (error) {
      if (error?.code !== "EEXIST") fail("session_store_directory_unavailable");
    }
    const info = fs.lstatSync(current);
    if (!info.isDirectory() || info.isSymbolicLink()) fail("session_store_directory_unsafe");
  }
  return current;
}

function inspectRegularDatabaseFile(databasePath, maxBytes) {
  let info;
  try {
    info = fs.lstatSync(databasePath);
  } catch (error) {
    if (error?.code === "ENOENT") return 0;
    fail("session_store_database_unavailable");
  }
  if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1) fail("session_store_database_unsafe");
  if (info.size > maxBytes) fail("session_store_database_byte_limit_exceeded");
  for (const suffix of ["-journal", "-wal", "-shm"]) {
    try {
      const sidecar = fs.lstatSync(`${databasePath}${suffix}`);
      if (!sidecar.isFile() || sidecar.isSymbolicLink() || sidecar.nlink !== 1 || sidecar.size > maxBytes) {
        fail("session_store_sidecar_unsafe_or_oversized");
      }
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
    }
  }
  return info.size;
}

/**
 * Durable OpenCode session state under the single approved Wrench data root.
 * SQLite BEGIN IMMEDIATE serializes claims across processes, so the persistent
 * claim count and unique session keys share one atomic capacity decision.
 * Callers must reserve the bounded database plus rollback-journal peak before
 * enabling writes. This class enforces its per-store byte and disk-headroom
 * ceilings, but does not create the external Wrench storage-budget reservation.
 */
export class WrenchRootSessionStateStore {
  constructor({
    storageRoot = WRENCH_STORAGE_ROOT,
    namespace = "opencode/tool-profile-state",
    maxSessionClaims = MAX_SESSION_CLAIMS,
    maxStoreBytes = MAX_SESSION_STORE_BYTES,
    minimumFreeBytes = MIN_FREE_SPACE_BYTES,
    freeSpaceProbe = null,
  } = {}) {
    const resolvedRoot = path.resolve(storageRoot);
    const expectedRoot = path.resolve(WRENCH_STORAGE_ROOT);
    if (resolvedRoot.toLowerCase() !== expectedRoot.toLowerCase()) {
      fail("session_store_root_must_be_wrench_storage_root");
    }
    if (!Number.isInteger(maxSessionClaims) || maxSessionClaims < 1 || maxSessionClaims > MAX_SESSION_CLAIMS) {
      fail("session_store_capacity_invalid");
    }
    if (!Number.isInteger(maxStoreBytes) || maxStoreBytes < PAGE_SIZE_BYTES || maxStoreBytes > MAX_SESSION_STORE_BYTES) {
      fail("session_store_byte_limit_invalid");
    }
    if (!Number.isSafeInteger(minimumFreeBytes) || minimumFreeBytes < 0) {
      fail("session_store_free_space_floor_invalid");
    }
    if (freeSpaceProbe !== null && typeof freeSpaceProbe !== "function") {
      fail("session_store_free_space_probe_invalid");
    }

    let canonicalRoot;
    try {
      canonicalRoot = fs.realpathSync.native(resolvedRoot);
    } catch {
      fail("session_store_root_unavailable");
    }
    if (canonicalRoot.toLowerCase() !== expectedRoot.toLowerCase()) {
      fail("session_store_root_reparse_or_alias_forbidden");
    }
    this.maxSessionClaims = maxSessionClaims;
    this.maxStoreBytes = maxStoreBytes;
    this.minimumFreeBytes = minimumFreeBytes;
    this.freeSpaceProbe = freeSpaceProbe;
    const directory = ensureSafeDirectory(canonicalRoot, validateNamespace(namespace));
    this.databasePath = path.join(directory, "session-state.sqlite");
    inspectRegularDatabaseFile(this.databasePath, this.maxStoreBytes);
    this.#assertDiskHeadroom();

    try {
      this.database = new DatabaseSync(this.databasePath, { timeout: 5000 });
      this.database.exec("PRAGMA journal_mode = DELETE");
      this.database.exec("PRAGMA synchronous = FULL");
      this.database.exec("PRAGMA foreign_keys = ON");
      this.database.exec("PRAGMA secure_delete = ON");
      this.database.exec("PRAGMA temp_store = MEMORY");
      this.database.exec(`PRAGMA max_page_count = ${Math.floor(this.maxStoreBytes / PAGE_SIZE_BYTES)}`);
      this.#initializeOrValidateSchema();
      this.#assertStoreBounds();
    } catch (error) {
      try { this.database?.close(); } catch { /* retain the original fail-closed error */ }
      if (typeof error?.code === "string" && error.code.startsWith("session_store_")) throw error;
      fail("session_store_database_open_or_schema_invalid");
    }
  }

  async get(key) {
    validateKey(key);
    this.#assertOpen();
    const row = this.database.prepare("SELECT json_value FROM session_values WHERE storage_key = ?").get(key);
    if (!row) return undefined;
    try {
      const value = JSON.parse(row.json_value);
      if (value === null || typeof value !== "object" || Array.isArray(value)) fail("session_store_state_corrupt");
      return value;
    } catch (error) {
      if (error?.code) throw error;
      fail("session_store_state_corrupt");
    }
  }

  async set(key, value) {
    validateKey(key);
    const json = encodeState(value);
    this.#assertOpen();
    this.#assertDiskHeadroom();
    this.database.exec("BEGIN IMMEDIATE");
    try {
      const claimed = this.database.prepare("SELECT 1 AS present FROM session_claims WHERE storage_key = ?").get(key);
      if (!claimed) fail("session_store_key_not_claimed");
      this.database.prepare(`
        INSERT INTO session_values(storage_key, json_value) VALUES(?, ?)
        ON CONFLICT(storage_key) DO UPDATE SET json_value = excluded.json_value
      `).run(key, json);
      this.database.exec("COMMIT");
    } catch (error) {
      if (this.database.isTransaction) this.database.exec("ROLLBACK");
      throw error;
    }
    this.#assertStoreBounds();
  }

  async claim(key, maxKeys) {
    validateKey(key);
    if (!Number.isInteger(maxKeys) || maxKeys < 1 || maxKeys > this.maxSessionClaims) {
      fail("session_store_claim_capacity_invalid");
    }
    this.#assertOpen();
    this.#assertDiskHeadroom();
    this.database.exec("BEGIN IMMEDIATE");
    try {
      const existing = this.database.prepare("SELECT 1 AS present FROM session_claims WHERE storage_key = ?").get(key);
      if (existing) {
        this.database.exec("COMMIT");
        return "existing";
      }
      const count = this.database.prepare("SELECT COUNT(*) AS count FROM session_claims").get().count;
      if (count >= maxKeys || count >= this.maxSessionClaims) {
        this.database.exec("COMMIT");
        return "capacity";
      }
      this.database.prepare("INSERT INTO session_claims(storage_key, created_at) VALUES(?, ?)").run(key, new Date().toISOString());
      this.database.exec("COMMIT");
    } catch (error) {
      if (this.database.isTransaction) this.database.exec("ROLLBACK");
      throw error;
    }
    this.#assertStoreBounds();
    return "created";
  }

  close() {
    if (this.database?.isOpen) this.database.close();
  }

  #initializeOrValidateSchema() {
    const appId = this.database.prepare("PRAGMA application_id").get().application_id;
    const userVersion = this.database.prepare("PRAGMA user_version").get().user_version;
    const objects = this.database.prepare("SELECT COUNT(*) AS count FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").get().count;
    if (appId === 0 && userVersion === 0 && objects === 0) {
      this.database.exec(`
        PRAGMA application_id = ${APPLICATION_ID};
        PRAGMA user_version = ${USER_VERSION};
        CREATE TABLE store_metadata (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE session_claims (
          storage_key TEXT PRIMARY KEY,
          created_at TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE session_values (
          storage_key TEXT PRIMARY KEY REFERENCES session_claims(storage_key),
          json_value TEXT NOT NULL
        ) WITHOUT ROWID;
        INSERT INTO store_metadata(key, value) VALUES('schema', '${SESSION_PROFILE_STATE_SCHEMA}');
      `);
    } else if (appId !== APPLICATION_ID || userVersion !== USER_VERSION) {
      fail("session_store_database_identity_invalid");
    }
    const schema = this.database.prepare("SELECT value FROM store_metadata WHERE key = 'schema'").get()?.value;
    if (schema !== SESSION_PROFILE_STATE_SCHEMA) fail("session_store_schema_invalid");
    const tables = new Set(this.database.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").all().map((row) => row.name));
    if (tables.size !== 3 || !["store_metadata", "session_claims", "session_values"].every((name) => tables.has(name))) {
      fail("session_store_table_inventory_invalid");
    }
    const integrity = this.database.prepare("PRAGMA integrity_check").all();
    if (integrity.length !== 1 || integrity[0].integrity_check !== "ok") fail("session_store_integrity_check_failed");
    const expectedColumns = {
      store_metadata: ["key", "value"],
      session_claims: ["storage_key", "created_at"],
      session_values: ["storage_key", "json_value"],
    };
    for (const [table, names] of Object.entries(expectedColumns)) {
      const columns = this.database.prepare(`PRAGMA table_info(${table})`).all();
      if (columns.map((column) => column.name).join("\0") !== names.join("\0") || columns.some((column) => column.pk !== 1 && column.name === names[0])) {
        fail("session_store_table_schema_invalid");
      }
    }
    const sessionValueReferences = this.database.prepare("PRAGMA foreign_key_list(session_values)").all();
    if (sessionValueReferences.length !== 1 || sessionValueReferences[0].table !== "session_claims" || sessionValueReferences[0].from !== "storage_key" || sessionValueReferences[0].to !== "storage_key") {
      fail("session_store_foreign_key_schema_invalid");
    }
    if (this.database.prepare("PRAGMA foreign_key_check").all().length !== 0) fail("session_store_foreign_key_check_failed");
  }

  #assertDiskHeadroom() {
    let available;
    try {
      if (this.freeSpaceProbe) available = this.freeSpaceProbe(this.databasePath);
      else {
        const stats = fs.statfsSync(path.dirname(this.databasePath));
        available = Number(BigInt(stats.bavail) * BigInt(stats.bsize));
      }
    } catch {
      fail("session_store_free_space_unavailable");
    }
    if (!Number.isSafeInteger(available) || available < this.minimumFreeBytes + this.maxStoreBytes) {
      fail("session_store_free_space_floor_breached");
    }
  }

  #assertStoreBounds() {
    const size = inspectRegularDatabaseFile(this.databasePath, this.maxStoreBytes);
    const pages = this.database.prepare("PRAGMA page_count").get().page_count;
    const pageSize = this.database.prepare("PRAGMA page_size").get().page_size;
    if (pageSize !== PAGE_SIZE_BYTES || pages * pageSize > this.maxStoreBytes || size > this.maxStoreBytes) {
      fail("session_store_database_byte_limit_exceeded");
    }
    const count = this.database.prepare("SELECT COUNT(*) AS count FROM session_claims").get().count;
    if (count > this.maxSessionClaims) fail("session_store_claim_capacity_corrupt");
    const claimKeys = this.database.prepare("SELECT storage_key FROM session_claims").all();
    if (claimKeys.some((row) => !KEY_PATTERN.test(row.storage_key))) fail("session_store_claim_key_corrupt");
  }

  #assertOpen() {
    if (!this.database?.isOpen) fail("session_store_closed");
  }
}
