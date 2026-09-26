"""Synthetic in-memory checks for mixed lifecycle ledger conversion."""

import json
import unittest

from tools.report_paired_frontier_savings import summarize
from wrench_harness.mixed_lifecycle_ledger_bridge import (
    LEDGER_SCHEMA,
    MAX_DOCUMENT_BYTES,
    LedgerError,
    bridge,
)


COMPARISON = {
    "protocol_id": "proto-synthetic-1",
    "client_id": "client-synthetic-1",
    "frontier_model_id": "model-synthetic-1",
    "token_convention_id": "frontier-token-counter-1",
}


def _usage(call_id, route, input_tokens, output_tokens, *, counter=None,
           status="exact", cost=7, cost_status="known"):
    if counter is None:
        counter = COMPARISON["token_convention_id"] if route == "frontier" else "local-token-counter-1"
    if status == "unknown":
        counter = input_tokens = output_tokens = None
    if cost_status == "unknown":
        cost = None
    return {
        "call_id": call_id,
        "route": route,
        "status": status,
        "counter_id": counter,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_status": cost_status,
        "cost_microunits": cost,
    }


def _arm(prefix, *, wrench=False, cost_status="known"):
    attempts = ([
        {"attempt_id": f"{prefix}-local", "route": "local", "result": "failed",
         "retry_of": None, "fallback": False, "call_made": True},
        {"attempt_id": f"{prefix}-frontier", "route": "frontier", "result": "success",
         "retry_of": f"{prefix}-local", "fallback": True, "call_made": True},
    ] if wrench else [
        {"attempt_id": f"{prefix}-frontier", "route": "frontier", "result": "success",
         "retry_of": None, "fallback": False, "call_made": True},
    ])
    verifier_route = "local" if wrench else "frontier"
    work_calls = [
        {"call_id": f"{prefix}-tool", "kind": "tool", "route": "none", "result": "success"},
        {"call_id": f"{prefix}-verifier", "kind": "verifier", "route": verifier_route, "result": "passed"},
    ]
    usage_rows = []
    for attempt in attempts:
        usage_rows.append(_usage(
            attempt["attempt_id"], attempt["route"],
            30 if attempt["route"] == "local" else 20,
            5 if attempt["route"] == "local" else 2,
            cost_status=cost_status,
        ))
    usage_rows.append(_usage(f"{prefix}-verifier", verifier_route, 8, 1,
                             cost_status=cost_status))
    return {
        "run_id": f"run-{prefix}",
        "session_id": f"session-{prefix}",
        "route": "mixed" if wrench else "frontier",
        "context_receipt_sha256": "b" * 64,
        "preparation_accounting_sha256": "d" * 64,
        "selected_evidence_ids": [],
        "omitted_evidence_ids": [],
        "retrieval_misses": [],
        "post_task_evidence_refs": [
            {"evidence_id": f"{prefix}-evidence", "kind": "test_result", "sha256": "c" * 64},
        ],
        "correction_refs": [],
        "verifier": {"identity": "verifier-1", "result": "passed", "evidence_ids": [f"{prefix}-evidence"]},
        "outcome": {"status": "completed", "provenance": "independently_verified", "evidence_ids": [f"{prefix}-evidence"]},
        "attempts": attempts,
        "work_calls": work_calls,
        "usage_rows": usage_rows,
    }


def _ledger(*, cost_status="known"):
    return {
        "schema": LEDGER_SCHEMA,
        "comparison": dict(COMPARISON),
        "tasks": [{
            "task_id": "task-synthetic-1",
            "snapshot_sha256": "a" * 64,
            "baseline": _arm("base", cost_status=cost_status),
            "wrench": _arm("wrench", wrench=True, cost_status=cost_status),
        }],
    }


class MixedLifecycleLedgerBridgeTests(unittest.TestCase):
    def test_mixed_retry_tool_verifier_usage_reconciles_and_reporter_counts_frontier_savings(self):
        converted = bridge(_ledger())
        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 1)
        self.assertEqual(report["successful_pair_count"], 0)
        self.assertIsNone(report["average_per_successful_task_savings_percent"])
        self.assertEqual(report["frontier_token_totals"], {"baseline": 31, "wrench": 22})
        self.assertEqual(report["average_per_task_savings_percent"], 29.032258)
        self.assertTrue(all(row["evidence_trust"] == "caller_supplied_untrusted" for row in converted.arm_audit))
        wrench_receipt = json.loads(converted.paired_input["tasks"][0]["wrench"]["receipt"]["payload_json"])
        self.assertEqual(wrench_receipt["schema"], "wrench.e0.outcome-receipt.v3")
        self.assertEqual(wrench_receipt["outcome"]["provenance"], "user_reported")
        audit = next(row for row in converted.arm_audit if row["arm"] == "wrench")
        self.assertIn("claimed_independent_verification_downgraded_untrusted", audit["reasons"])
        self.assertEqual(wrench_receipt["accounting"]["local_model_calls"], 2)
        self.assertEqual(wrench_receipt["accounting"]["frontier_model_calls"], 1)
        self.assertEqual(wrench_receipt["accounting"]["retries"], 1)
        self.assertEqual(wrench_receipt["accounting"]["fallback_calls"], 1)
        self.assertEqual(wrench_receipt["accounting"]["tool_calls"], 1)
        self.assertEqual(wrench_receipt["accounting"]["verifier_calls"], 1)

    def test_unknown_cost_keeps_exact_tokens_eligible(self):
        converted = bridge(_ledger(cost_status="unknown"))
        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 1)
        self.assertEqual(report["successful_pair_count"], 0)
        self.assertEqual(report["average_per_task_savings_percent"], 29.032258)
        self.assertEqual(report["cost_unknown_valid_pair_count"], 1)

    def test_missing_usage_taints_whole_arm_instead_of_partial_sum(self):
        ledger = _ledger()
        ledger["tasks"][0]["wrench"]["usage_rows"].pop()
        converted = bridge(ledger)
        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 0)
        self.assertIsNone(report["average_per_task_savings_percent"])
        receipt = json.loads(converted.paired_input["tasks"][0]["wrench"]["receipt"]["payload_json"])
        self.assertEqual(receipt["accounting"]["token_count_status"], "unknown")
        self.assertIsNone(receipt["accounting"]["frontier_tokens"])
        audit = next(row for row in converted.arm_audit if row["arm"] == "wrench")
        self.assertIn("missing_usage_row", audit["reasons"])

    def test_not_run_work_call_cannot_claim_model_route_or_usage(self):
        for route in ("local", "frontier"):
            with self.subTest(route=route):
                ledger = _ledger()
                work = ledger["tasks"][0]["wrench"]["work_calls"][0]
                work["route"] = route
                work["result"] = "not_run"
                with self.assertRaisesRegex(
                    LedgerError, "wrench_work_call_not_run_with_model_route"
                ):
                    bridge(ledger)

        ledger = _ledger()
        arm = ledger["tasks"][0]["wrench"]
        work = arm["work_calls"][0]
        work["route"] = "none"
        work["result"] = "not_run"
        arm["usage_rows"] = [row for row in arm["usage_rows"] if row["call_id"] != work["call_id"]]
        converted = bridge(ledger)
        receipt = json.loads(converted.paired_input["tasks"][0]["wrench"]["receipt"]["payload_json"])
        self.assertEqual(receipt["accounting"]["local_model_calls"], 2)
        self.assertEqual(receipt["accounting"]["frontier_model_calls"], 1)
        self.assertEqual(receipt["accounting"]["local_tokens"], 44)
        self.assertEqual(receipt["accounting"]["frontier_tokens"], 22)
        self.assertEqual(receipt["work_calls"][0]["result"], "not_run")
        self.assertEqual(receipt["work_calls"][0]["usage"]["status"], "not_applicable")

    def test_duplicate_unmatched_wrong_route_and_wrong_frontier_counter_taint_arm(self):
        for mutation, reason in (
            ("duplicate", "duplicate_usage_call_id"),
            ("unmatched", "unmatched_usage_call_id"),
            ("route", "usage_route_mismatch"),
            ("counter", "frontier_counter_mismatch"),
        ):
            with self.subTest(mutation=mutation):
                ledger = _ledger()
                rows = ledger["tasks"][0]["wrench"]["usage_rows"]
                if mutation == "duplicate":
                    rows.append(dict(rows[0]))
                elif mutation == "unmatched":
                    rows.append(dict(rows[0], call_id="ghost-call"))
                elif mutation == "route":
                    rows[0]["route"] = "frontier"
                else:
                    rows[1]["counter_id"] = "wrong-counter"
                converted = bridge(ledger)
                report = summarize(converted.paired_input)
                self.assertEqual(report["valid_pair_count"], 0)
                receipt = json.loads(converted.paired_input["tasks"][0]["wrench"]["receipt"]["payload_json"])
                self.assertEqual(receipt["accounting"]["token_count_status"], "unknown")
                audit = next(row for row in converted.arm_audit if row["arm"] == "wrench")
                self.assertIn(reason, audit["reasons"])

    def test_bad_comparison_and_duplicate_task_reject_document(self):
        malformed = _ledger()
        malformed["comparison"]["token_convention_id"] = "has spaces"
        with self.assertRaisesRegex(LedgerError, "comparison_token_convention_id_invalid"):
            bridge(malformed)
        duplicate = _ledger()
        duplicate["tasks"].append(dict(duplicate["tasks"][0]))
        with self.assertRaisesRegex(LedgerError, "duplicate_task_id"):
            bridge(duplicate)

    def test_oversized_input_is_rejected_before_serialization_and_unhashable_enum_is_typed_error(self):
        with self.assertRaisesRegex(LedgerError, "ledger_byte_limit_exceeded"):
            bridge({"schema": "x" * (MAX_DOCUMENT_BYTES + 1)})
        malformed = _ledger()
        malformed["tasks"][0]["wrench"]["route"] = []
        with self.assertRaisesRegex(LedgerError, "declared_route_invalid"):
            bridge(malformed)


if __name__ == "__main__":
    unittest.main()
