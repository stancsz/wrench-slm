"""Offline synthetic checks for frontier usage ledger conversion."""

import hashlib
import json
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from wrench_harness.frontier_attempt_ledger_bridge import (
    LEDGER_SCHEMA,
    MAX_DOCUMENT_BYTES,
    LedgerError,
    bridge,
    main,
)
from tools.report_paired_frontier_savings import summarize


COMPARISON = {
    "protocol_id": "proto-synthetic-1",
    "client_id": "client-synthetic-1",
    "frontier_model_id": "model-synthetic-1",
    "token_convention_id": "tokens-synthetic-1",
}


class _ReadProbe(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.requested_size = None

    def read(self, size=-1):
        self.requested_size = size
        return super().read(size)


def _arm(prefix, counts, *, outcome="completed"):
    attempts = []
    usage_rows = []
    for index, (input_tokens, output_tokens) in enumerate(counts, start=1):
        attempt_id = f"{prefix}-call-{index}"
        attempts.append({
            "attempt_id": attempt_id,
            "route": "frontier",
            "result": "failed" if outcome == "failed" and index == len(counts) else "success",
            "retry_of": f"{prefix}-call-{index - 1}" if index > 1 else None,
            "fallback": False,
        })
        usage_rows.append({
            "call_id": attempt_id, "status": "exact",
            "counter_id": COMPARISON["token_convention_id"],
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "cost_status": "known", "cost_microunits": input_tokens + output_tokens,
        })
    return {
        "route": "frontier",
        "local_model_calls": 0,
        "tool_calls": 0,
        "verifier_calls": 0,
        "run_id": f"run-{prefix}",
        "context_receipt_sha256": "b" * 64,
        "outcome_status": outcome,
        "attempts": attempts,
        "usage_rows": usage_rows,
    }


def _ledger(*, baseline=((90, 10),), wrench=((40, 10),), outcome="completed"):
    return {
        "schema": LEDGER_SCHEMA,
        "comparison": dict(COMPARISON),
        "tasks": [{
            "task_id": "task-synthetic-1",
            "snapshot_sha256": "a" * 64,
            "baseline": _arm("base", baseline, outcome=outcome),
            "wrench": _arm("wrench", wrench, outcome=outcome),
        }],
    }


class AttemptLedgerBridgeTests(unittest.TestCase):
    def test_exact_per_attempt_ledger_builds_receipts_reporter_accepts_and_keeps_failed_outcomes(self):
        converted = bridge(_ledger(
            baseline=((90, 10), (30, 10)),
            wrench=((40, 10),),
            outcome="failed",
        ))
        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 1)
        self.assertEqual(report["frontier_token_totals"], {"baseline": 140, "wrench": 50})
        self.assertEqual(report["average_per_task_savings_percent"], 64.285714)
        self.assertEqual(report["task_outcome_counts_by_arm"], {
            "baseline": {"failed": 1}, "wrench": {"failed": 1},
        })
        self.assertTrue(all(row["status"] == "complete" for row in converted.arm_audit))

    def test_missing_duplicate_and_unmatched_usage_are_excluded(self):
        mutations = ("missing", "duplicate", "unmatched")
        expected = ("missing_usage_row", "duplicate_usage_call_id", "unmatched_usage_call_id")
        for mutation, reason in zip(mutations, expected):
            with self.subTest(mutation=mutation):
                ledger = _ledger(baseline=((90, 10),), wrench=((40, 10), (8, 2)))
                wrench = ledger["tasks"][0]["wrench"]
                if mutation == "missing":
                    wrench["usage_rows"].pop()
                elif mutation == "duplicate":
                    wrench["usage_rows"].append(dict(wrench["usage_rows"][0]))
                else:
                    extra = dict(wrench["usage_rows"][0], call_id="unmatched-call")
                    wrench["usage_rows"].append(extra)
                converted = bridge(ledger)
                report = summarize(converted.paired_input)
                self.assertEqual(report["valid_pair_count"], 0)
                self.assertIsNone(report["average_per_task_savings_percent"])
                self.assertEqual(report["excluded_by_reason"], {"incomplete_receipt": 1})
                audit = next(row for row in converted.arm_audit if row["arm"] == "wrench")
                self.assertEqual(audit["reasons"], reason)

    def test_nonexact_or_wrong_convention_usage_is_excluded(self):
        ledger = _ledger()
        ledger["tasks"][0]["wrench"]["usage_rows"][0]["counter_id"] = "wrong-tokenizer"
        converted = bridge(ledger)
        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 0)
        self.assertEqual(report["excluded_by_reason"], {"incomplete_receipt": 1})
        audit = next(row for row in converted.arm_audit if row["arm"] == "wrench")
        self.assertIn("non_exact_or_mismatched_usage", audit["reasons"])

    def test_exact_tokens_remain_eligible_when_cost_is_unknown(self):
        ledger = _ledger(wrench=((40, 10), (5, 1)))
        unknown_cost_usage = ledger["tasks"][0]["wrench"]["usage_rows"][0]
        unknown_cost_usage["cost_status"] = "unknown"
        unknown_cost_usage["cost_microunits"] = None
        converted = bridge(ledger)
        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 1)
        self.assertEqual(report["cost_unknown_valid_pair_count"], 1)
        self.assertEqual(report["frontier_token_totals"], {"baseline": 100, "wrench": 56})
        self.assertEqual(report["average_per_task_savings_percent"], 44.0)
        arm = converted.paired_input["tasks"][0]["wrench"]
        receipt = json.loads(arm["receipt"]["payload_json"])
        self.assertEqual(receipt["completeness"], "incomplete")
        self.assertEqual(receipt["missing_fields"], ["costs"])
        self.assertEqual(receipt["accounting"]["token_count_status"], "exact")
        self.assertEqual(receipt["accounting"]["cost_status"], "unknown")
        audit = next(row for row in converted.arm_audit if row["arm"] == "wrench")
        self.assertEqual(audit["status"], "token_complete_cost_unknown")
        self.assertEqual(audit["reasons"], "cost_unknown")

    def test_missing_cost_fields_fail_closed(self):
        ledger = _ledger()
        del ledger["tasks"][0]["wrench"]["usage_rows"][0]["cost_status"]
        converted = bridge(ledger)
        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 0)
        self.assertEqual(report["excluded_by_reason"], {"incomplete_receipt": 1})

    def test_cost_known_receipt_cannot_claim_cost_only_incompleteness(self):
        converted = bridge(_ledger())
        arm = converted.paired_input["tasks"][0]["wrench"]
        receipt = arm["receipt"]
        payload = json.loads(receipt["payload_json"])
        payload["completeness"] = "incomplete"
        payload["missing_fields"] = ["costs"]
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        receipt["payload_json"] = canonical
        receipt["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        report = summarize(converted.paired_input)
        self.assertEqual(report["valid_pair_count"], 0)
        self.assertEqual(report["excluded_by_reason"], {"incomplete_receipt": 1})

    def test_duplicate_task_identity_rejects_document(self):
        ledger = _ledger()
        ledger["tasks"].append(json.loads(json.dumps(ledger["tasks"][0])))
        with self.assertRaisesRegex(LedgerError, "duplicate_task_id"):
            bridge(ledger)

    def test_each_nonfrontier_call_category_must_be_explicit_zero(self):
        for category in ("local_model_calls", "tool_calls", "verifier_calls"):
            with self.subTest(category=category, value=1):
                ledger = _ledger()
                ledger["tasks"][0]["wrench"][category] = 1
                with self.assertRaisesRegex(LedgerError, f"wrench_{category}_must_be_explicit_zero"):
                    bridge(ledger)
            with self.subTest(category=category, value="omitted"):
                ledger = _ledger()
                del ledger["tasks"][0]["wrench"][category]
                with self.assertRaisesRegex(LedgerError, "wrench_arm_shape_invalid"):
                    bridge(ledger)

    def test_frontier_only_route_fallback_and_attempt_status_are_enforced(self):
        cases = (
            ("arm route", "route", "mixed", "wrench_route_must_be_frontier_only"),
            ("attempt route", "attempt_route", "local", "wrench_attempt_route_must_be_frontier_only"),
            ("fallback", "fallback", True, "wrench_fallback_unsupported"),
            ("not run", "result", "not_run", "wrench_attempt_result_invalid"),
        )
        for label, field, value, reason in cases:
            with self.subTest(label=label):
                ledger = _ledger()
                arm = ledger["tasks"][0]["wrench"]
                if field == "attempt_route":
                    arm["attempts"][0]["route"] = value
                elif field in {"fallback", "result"}:
                    arm["attempts"][0][field] = value
                else:
                    arm[field] = value
                with self.assertRaisesRegex(LedgerError, reason):
                    bridge(ledger)

    def test_unknown_outcome_status_is_rejected_at_bridge_boundary(self):
        ledger = _ledger()
        ledger["tasks"][0]["wrench"]["outcome_status"] = "unknown"
        with self.assertRaisesRegex(LedgerError, "wrench_outcome_status_invalid"):
            bridge(ledger)

    def test_cli_keeps_reporter_json_on_stdout_and_bounded_arm_audit_on_stderr(self):
        ledger = _ledger()
        ledger["tasks"][0]["wrench"]["usage_rows"].pop()
        stdout, stderr = io.StringIO(), io.StringIO()
        probe = _ReadProbe(json.dumps(ledger).encode("utf-8"))
        with patch.object(Path, "open", return_value=probe):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main(["synthetic-ledger.json"])
        paired_input = json.loads(stdout.getvalue())
        audit_lines = stderr.getvalue().splitlines()
        self.assertEqual(status, 0)
        self.assertEqual(paired_input["schema"], "wrench.paired-frontier-savings-input.v1")
        self.assertEqual(len(audit_lines), 1)
        audit = json.loads(audit_lines[0])
        self.assertEqual(audit["schema"], "wrench.frontier-attempt-ledger-bridge-audit.v1")
        wrench = next(row for row in audit["arms"] if row["arm"] == "wrench")
        self.assertEqual(wrench["reasons"], "missing_usage_row")
        self.assertEqual(probe.requested_size, MAX_DOCUMENT_BYTES + 1)

    def test_cli_oversized_input_reads_only_the_limit_plus_one(self):
        probe = _ReadProbe(b"x" * (MAX_DOCUMENT_BYTES + 100))
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(Path, "open", return_value=probe):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main(["oversized-ledger.json"])
        error = json.loads(stdout.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(error["error"], "ledger_byte_limit_exceeded")
        self.assertEqual(probe.requested_size, MAX_DOCUMENT_BYTES + 1)
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
