"""Validate a provider-authoritative paid-cost receipt for the paired canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlparse

try:
    from .probe_paired_real_client_canary import (
        PARENT_CONTRACT_PATH,
        _validate_paid_baseline_child_contract,
    )
except ImportError:
    from probe_paired_real_client_canary import (  # type: ignore[no-redef]
        PARENT_CONTRACT_PATH,
        _validate_paid_baseline_child_contract,
    )

SCHEMA = "wrench.paid-cost-receipt.v2"
AUTHORIZED = "approved_real_workflow"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
EVIDENCE_SCHEMA = "wrench.provider-cost-export.v1"
OPENAI_AGGREGATE_EVIDENCE_SCHEMA = "wrench.openai-cost-export.aggregate.v1"
OPENAI_COSTS_ENDPOINT = "https://api.openai.com/v1/organization/costs"
PROVIDER_COST_ACCOUNTING_SCHEMA = "wrench.provider-cost-accounting-binding.v1"
SECONDS_PER_DAY = 24 * 60 * 60


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_openai_aggregate_evidence(
    provider_evidence: dict,
    receipt: dict,
    approved_child: dict | None,
    errors: list[str],
) -> tuple[bool, float | None]:
    """Bind a daily OpenAI Costs export only through a human-approved isolated scope."""
    valid = True

    def fail(code: str) -> None:
        nonlocal valid
        valid = False
        errors.append(code)

    if provider_evidence.get("provider") != "openai":
        fail("provider_evidence_provider_invalid")
    if provider_evidence.get("endpoint") != OPENAI_COSTS_ENDPOINT:
        fail("provider_evidence_endpoint_invalid")

    scope = provider_evidence.get("scope")
    child_binding = approved_child.get("cost_accounting") if approved_child else None
    if not isinstance(scope, dict):
        fail("provider_evidence_aggregate_scope_invalid")
        scope = {}
    if not isinstance(child_binding, dict):
        fail("approved_child_aggregate_cost_binding_missing")
        child_binding = {}

    required_binding = {
        "schema": PROVIDER_COST_ACCOUNTING_SCHEMA,
        "provider": "openai",
        "mode": "openai_organization_costs_daily_aggregate",
        "export_endpoint": OPENAI_COSTS_ENDPOINT,
        "project_id": scope.get("project_id"),
        "api_key_id": scope.get("api_key_id"),
        "bucket_start_time": scope.get("bucket_start_time"),
        "bucket_end_time": scope.get("bucket_end_time"),
        "isolation_evidence_reference": scope.get("isolation_evidence_reference"),
        "dedicated_project": True,
        "exclusive_api_key": True,
        "exclusive_for_entire_interval": True,
    }
    for field, expected in required_binding.items():
        if child_binding.get(field) != expected:
            fail("approved_child_aggregate_binding_" + field + "_mismatch")

    for field in ("project_id", "api_key_id", "isolation_evidence_reference"):
        value = scope.get(field)
        if not isinstance(value, str) or not value.strip():
            fail("provider_evidence_aggregate_" + field + "_missing")
    for field in ("dedicated_project", "exclusive_api_key", "exclusive_for_entire_interval"):
        if scope.get(field) is not True:
            fail("provider_evidence_aggregate_" + field + "_not_confirmed")

    start = scope.get("bucket_start_time")
    end = scope.get("bucket_end_time")
    interval_valid = (
        isinstance(start, int)
        and not isinstance(start, bool)
        and isinstance(end, int)
        and not isinstance(end, bool)
        and start >= 0
        and end > start
        and start % SECONDS_PER_DAY == 0
        and end % SECONDS_PER_DAY == 0
        and end - start <= 2 * SECONDS_PER_DAY
    )
    if not interval_valid:
        fail("provider_evidence_aggregate_interval_invalid")

    export = provider_evidence.get("export")
    if not isinstance(export, dict):
        fail("provider_evidence_aggregate_export_invalid")
        return False, None
    export_hash = provider_evidence.get("export_sha256")
    if (
        not isinstance(export_hash, str)
        or len(export_hash) != 64
        or any(character not in "0123456789abcdef" for character in export_hash)
        or export_hash != _canonical_sha256(export)
    ):
        fail("provider_evidence_aggregate_export_hash_mismatch")
    if export.get("object") != "page":
        fail("provider_evidence_aggregate_page_object_invalid")
    if export.get("has_more") is not False or export.get("next_page") is not None:
        fail("provider_evidence_aggregate_export_incomplete")

    buckets = export.get("data")
    if not isinstance(buckets, list) or not buckets:
        fail("provider_evidence_aggregate_buckets_missing")
        return False, None
    if interval_valid and len(buckets) != (end - start) // SECONDS_PER_DAY:
        fail("provider_evidence_aggregate_bucket_count_mismatch")

    project_id = scope.get("project_id")
    api_key_id = scope.get("api_key_id")
    total_cost = 0.0
    for index, bucket in enumerate(buckets):
        if not isinstance(bucket, dict):
            fail("provider_evidence_aggregate_bucket_invalid")
            continue
        expected_start = start + index * SECONDS_PER_DAY if interval_valid else None
        expected_end = expected_start + SECONDS_PER_DAY if expected_start is not None else None
        if (
            bucket.get("object") != "bucket"
            or bucket.get("start_time") != expected_start
            or bucket.get("end_time") != expected_end
        ):
            fail("provider_evidence_aggregate_bucket_coverage_invalid")
        rows = bucket.get("results")
        if not isinstance(rows, list):
            fail("provider_evidence_aggregate_results_invalid")
            continue
        for row in rows:
            if not isinstance(row, dict) or row.get("object") != "organization.costs.result":
                fail("provider_evidence_aggregate_result_invalid")
                continue
            if row.get("project_id") != project_id or row.get("api_key_id") != api_key_id:
                fail("provider_evidence_aggregate_identity_mismatch")
            amount = row.get("amount")
            if not isinstance(amount, dict):
                fail("provider_evidence_aggregate_amount_invalid")
                continue
            value = amount.get("value")
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value < 0
            ):
                fail("provider_evidence_aggregate_amount_invalid")
                continue
            if not isinstance(amount.get("currency"), str) or amount["currency"].lower() != "usd":
                fail("provider_evidence_aggregate_currency_invalid")
                continue
            total_cost += float(value)

    receipt_cost = receipt.get("cost_usd")
    if (
        not isinstance(receipt_cost, (int, float))
        or isinstance(receipt_cost, bool)
        or not math.isfinite(receipt_cost)
        or not math.isclose(total_cost, float(receipt_cost), rel_tol=1e-9, abs_tol=1e-9)
    ):
        fail("provider_evidence_aggregate_cost_mismatch")
    return valid, total_cost


def workload_hash(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("workload_must_be_object")
    if payload.get("schema") != "wrench.paired-canary-workload.v1":
        raise ValueError("workload_schema_invalid")
    if payload.get("authorization") != AUTHORIZED:
        raise ValueError("workload_authorization_invalid")
    if not isinstance(payload.get("workload_id"), str) or not payload["workload_id"].strip():
        raise ValueError("workload_id_invalid")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != 1 or not isinstance(cases[0], dict):
        raise ValueError("workload_must_contain_one_case")
    if any(not isinstance(cases[0].get(key), str) or not cases[0][key].strip() for key in ("case_id", "prompt", "expected_observation")):
        raise ValueError("workload_case_invalid")
    payload.pop("workload_sha256", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(
    receipt: object,
    expected_workload_hash: str,
    provider_evidence: object,
    *,
    parent_contract: object,
    parent_contract_sha256: str,
    child_contract: object,
    child_contract_sha256: str,
) -> dict:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        receipt = {}
        errors.append("receipt_must_be_object")
    if receipt.get("template") is True:
        errors.append("template_not_receipt")
    if receipt.get("schema") != SCHEMA:
        errors.append("schema_invalid")
    if receipt.get("authorization") != AUTHORIZED:
        errors.append("authorization_invalid")
    if receipt.get("workload_sha256") != expected_workload_hash:
        errors.append("workload_hash_mismatch")
    approved_child: dict | None = None
    requested_endpoint = receipt.get("requested_endpoint")
    requested_model = receipt.get("requested_model")
    if not isinstance(requested_endpoint, str) or not isinstance(requested_model, str):
        errors.append("requested_route_missing")
    else:
        try:
            approved_child = _validate_paid_baseline_child_contract(
                child_contract,
                parent_contract=parent_contract,
                parent_contract_sha256=parent_contract_sha256,
                baseline_url=requested_endpoint,
                baseline_model=requested_model,
                workload_sha256=expected_workload_hash,
                workload_authorization=receipt.get("authorization", ""),
            )
        except (RuntimeError, TypeError):
            errors.append("approved_canary_contract_invalid")
    if receipt.get("parent_contract_sha256") != parent_contract_sha256:
        errors.append("parent_contract_hash_mismatch")
    if receipt.get("child_contract_sha256") != child_contract_sha256:
        errors.append("child_contract_hash_mismatch")
    if approved_child is not None:
        approved_cap = approved_child["max_spend_usd"]
        if receipt.get("model") != approved_child["expected_provider_model"]:
            errors.append("provider_model_mismatch")
        if (
            isinstance(receipt.get("cost_usd"), (int, float))
            and not isinstance(receipt.get("cost_usd"), bool)
            and math.isfinite(receipt["cost_usd"])
            and receipt["cost_usd"] > approved_cap
        ):
            errors.append("paid_cost_exceeds_approved_child_cap")
    if receipt.get("source") != "provider_export":
        errors.append("source_not_provider_export")
    if receipt.get("paid_transaction_receipt") is not True:
        errors.append("paid_transaction_receipt_not_true")
    if receipt.get("currency") != "USD":
        errors.append("currency_invalid")
    endpoint = receipt.get("endpoint")
    parsed = urlparse(endpoint) if isinstance(endpoint, str) else None
    if parsed is None or parsed.scheme.lower() != "https" or not parsed.hostname or parsed.hostname in LOOPBACK_HOSTS or parsed.username or parsed.password:
        errors.append("endpoint_must_be_https_non_loopback")
    request_ids = receipt.get("request_ids")
    if (
        not isinstance(request_ids, list)
        or not request_ids
        or not all(isinstance(item, str) and item.strip() for item in request_ids)
        or len(set(request_ids)) != len(request_ids)
    ):
        errors.append("request_ids_missing")
    usage = receipt.get("usage")
    receipt_usage_valid = False
    if not isinstance(usage, dict):
        errors.append("usage_missing")
    else:
        required_usage = ("prompt_tokens", "completion_tokens", "total_tokens")
        if any(not isinstance(usage.get(key), int) or isinstance(usage.get(key), bool) or usage[key] < 0 for key in required_usage):
            errors.append("usage_invalid")
        elif usage["prompt_tokens"] + usage["completion_tokens"] != usage["total_tokens"]:
            errors.append("usage_total_mismatch")
        else:
            receipt_usage_valid = True
    cost_usd = receipt.get("cost_usd")
    if not isinstance(cost_usd, (int, float)) or isinstance(cost_usd, bool) or not math.isfinite(cost_usd) or cost_usd < 0:
        errors.append("cost_invalid")
    clients = receipt.get("clients")
    if not isinstance(clients, dict) or any(
        not isinstance(clients.get(name), dict) or clients[name].get("correct") is not True
        for name in ("opencode", "deepseek_harness")
    ):
        errors.append("client_answers_incomplete")
    evidence_hash = _canonical_sha256(provider_evidence) if isinstance(provider_evidence, (dict, list)) else None
    cost_binding_level = "unverified"
    request_level_cost_attribution = False
    aggregate_scope_confirmed = False
    if not isinstance(provider_evidence, dict):
        errors.append("provider_evidence_must_be_object")
    else:
        if provider_evidence.get("template") is True:
            errors.append("provider_evidence_template_not_export")
        if provider_evidence.get("paid_transaction_receipt") is not True:
            errors.append("provider_evidence_not_paid_receipt")
        if not isinstance(provider_evidence.get("billing_reference"), str) or not provider_evidence["billing_reference"].strip():
            errors.append("billing_reference_missing")
        if receipt.get("provider_evidence_sha256") != evidence_hash:
            errors.append("provider_evidence_hash_mismatch")
        evidence_schema = provider_evidence.get("schema")
        if evidence_schema == EVIDENCE_SCHEMA:
            cost_binding_level = "provider_request_rows"
            request_level_cost_attribution = True
            child_accounting = approved_child.get("cost_accounting") if approved_child else None
            if not isinstance(child_accounting, dict) or child_accounting.get("mode") != "provider_request_rows":
                errors.append("provider_cost_accounting_mode_mismatch")
            records = provider_evidence.get("records")
            if not isinstance(records, list) or not records or not all(isinstance(row, dict) for row in records):
                errors.append("provider_evidence_records_invalid")
            else:
                evidence_ids = [row.get("request_id") for row in records]
                if not all(isinstance(item, str) and item.strip() for item in evidence_ids) or len(set(evidence_ids)) != len(evidence_ids):
                    errors.append("provider_evidence_request_ids_invalid")
                if isinstance(request_ids, list) and set(evidence_ids) != set(request_ids):
                    errors.append("provider_evidence_request_ids_mismatch")
                if any(row.get("model") != receipt.get("model") for row in records):
                    errors.append("provider_evidence_model_mismatch")
                record_usage = ("prompt_tokens", "completion_tokens", "total_tokens")
                totals: dict[str, int] = {}
                records_valid = True
                for key in record_usage:
                    values = [row.get(key) for row in records]
                    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
                        records_valid = False
                    else:
                        totals[key] = sum(values)
                if not records_valid:
                    errors.append("provider_evidence_usage_invalid")
                elif receipt_usage_valid and any(totals[key] != usage[key] for key in record_usage):
                    errors.append("provider_evidence_usage_mismatch")
                record_costs = [row.get("cost_usd") for row in records]
                if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0 for value in record_costs):
                    errors.append("provider_evidence_cost_invalid")
                elif isinstance(cost_usd, (int, float)) and not isinstance(cost_usd, bool) and math.isfinite(cost_usd):
                    if not math.isclose(sum(record_costs), cost_usd, rel_tol=1e-9, abs_tol=1e-9):
                        errors.append("provider_evidence_cost_mismatch")
                if any(row.get("currency") != "USD" for row in records):
                    errors.append("provider_evidence_currency_mismatch")
        elif evidence_schema == OPENAI_AGGREGATE_EVIDENCE_SCHEMA:
            cost_binding_level = "isolated_project_key_daily_aggregate"
            child_accounting = approved_child.get("cost_accounting") if approved_child else None
            if not isinstance(child_accounting, dict) or child_accounting.get("mode") != "openai_organization_costs_daily_aggregate":
                errors.append("provider_cost_accounting_mode_mismatch")
            aggregate_scope_confirmed, _ = _validate_openai_aggregate_evidence(
                provider_evidence, receipt, approved_child, errors
            )
        else:
            errors.append("provider_evidence_schema_invalid")
    return {
        "schema": "wrench.paid-cost-receipt-validation.v2",
        "status": "PASS_PAID_COST_EVIDENCE_BOUND" if not errors else "FAIL_PAID_COST_EVIDENCE_BOUND",
        "errors": errors,
        "workload_sha256": expected_workload_hash,
        "evidence_hash": evidence_hash,
        "parent_contract_sha256": parent_contract_sha256,
        "child_contract_sha256": child_contract_sha256,
        "approved_max_spend_usd": approved_child.get("max_spend_usd") if approved_child else None,
        "evidence_bound_and_consistent": not errors,
        "cost_binding_level": cost_binding_level,
        "request_level_cost_attribution": request_level_cost_attribution,
        "aggregate_scope_assertions_consistent": aggregate_scope_confirmed,
        "spend_cap_observed": approved_child is not None,
        "human_source_review_required": True,
        "production_enablement": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--provider-evidence", type=Path, required=True)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--child-contract", type=Path, required=True)
    parser.add_argument("--parent-contract", type=Path, default=PARENT_CONTRACT_PATH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    provider_evidence = json.loads(args.provider_evidence.read_text(encoding="utf-8"))
    child_contract_bytes = args.child_contract.read_bytes()
    parent_contract_bytes = args.parent_contract.read_bytes()
    result = validate(
        json.loads(args.receipt.read_text(encoding="utf-8")),
        workload_hash(args.workload),
        provider_evidence,
        parent_contract=json.loads(parent_contract_bytes.decode("utf-8")),
        parent_contract_sha256=hashlib.sha256(parent_contract_bytes).hexdigest(),
        child_contract=json.loads(child_contract_bytes.decode("utf-8")),
        child_contract_sha256=hashlib.sha256(child_contract_bytes).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS_PAID_COST_EVIDENCE_BOUND" else 1


if __name__ == "__main__":
    raise SystemExit(main())
