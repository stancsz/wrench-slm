"""Fail-closed approval and durable aggregate spend ledger for SubRoute calls.

This module is host-side accounting. The learned Wrench controller never gets
access to the ledger, SubRoute credentials, or provider authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path
from typing import Any


APPROVAL_SCHEMA = "wrench.subroute-spend-approval.v1"
LEDGER_SCHEMA_VERSION = 2
CAMPAIGN_ID = "wrench-gateway-model-research-20260927"
SUBROUTE_ENDPOINT = "http://127.0.0.1:4000/v1/chat/completions"
MODEL_ALIAS = "openrouter"
EXPECTED_UPSTREAM_MODEL = "minimax/minimax-m3"
EXPECTED_PROVIDER = "minimax"
MAX_INPUT_RATE_USD_PER_MILLION = Decimal("0.30")
MAX_OUTPUT_RATE_USD_PER_MILLION = Decimal("1.20")
PROVIDER_FRAMING_TOKEN_OVERHEAD = 4096
MAX_REQUEST_BODY_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 1_048_576
MAX_REQUESTS_PER_JOB = 10_000
MAX_REQUESTS_PER_CAMPAIGN = 10_000
MICRO_USD = Decimal("1000000")
_JOB_ID = re.compile(r"[A-Z0-9][A-Z0-9_-]{7,95}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CALLER_BUNDLE_FILES = (
    "tools/subroute_budget_guard.py",
    "tools/capture_subroute_teacher_traces.py",
    "tools/capture_minimax_teacher_traces.py",
    "tools/provider_budget_guard.py",
)


DATA_ROOT = Path(r"C:\wrench-slm-data").resolve()
APPROVAL_ROOT = DATA_ROOT / "artifacts" / "wrench-gateway-model-research" / "approvals"
CALL_ROOT = DATA_ROOT / "artifacts" / "wrench-gateway-model-research" / "subroute-calls"
DATASET_ROOT = DATA_ROOT / "datasets"
REPO_ROOT = Path(__file__).resolve().parents[1]


class BudgetError(ValueError):
    """A fail-closed approval, ledger, or settlement rejection."""


def _decimal(value: Any, name: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise BudgetError(f"{name}_invalid")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise BudgetError(f"{name}_invalid") from exc
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise BudgetError(f"{name}_invalid")
    return result


def usd_to_microusd(value: Any, name: str = "usd") -> int:
    amount = _decimal(value, name)
    rounded = amount.quantize(Decimal("0.000001"), rounding=ROUND_CEILING)
    return int(rounded * MICRO_USD)


def request_reserve_microusd(
    maximum_input_tokens: int,
    maximum_output_tokens: int,
    maximum_input_rate_usd_per_million_tokens: Any,
    maximum_output_rate_usd_per_million_tokens: Any,
) -> int:
    """Round the whole request ceiling up to the nearest micro-dollar."""
    for value, name in (
        (maximum_input_tokens, "maximum_input_tokens"),
        (maximum_output_tokens, "maximum_output_tokens"),
    ):
        if type(value) is not int or value <= 0:
            raise BudgetError(f"{name}_invalid")
    input_rate = _decimal(maximum_input_rate_usd_per_million_tokens, "input_rate", positive=True)
    output_rate = _decimal(maximum_output_rate_usd_per_million_tokens, "output_rate", positive=True)
    micro_usd = (
        Decimal(maximum_input_tokens) * input_rate
        + Decimal(maximum_output_tokens) * output_rate
    )
    return int(micro_usd.to_integral_value(rounding=ROUND_CEILING))


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BudgetError("duplicate_json_key")
        result[key] = value
    return result


def _read_json_no_duplicates(path: Path, name: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=_no_duplicate_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BudgetError(f"{name}_unavailable_or_invalid") from exc
    if not isinstance(value, dict):
        raise BudgetError(f"{name}_shape_invalid")
    return value, raw


def _safe_path(path: Path, root: Path, *, must_exist: bool) -> Path:
    absolute = Path(os.path.abspath(path))
    root_abs = Path(os.path.abspath(root))
    try:
        absolute.relative_to(root_abs)
    except ValueError as exc:
        raise BudgetError("path_outside_approved_root") from exc
    current = root_abs
    try:
        relative = absolute.relative_to(root_abs)
    except ValueError as exc:
        raise BudgetError("path_outside_approved_root") from exc
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise BudgetError("path_link_refused")
    if must_exist and not absolute.is_file():
        raise BudgetError("required_file_missing")
    if absolute.exists() and absolute.is_dir():
        raise BudgetError("file_path_is_directory")
    return absolute


def _parse_utc(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise BudgetError(f"{name}_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BudgetError(f"{name}_invalid") from exc
    if parsed.tzinfo is None:
        raise BudgetError(f"{name}_must_be_timezone_aware")
    return parsed.astimezone(timezone.utc)


def _git_head(repo_root: Path) -> str:
    import subprocess

    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BudgetError("repository_head_unavailable") from exc
    head = completed.stdout.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40,64}", head):
        raise BudgetError("repository_head_invalid")
    return head


def caller_bundle_sha256(repo_root: Path = REPO_ROOT) -> str:
    """Hash caller and policy dependencies into the spend approval."""
    root = Path(os.path.abspath(repo_root))
    digest = hashlib.sha256()
    for relative in CALLER_BUNDLE_FILES:
        path = _safe_path(root / relative, root, must_exist=True)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True)
class SubRouteApproval:
    approval_id: str
    job_id: str
    approval_sha256: str
    approved_head: str
    endpoint: str
    model_alias: str
    expected_upstream_model: str
    expected_provider: str
    aggregate_cap_microusd: int
    maximum_requests: int
    maximum_input_tokens: int
    maximum_output_tokens: int
    maximum_request_body_bytes: int
    maximum_input_rate_usd_per_million_tokens: Decimal
    maximum_output_rate_usd_per_million_tokens: Decimal
    cases_path: Path
    cases_sha256: str
    ledger_path: Path
    receipt_path: Path
    expires_at_utc: datetime

    @property
    def request_reserve_microusd(self) -> int:
        return request_reserve_microusd(
            self.maximum_input_tokens,
            self.maximum_output_tokens,
            self.maximum_input_rate_usd_per_million_tokens,
            self.maximum_output_rate_usd_per_million_tokens,
        )

    def ledger_identity(self) -> dict[str, Any]:
        return {
            "schema_version": LEDGER_SCHEMA_VERSION,
            "campaign_id": CAMPAIGN_ID,
            "endpoint": self.endpoint,
            "model_alias": self.model_alias,
            "expected_upstream_model": self.expected_upstream_model,
            "expected_provider": self.expected_provider,
            "aggregate_cap_microusd": self.aggregate_cap_microusd,
            "maximum_input_rate_usd_per_million_tokens": str(MAX_INPUT_RATE_USD_PER_MILLION),
            "maximum_output_rate_usd_per_million_tokens": str(MAX_OUTPUT_RATE_USD_PER_MILLION),
        }

    def job_identity(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "job_id": self.job_id,
            "approval_sha256": self.approval_sha256,
            "approved_head": self.approved_head,
            "cases_sha256": self.cases_sha256,
            "maximum_requests": self.maximum_requests,
            "maximum_input_tokens": self.maximum_input_tokens,
            "maximum_output_tokens": self.maximum_output_tokens,
            "maximum_input_rate_usd_per_million_tokens": str(self.maximum_input_rate_usd_per_million_tokens),
            "maximum_output_rate_usd_per_million_tokens": str(self.maximum_output_rate_usd_per_million_tokens),
        }


def load_approval(
    approval_path: Path,
    cases_path: Path,
    *,
    data_root: Path = DATA_ROOT,
    repo_root: Path = REPO_ROOT,
    now: datetime | None = None,
) -> SubRouteApproval:
    """Validate an exact human approval and its immutable synthetic case file."""
    root = Path(os.path.abspath(data_root))
    approvals_root = root / "artifacts" / "wrench-gateway-model-research" / "approvals"
    calls_root = root / "artifacts" / "wrench-gateway-model-research" / "subroute-calls"
    datasets_root = root / "datasets"
    approval_file = _safe_path(approval_path, approvals_root, must_exist=True)
    cases_file = _safe_path(cases_path, datasets_root, must_exist=True)
    approval, raw = _read_json_no_duplicates(approval_file, "approval")
    required = {
        "schema", "status", "approved_by", "approval_id", "job_id", "approved_head",
        "issued_at_utc", "expires_at_utc", "owner_authorization_ref", "data_scope",
        "caller_bundle_sha256", "campaign_id",
        "endpoint", "model_alias", "expected_upstream_model", "upstream_provider",
        "aggregate_cap_usd", "maximum_requests", "maximum_input_tokens",
        "maximum_output_tokens", "maximum_request_body_bytes",
        "maximum_input_rate_usd_per_million_tokens", "maximum_output_rate_usd_per_million_tokens",
        "cases_path", "cases_sha256", "ledger_path", "receipt_path",
        "automatic_retries", "allow_fallbacks",
    }
    if set(approval) != required:
        raise BudgetError("approval_fields_mismatch")
    if approval.get("schema") != APPROVAL_SCHEMA or approval.get("status") != "APPROVED":
        raise BudgetError("approval_status_or_schema_invalid")
    if approval.get("campaign_id") != CAMPAIGN_ID:
        raise BudgetError("campaign_id_mismatch")
    if approval.get("approved_by") != "human":
        raise BudgetError("human_approval_required")
    if approval.get("data_scope") != "wrench_authored_synthetic_only":
        raise BudgetError("only_open_synthetic_data_is_admitted")
    approval_id = approval.get("approval_id")
    job_id = approval.get("job_id")
    if (
        not isinstance(approval_id, str)
        or not approval_id.strip()
        or not isinstance(job_id, str)
        or not _JOB_ID.fullmatch(job_id)
    ):
        raise BudgetError("approval_identity_invalid")
    if approval_file.name != f"{job_id}.json":
        raise BudgetError("approval_path_job_mismatch")
    if approval.get("endpoint") != SUBROUTE_ENDPOINT:
        raise BudgetError("endpoint_not_approved_subroute")
    if approval.get("model_alias") != MODEL_ALIAS:
        raise BudgetError("model_alias_mismatch")
    if approval.get("expected_upstream_model") != EXPECTED_UPSTREAM_MODEL:
        raise BudgetError("expected_upstream_model_mismatch")
    if approval.get("upstream_provider") != EXPECTED_PROVIDER:
        raise BudgetError("upstream_provider_mismatch")
    if approval.get("automatic_retries") != 0 or approval.get("allow_fallbacks") is not False:
        raise BudgetError("retry_or_fallback_not_allowed")
    authority_ref = approval.get("owner_authorization_ref")
    if not isinstance(authority_ref, str) or not authority_ref.strip():
        raise BudgetError("owner_authorization_reference_missing")

    approved_head = approval.get("approved_head")
    if not isinstance(approved_head, str) or not re.fullmatch(r"[0-9a-fA-F]{40,64}", approved_head):
        raise BudgetError("approved_head_invalid")
    approved_head = approved_head.lower()
    if approved_head != _git_head(repo_root):
        raise BudgetError("approved_repository_head_changed")
    source_hash = approval.get("caller_bundle_sha256")
    if not isinstance(source_hash, str) or not _SHA256.fullmatch(source_hash):
        raise BudgetError("caller_bundle_hash_invalid")
    if source_hash != caller_bundle_sha256(repo_root):
        raise BudgetError("caller_bundle_changed_after_approval")
    issued = _parse_utc(approval.get("issued_at_utc"), "issued_at_utc")
    expires = _parse_utc(approval.get("expires_at_utc"), "expires_at_utc")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if issued > current or expires <= current or expires <= issued:
        raise BudgetError("approval_expired_or_invalid_window")

    maximum_requests = approval.get("maximum_requests")
    maximum_input_tokens = approval.get("maximum_input_tokens")
    maximum_output_tokens = approval.get("maximum_output_tokens")
    maximum_request_body_bytes = approval.get("maximum_request_body_bytes")
    bounds = (
        (maximum_requests, "maximum_requests", MAX_REQUESTS_PER_JOB),
        (maximum_input_tokens, "maximum_input_tokens", 2_000_000),
        (maximum_output_tokens, "maximum_output_tokens", 16_384),
        (maximum_request_body_bytes, "maximum_request_body_bytes", MAX_REQUEST_BODY_BYTES),
    )
    for value, name, maximum in bounds:
        if type(value) is not int or value <= 0 or value > maximum:
            raise BudgetError(f"{name}_out_of_bounds")
    if maximum_input_tokens < maximum_request_body_bytes + PROVIDER_FRAMING_TOKEN_OVERHEAD:
        raise BudgetError("input_token_ceiling_below_body_byte_bound")

    input_rate = _decimal(approval.get("maximum_input_rate_usd_per_million_tokens"), "input_rate", positive=True)
    output_rate = _decimal(approval.get("maximum_output_rate_usd_per_million_tokens"), "output_rate", positive=True)
    if input_rate > MAX_INPUT_RATE_USD_PER_MILLION or output_rate > MAX_OUTPUT_RATE_USD_PER_MILLION:
        raise BudgetError("price_filter_exceeds_current_approved_rate_ceiling")
    cap = usd_to_microusd(approval.get("aggregate_cap_usd"), "aggregate_cap")
    per_request = request_reserve_microusd(maximum_input_tokens, maximum_output_tokens, input_rate, output_rate)
    if cap < per_request or cap < per_request * maximum_requests:
        raise BudgetError("aggregate_cap_does_not_cover_all_approved_request_worst_cases")

    expected_cases = Path(os.path.abspath(cases_file))
    if approval.get("cases_path") != str(expected_cases):
        raise BudgetError("cases_path_mismatch")
    if not isinstance(approval.get("cases_sha256"), str) or not _SHA256.fullmatch(approval["cases_sha256"]):
        raise BudgetError("cases_sha256_invalid")
    case_hash = _sha256(cases_file.read_bytes())
    if case_hash != approval["cases_sha256"]:
        raise BudgetError("cases_hash_mismatch")

    expected_ledger = calls_root / f"{CAMPAIGN_ID}.sqlite"
    expected_receipt = calls_root / f"{job_id}.json"
    ledger_path = Path(os.path.abspath(approval.get("ledger_path", "")))
    receipt_path = Path(os.path.abspath(approval.get("receipt_path", "")))
    if ledger_path != expected_ledger or receipt_path != expected_receipt:
        raise BudgetError("ledger_or_receipt_path_mismatch")
    if receipt_path.exists():
        raise BudgetError("receipt_already_exists")

    return SubRouteApproval(
        approval_id=approval_id,
        job_id=job_id,
        approval_sha256=_sha256(raw),
        approved_head=approved_head,
        endpoint=SUBROUTE_ENDPOINT,
        model_alias=MODEL_ALIAS,
        expected_upstream_model=EXPECTED_UPSTREAM_MODEL,
        expected_provider=EXPECTED_PROVIDER,
        aggregate_cap_microusd=cap,
        maximum_requests=maximum_requests,
        maximum_input_tokens=maximum_input_tokens,
        maximum_output_tokens=maximum_output_tokens,
        maximum_request_body_bytes=maximum_request_body_bytes,
        maximum_input_rate_usd_per_million_tokens=input_rate,
        maximum_output_rate_usd_per_million_tokens=output_rate,
        cases_path=cases_file,
        cases_sha256=case_hash,
        ledger_path=ledger_path,
        receipt_path=receipt_path,
        expires_at_utc=expires,
    )


class BudgetLedger:
    """SQLite-backed, cross-process pre-dispatch reservations and settlements."""

    def __init__(self, approval: SubRouteApproval, *, storage_root: Path = DATA_ROOT) -> None:
        self.approval = approval
        self.storage_root = Path(os.path.abspath(storage_root))
        self.path = _safe_path(approval.ledger_path, self.storage_root, must_exist=False)
        expected_path = (
            self.storage_root
            / "artifacts"
            / "wrench-gateway-model-research"
            / "subroute-calls"
            / f"{CAMPAIGN_ID}.sqlite"
        )
        if self.path != expected_path:
            raise BudgetError("campaign_ledger_path_mismatch")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path = _safe_path(self.path, self.storage_root, must_exist=False)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute("PRAGMA journal_mode=DELETE")
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version not in (0, LEDGER_SCHEMA_VERSION):
                raise BudgetError("campaign_ledger_schema_version_unsupported")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS ledger_meta ("
                "singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
                "identity_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS jobs ("
                "job_id TEXT PRIMARY KEY, identity_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS calls ("
                "request_id TEXT PRIMARY KEY, "
                "job_id TEXT NOT NULL, case_id TEXT NOT NULL, "
                "request_sha256 TEXT NOT NULL, "
                "reserved_microusd INTEGER NOT NULL CHECK(reserved_microusd > 0), "
                "status TEXT NOT NULL CHECK(status IN ('reserved','dispatched','settled','unknown')), "
                "actual_microusd INTEGER, "
                "response_model TEXT, provider_name TEXT, generation_id TEXT, "
                "prompt_tokens INTEGER, completion_tokens INTEGER, total_tokens INTEGER, "
                "usage_json TEXT, receipt_json TEXT, failure_code TEXT, "
                "created_at_utc TEXT NOT NULL, updated_at_utc TEXT NOT NULL, "
                "UNIQUE(job_id, case_id))"
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(calls)").fetchall()}
            if "job_id" not in columns:
                raise BudgetError("campaign_ledger_schema_migration_required")
            connection.execute("CREATE INDEX IF NOT EXISTS calls_by_status ON calls(status)")
            connection.execute(f"PRAGMA user_version={LEDGER_SCHEMA_VERSION}")
        finally:
            connection.close()

    def _begin(self) -> sqlite3.Connection:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            identity_json = _canonical_json(self.approval.ledger_identity()).decode("utf-8")
            row = connection.execute("SELECT identity_json FROM ledger_meta WHERE singleton=1").fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO ledger_meta(singleton, identity_json) VALUES(1, ?)",
                    (identity_json,),
                )
            elif row["identity_json"] != identity_json:
                raise BudgetError("campaign_ledger_approval_identity_mismatch")
            job_identity_json = _canonical_json(self.approval.job_identity()).decode("utf-8")
            job = connection.execute("SELECT identity_json FROM jobs WHERE job_id=?", (self.approval.job_id,)).fetchone()
            if job is None:
                connection.execute(
                    "INSERT INTO jobs(job_id,identity_json) VALUES(?,?)",
                    (self.approval.job_id, job_identity_json),
                )
            elif job["identity_json"] != job_identity_json:
                raise BudgetError("ledger_approval_identity_mismatch")
            return connection
        except BaseException:
            connection.rollback()
            connection.close()
            raise

    def reserve(self, case_id: str, request_sha256: str) -> tuple[str, int]:
        if not isinstance(case_id, str) or not case_id.strip() or len(case_id) > 160:
            raise BudgetError("case_id_invalid")
        if not isinstance(request_sha256, str) or not _SHA256.fullmatch(request_sha256):
            raise BudgetError("request_sha256_invalid")
        request_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        amount = self.approval.request_reserve_microusd
        connection = self._begin()
        try:
            open_call = connection.execute(
                "SELECT request_id, status FROM calls WHERE status IN ('reserved','dispatched','unknown') LIMIT 1"
            ).fetchone()
            if open_call is not None:
                raise BudgetError("unresolved_provider_call_blocks_dispatch")
            campaign_count = int(connection.execute("SELECT COUNT(*) FROM calls").fetchone()[0])
            if campaign_count >= MAX_REQUESTS_PER_CAMPAIGN:
                raise BudgetError("campaign_request_count_exhausted")
            job_count = int(
                connection.execute("SELECT COUNT(*) FROM calls WHERE job_id=?", (self.approval.job_id,)).fetchone()[0]
            )
            if job_count >= self.approval.maximum_requests:
                raise BudgetError("approved_request_count_exhausted")
            exposure = int(
                connection.execute(
                    "SELECT COALESCE(SUM(CASE WHEN status='settled' THEN actual_microusd "
                    "WHEN status IN ('reserved','dispatched','unknown') THEN reserved_microusd ELSE 0 END),0) "
                    "FROM calls"
                ).fetchone()[0]
            )
            if exposure + amount > self.approval.aggregate_cap_microusd:
                raise BudgetError("aggregate_cap_would_be_exceeded")
            connection.execute(
                "INSERT INTO calls(request_id,job_id,case_id,request_sha256,reserved_microusd,status,created_at_utc,updated_at_utc) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (request_id, self.approval.job_id, case_id, request_sha256, amount, "reserved", now, now),
            )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return request_id, amount

    def mark_dispatched(self, request_id: str) -> None:
        self._transition(request_id, "reserved", "dispatched")

    def mark_unknown(self, request_id: str, failure_code: str) -> None:
        if not isinstance(failure_code, str) or not re.fullmatch(r"[a-z0-9_]{1,80}", failure_code):
            raise BudgetError("failure_code_invalid")
        connection = self._begin()
        try:
            cursor = connection.execute(
                "UPDATE calls SET status='unknown',failure_code=?,updated_at_utc=? "
                "WHERE request_id=? AND status IN ('reserved','dispatched')",
                (failure_code, datetime.now(timezone.utc).isoformat(), request_id),
            )
            if cursor.rowcount != 1:
                raise BudgetError("call_not_resolvable_to_unknown")
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _transition(self, request_id: str, old: str, new: str) -> None:
        connection = self._begin()
        try:
            cursor = connection.execute(
                "UPDATE calls SET status=?,updated_at_utc=? WHERE request_id=? AND status=?",
                (new, datetime.now(timezone.utc).isoformat(), request_id, old),
            )
            if cursor.rowcount != 1:
                raise BudgetError("call_state_transition_invalid")
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def settle(
        self,
        request_id: str,
        *,
        provider_name: str,
        response_model: str,
        generation_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        actual_cost_usd: Any,
        usage: dict[str, Any],
        safe_result: dict[str, Any],
    ) -> int:
        """Settle only a complete receipt; invalid receipts remain fully reserved."""
        failure: str | None = None
        if not isinstance(provider_name, str) or provider_name.casefold() != self.approval.expected_provider:
            failure = "provider_identity_mismatch"
        elif response_model != self.approval.expected_upstream_model:
            failure = "response_model_mismatch"
        elif not isinstance(generation_id, str) or not generation_id.strip() or len(generation_id) > 256:
            failure = "generation_id_missing"
        elif any(type(value) is not int or value < 0 for value in (prompt_tokens, completion_tokens, total_tokens)):
            failure = "usage_tokens_invalid"
        elif prompt_tokens > self.approval.maximum_input_tokens or completion_tokens > self.approval.maximum_output_tokens:
            failure = "usage_exceeds_approved_token_ceiling"
        elif total_tokens != prompt_tokens + completion_tokens:
            failure = "usage_total_mismatch"
        elif not isinstance(usage, dict) or not isinstance(safe_result, dict):
            failure = "usage_or_result_shape_invalid"

        try:
            actual_microusd = usd_to_microusd(actual_cost_usd, "actual_cost")
        except BudgetError:
            actual_microusd = 0
            failure = failure or "actual_cost_invalid"

        connection = self._begin()
        try:
            row = connection.execute(
                "SELECT reserved_microusd,status FROM calls WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if row is None or row["status"] != "dispatched":
                raise BudgetError("call_not_in_dispatched_state")
            if actual_microusd > int(row["reserved_microusd"]):
                failure = failure or "actual_cost_exceeds_request_reserve"
            if failure is not None:
                connection.execute(
                    "UPDATE calls SET status='unknown',failure_code=?,updated_at_utc=? WHERE request_id=?",
                    (failure, datetime.now(timezone.utc).isoformat(), request_id),
                )
                connection.commit()
                raise BudgetError(f"receipt_not_settled_{failure}")
            usage_json = _canonical_json(usage).decode("utf-8")
            receipt_json = _canonical_json(safe_result).decode("utf-8")
            connection.execute(
                "UPDATE calls SET status='settled',actual_microusd=?,response_model=?,provider_name=?,generation_id=?,"
                "prompt_tokens=?,completion_tokens=?,total_tokens=?,usage_json=?,receipt_json=?,failure_code=NULL,updated_at_utc=? "
                "WHERE request_id=?",
                (
                    actual_microusd, response_model, provider_name, generation_id,
                    prompt_tokens, completion_tokens, total_tokens, usage_json, receipt_json,
                    datetime.now(timezone.utc).isoformat(), request_id,
                ),
            )
            connection.commit()
            return actual_microusd
        except BaseException:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def settled_cases(self) -> dict[str, dict[str, Any]]:
        connection = self._begin()
        try:
            rows = connection.execute(
                "SELECT case_id,receipt_json,usage_json,actual_microusd,status FROM calls "
                "WHERE job_id=? ORDER BY created_at_utc,request_id",
                (self.approval.job_id,),
            ).fetchall()
            result: dict[str, dict[str, Any]] = {}
            for row in rows:
                if row["status"] == "settled":
                    result[row["case_id"]] = {
                        "receipt": json.loads(row["receipt_json"]),
                        "usage": json.loads(row["usage_json"]),
                        "actual_microusd": int(row["actual_microusd"]),
                    }
            connection.commit()
            return result
        except BaseException:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def summary(self) -> dict[str, Any]:
        connection = self._begin()
        try:
            rows = connection.execute("SELECT job_id,status,reserved_microusd,actual_microusd FROM calls").fetchall()
            settled = sum(int(row["actual_microusd"]) for row in rows if row["status"] == "settled")
            outstanding = sum(
                int(row["reserved_microusd"])
                for row in rows
                if row["status"] in {"reserved", "dispatched", "unknown"}
            )
            job_rows = [row for row in rows if row["job_id"] == self.approval.job_id]
            result = {
                "campaign_id": CAMPAIGN_ID,
                "job_id": self.approval.job_id,
                "approved_cap_microusd": self.approval.aggregate_cap_microusd,
                "settled_spend_microusd": settled,
                "outstanding_reserve_microusd": outstanding,
                "available_microusd": self.approval.aggregate_cap_microusd - settled - outstanding,
                "request_count": len(rows),
                "job_request_count": len(job_rows),
                "unresolved_count": sum(row["status"] in {"reserved", "dispatched", "unknown"} for row in rows),
                "job_unresolved_count": sum(
                    row["status"] in {"reserved", "dispatched", "unknown"} for row in job_rows
                ),
            }
            connection.commit()
            return result
        except BaseException:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()
