import hashlib
import json

from tools.validate_paid_cost_receipt import validate, workload_hash


def _evidence():
    return {
        "schema": "wrench.provider-cost-export.v1",
        "paid_transaction_receipt": True,
        "billing_reference": "invoice-2026-09",
        "records": [
            {
                "request_id": "req-1",
                "model": "provider-model-test",
                "prompt_tokens": 60,
                "completion_tokens": 12,
                "total_tokens": 72,
                "cost_usd": 0.006,
                "currency": "USD",
            },
            {
                "request_id": "req-2",
                "model": "provider-model-test",
                "prompt_tokens": 40,
                "completion_tokens": 8,
                "total_tokens": 48,
                "cost_usd": 0.004,
                "currency": "USD",
            },
        ],
    }


def _evidence_hash(evidence):
    canonical = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _aggregate_evidence():
    start = 1730419200
    end = start + 86400
    export = {
        "object": "page",
        "data": [
            {
                "object": "bucket",
                "start_time": start,
                "end_time": end,
                "results": [
                    {
                        "object": "organization.costs.result",
                        "amount": {"value": 0.01, "currency": "usd"},
                        "line_item": "gpt-6-test, input_tokens",
                        "project_id": "proj-dedicated",
                        "api_key_id": "key-dedicated",
                        "quantity": 120,
                        "quantity_unit": "tokens",
                    }
                ],
            }
        ],
        "has_more": False,
        "next_page": None,
    }
    return {
        "schema": "wrench.openai-cost-export.aggregate.v1",
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/organization/costs",
        "paid_transaction_receipt": True,
        "billing_reference": "openai-costs-canary-day",
        "scope": {
            "project_id": "proj-dedicated",
            "api_key_id": "key-dedicated",
            "bucket_start_time": start,
            "bucket_end_time": end,
            "dedicated_project": True,
            "exclusive_api_key": True,
            "exclusive_for_entire_interval": True,
            "isolation_evidence_reference": "human-reviewed-project-key-isolation",
        },
        "export_sha256": _evidence_hash(export),
        "export": export,
    }


def _aggregate_authorization(expected_workload_hash):
    authorization = list(_authorization(expected_workload_hash))
    authorization[2]["cost_accounting"] = {
        "schema": "wrench.provider-cost-accounting-binding.v1",
        "provider": "openai",
        "mode": "openai_organization_costs_daily_aggregate",
        "export_endpoint": "https://api.openai.com/v1/organization/costs",
        "project_id": "proj-dedicated",
        "api_key_id": "key-dedicated",
        "bucket_start_time": 1730419200,
        "bucket_end_time": 1730505600,
        "dedicated_project": True,
        "exclusive_api_key": True,
        "exclusive_for_entire_interval": True,
        "isolation_evidence_reference": "human-reviewed-project-key-isolation",
        "current_project_spend_usd": 0.0,
        "project_hard_limit_usd": 0.01,
        "hard_limit_overshoot_reserve_usd": 0.001,
        "spend_headroom_evidence_reference": "human-reviewed-spend-limit-snapshot",
    }
    child_bytes = json.dumps(authorization[2], indent=2).encode("utf-8")
    authorization[3] = hashlib.sha256(child_bytes).hexdigest()
    return tuple(authorization)


def _authorization(workload_sha256, *, parent_budget_usd=0.02, child_cap_usd=0.015):
    parent = {
        "contract_id": "wrench-slm-productive-value-2026-09-22",
        "collaboration": {
            "bounds": {
                "monetary_budget": parent_budget_usd,
                "paid_canary_route_allowance": {
                    "schema": "wrench.paid-canary-route-allowance.v1",
                    "decision": "human.approve_commit",
                    "status": "APPROVED",
                    "approved_by": "test-human",
                    "approval_reference": "test-only-route-approval",
                    "routes": [
                        {
                            "endpoint": "http://localhost:4000/v1",
                            "gateway_model_alias": "gateway-alias-test",
                            "expected_provider_model": "provider-model-test",
                        }
                    ],
                },
            }
        },
    }
    parent_bytes = json.dumps(parent, indent=2).encode("utf-8")
    parent_hash = hashlib.sha256(parent_bytes).hexdigest()
    child = {
        "schema": "wrench.paid-canary-child-contract.v3",
        "parent_contract_id": "wrench-slm-productive-value-2026-09-22",
        "parent_contract_sha256": parent_hash,
        "decision": "human.approve_commit",
        "status": "APPROVED",
        "approved_by": "test-human",
        "approval_reference": "test-only-approval",
        "workload_sha256": workload_sha256,
        "endpoint": "http://localhost:4000/v1",
        "model": "gateway-alias-test",
        "expected_provider_model": "provider-model-test",
        "repetitions": 1,
        "max_spend_usd": child_cap_usd,
        "spend_cap_kind": "provider_hard_cap",
        "spend_cap_reference": "test-only-provider-cap",
        "cost_accounting": {
            "schema": "wrench.provider-cost-accounting-binding.v1",
            "provider": "provider-test",
            "mode": "provider_request_rows",
            "export_endpoint": "https://provider.example/v1/costs",
            "export_path_reference": "test-only-request-cost-export",
        },
    }
    child_bytes = json.dumps(child, indent=2).encode("utf-8")
    return parent, parent_hash, child, hashlib.sha256(child_bytes).hexdigest()


def _valid_receipt(workload_sha256, evidence, parent_hash, child_hash):
    return {
        "schema": "wrench.paid-cost-receipt.v2",
        "authorization": "approved_real_workflow",
        "source": "provider_export",
        "paid_transaction_receipt": True,
        "endpoint": "https://provider.example/v1",
        "requested_endpoint": "http://localhost:4000/v1",
        "requested_model": "gateway-alias-test",
        "parent_contract_sha256": parent_hash,
        "child_contract_sha256": child_hash,
        "workload_sha256": workload_sha256,
        "model": "provider-model-test",
        "request_ids": ["req-1", "req-2"],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        "cost_usd": 0.01,
        "currency": "USD",
        "provider_evidence_sha256": _evidence_hash(evidence),
        "clients": {"opencode": {"correct": True}, "deepseek_harness": {"correct": True}},
    }


def _validate(receipt, expected_hash, evidence, authorization):
    parent, parent_hash, child, child_hash = authorization
    return validate(
        receipt,
        expected_hash,
        evidence,
        parent_contract=parent,
        parent_contract_sha256=parent_hash,
        child_contract=child,
        child_contract_sha256=child_hash,
    )


def test_provider_evidence_matches_receipt(tmp_path):
    workload = tmp_path / "workload.json"
    workload.write_text(
        '{"schema":"wrench.paired-canary-workload.v1","workload_id":"x","authorization":"approved_real_workflow","cases":[{"case_id":"c1","prompt":"p","expected_observation":"x"}]}',
        encoding="utf-8",
    )
    evidence = _evidence()
    expected_hash = workload_hash(workload)
    authorization = _authorization(expected_hash)
    result = _validate(_valid_receipt(expected_hash, evidence, authorization[1], authorization[3]), expected_hash, evidence, authorization)

    assert result["status"] == "PASS_PAID_COST_EVIDENCE_BOUND"
    assert result["evidence_bound_and_consistent"] is True
    assert result["human_source_review_required"] is True


def test_paid_cost_above_exact_approved_child_cap_is_rejected():
    expected = "f" * 64
    evidence = _evidence()
    authorization = _authorization(expected, child_cap_usd=0.009)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "FAIL_PAID_COST_EVIDENCE_BOUND"
    assert "paid_cost_exceeds_approved_child_cap" in result["errors"]


def test_provider_model_must_match_separately_approved_child_identity():
    expected = "a" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["model"] = "unapproved-provider-model"

    result = _validate(receipt, expected, evidence, authorization)

    assert "provider_model_mismatch" in result["errors"]


def test_requested_gateway_alias_must_match_child_contract():
    expected = "c" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["requested_model"] = "unapproved-gateway-alias"

    result = _validate(receipt, expected, evidence, authorization)

    assert "approved_canary_contract_invalid" in result["errors"]


def test_gateway_alias_and_provider_model_are_bound_as_separate_identities():
    expected = "b" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "PASS_PAID_COST_EVIDENCE_BOUND"
    assert receipt["requested_model"] == authorization[2]["model"]
    assert receipt["model"] == authorization[2]["expected_provider_model"]
    assert receipt["requested_model"] != receipt["model"]


def test_paid_cost_receipt_rejects_child_route_outside_parent_allowance():
    expected = "f" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    authorization[2]["expected_provider_model"] = "unapproved-provider-model"
    child_bytes = json.dumps(authorization[2], indent=2).encode("utf-8")
    authorization[3] = hashlib.sha256(child_bytes).hexdigest()
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])

    result = _validate(receipt, expected, evidence, authorization)

    assert "approved_canary_contract_invalid" in result["errors"]


def test_child_contract_requires_expected_provider_model_identity():
    expected = "e" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    authorization[2]["expected_provider_model"] = " "
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])

    result = _validate(receipt, expected, evidence, authorization)

    assert "approved_canary_contract_invalid" in result["errors"]
    assert result["spend_cap_observed"] is False


def test_provider_export_model_must_match_approved_provider_identity():
    expected = "d" * 64
    evidence = _evidence()
    evidence["records"][0]["model"] = "unapproved-provider-model"
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["provider_evidence_sha256"] = _evidence_hash(evidence)

    result = _validate(receipt, expected, evidence, authorization)

    assert "provider_evidence_model_mismatch" in result["errors"]


def test_legacy_receipt_schema_is_rejected():
    expected = "0" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["schema"] = "wrench.paid-cost-receipt.v1"

    result = _validate(receipt, expected, evidence, authorization)

    assert "schema_invalid" in result["errors"]


def test_receipt_must_bind_exact_parent_and_child_contract_hashes():
    expected = "1" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["parent_contract_sha256"] = "2" * 64
    receipt["child_contract_sha256"] = "3" * 64

    result = _validate(receipt, expected, evidence, authorization)

    assert "parent_contract_hash_mismatch" in result["errors"]
    assert "child_contract_hash_mismatch" in result["errors"]


def test_zero_parent_budget_cannot_validate_a_paid_cost_receipt():
    expected = "4" * 64
    evidence = _evidence()
    authorization = _authorization(expected, parent_budget_usd=0)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "FAIL_PAID_COST_EVIDENCE_BOUND"
    assert "approved_canary_contract_invalid" in result["errors"]
    assert result["spend_cap_observed"] is False


def test_estimate_loopback_or_template_receipt_is_rejected():
    expected = "a" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt.update(source="configured_rate_estimate", paid_transaction_receipt=False, endpoint="http://localhost:4000/v1", template=True)

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "FAIL_PAID_COST_EVIDENCE_BOUND"
    assert "template_not_receipt" in result["errors"]
    assert "source_not_provider_export" in result["errors"]
    assert "paid_transaction_receipt_not_true" in result["errors"]
    assert "endpoint_must_be_https_non_loopback" in result["errors"]


def test_provider_export_must_match_request_ids_usage_and_cost():
    expected = "b" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    evidence["records"][1]["total_tokens"] = 999
    evidence["records"][1]["cost_usd"] = 3.0
    receipt["provider_evidence_sha256"] = _evidence_hash(evidence)

    result = _validate(receipt, expected, evidence, authorization)

    assert "provider_evidence_usage_mismatch" in result["errors"]
    assert "provider_evidence_cost_mismatch" in result["errors"]


def test_evidence_hash_and_client_answers_are_required():
    expected = "c" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["provider_evidence_sha256"] = "0" * 64
    receipt["clients"]["deepseek_harness"]["correct"] = False

    result = _validate(receipt, expected, evidence, authorization)

    assert "provider_evidence_hash_mismatch" in result["errors"]
    assert "client_answers_incomplete" in result["errors"]


def test_malformed_client_shape_and_nonfinite_cost_fail_closed():
    expected = "d" * 64
    evidence = _evidence()
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["cost_usd"] = float("nan")
    receipt["clients"]["opencode"] = None

    result = _validate(receipt, expected, evidence, authorization)

    assert "cost_invalid" in result["errors"]
    assert "client_answers_incomplete" in result["errors"]


def test_provider_export_template_is_rejected():
    expected = "e" * 64
    evidence = _evidence()
    evidence["template"] = True
    authorization = _authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])

    result = _validate(receipt, expected, evidence, authorization)

    assert "provider_evidence_template_not_export" in result["errors"]


def test_openai_daily_aggregate_requires_and_binds_isolated_child_scope():
    expected = "6" * 64
    evidence = _aggregate_evidence()
    authorization = _aggregate_authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["provider_evidence_sha256"] = _evidence_hash(evidence)

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "PASS_PAID_COST_EVIDENCE_BOUND"
    assert result["cost_binding_level"] == "isolated_project_key_daily_aggregate"
    assert result["aggregate_scope_assertions_consistent"] is True
    assert result["request_level_cost_attribution"] is False
    assert result["human_source_review_required"] is True


def test_openai_aggregate_rejects_unisolated_project_key_or_mismatched_child():
    expected = "7" * 64
    evidence = _aggregate_evidence()
    evidence["scope"]["project_id"] = "proj-shared"
    evidence["scope"]["exclusive_api_key"] = False
    evidence["export"]["data"][0]["results"][0]["project_id"] = "proj-unexpected"
    evidence["export_sha256"] = _evidence_hash(evidence["export"])
    authorization = _aggregate_authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["provider_evidence_sha256"] = _evidence_hash(evidence)

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "FAIL_PAID_COST_EVIDENCE_BOUND"
    assert "provider_evidence_aggregate_exclusive_api_key_not_confirmed" in result["errors"]
    assert "provider_evidence_aggregate_identity_mismatch" in result["errors"]
    assert any(error.startswith("approved_child_aggregate_binding_") for error in result["errors"])


def test_openai_aggregate_rejects_incomplete_pagination_and_cost_mismatch():
    expected = "8" * 64
    evidence = _aggregate_evidence()
    evidence["export"]["has_more"] = True
    evidence["export"]["next_page"] = "next"
    evidence["export"]["data"][0]["results"][0]["amount"]["value"] = 0.02
    evidence["export_sha256"] = _evidence_hash(evidence["export"])
    authorization = _aggregate_authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["provider_evidence_sha256"] = _evidence_hash(evidence)

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "FAIL_PAID_COST_EVIDENCE_BOUND"
    assert "provider_evidence_aggregate_export_incomplete" in result["errors"]
    assert "provider_evidence_aggregate_cost_mismatch" in result["errors"]


def test_openai_aggregate_rejects_unbound_daily_bucket_coverage():
    expected = "9" * 64
    evidence = _aggregate_evidence()
    evidence["export"]["data"][0]["end_time"] -= 1
    evidence["export_sha256"] = _evidence_hash(evidence["export"])
    authorization = _aggregate_authorization(expected)
    receipt = _valid_receipt(expected, evidence, authorization[1], authorization[3])
    receipt["provider_evidence_sha256"] = _evidence_hash(evidence)

    result = _validate(receipt, expected, evidence, authorization)

    assert result["status"] == "FAIL_PAID_COST_EVIDENCE_BOUND"
    assert "provider_evidence_aggregate_bucket_coverage_invalid" in result["errors"]


def test_workload_hash_requires_approved_one_case_manifest(tmp_path):
    workload = tmp_path / "workload.json"
    workload.write_text('{"schema":"wrench.paired-canary-workload.v1","workload_id":"x","authorization":"local_stub_only","cases":[]}', encoding="utf-8")

    try:
        workload_hash(workload)
    except ValueError as exc:
        assert str(exc) == "workload_authorization_invalid"
    else:
        raise AssertionError("unauthorized workload was accepted")
