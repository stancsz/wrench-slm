from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from tools.capture_subroute_teacher_traces import capture
from tools.subroute_budget_guard import (
    BudgetError,
    BudgetLedger,
    CAMPAIGN_ID,
    SubRouteApproval,
    _git_head,
    caller_bundle_sha256,
    load_approval,
    request_reserve_microusd,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = REPO_ROOT / "tmp" / "wrench-subroute-budget-tests"


def make_approval(root: Path, *, job_id: str, maximum_requests: int = 2, cap_microusd: int | None = None) -> SubRouteApproval:
    call_root = root / "artifacts" / "wrench-gateway-model-research" / "subroute-calls"
    reserve = request_reserve_microusd(16_384, 128, "0.30", "1.20")
    return SubRouteApproval(
        approval_id="human-test-approval",
        job_id=job_id,
        approval_sha256="a" * 64,
        approved_head="b" * 40,
        endpoint="http://127.0.0.1:4000/v1/chat/completions",
        model_alias="openrouter",
        expected_upstream_model="minimax/minimax-m3",
        expected_provider="minimax",
        aggregate_cap_microusd=cap_microusd if cap_microusd is not None else reserve * maximum_requests,
        maximum_requests=maximum_requests,
        maximum_input_tokens=16_384,
        maximum_output_tokens=128,
        maximum_request_body_bytes=12_288,
        maximum_input_rate_usd_per_million_tokens=Decimal("0.30"),
        maximum_output_rate_usd_per_million_tokens=Decimal("1.20"),
        cases_path=root / "datasets" / "cases.jsonl",
        cases_sha256="c" * 64,
        ledger_path=call_root / f"{CAMPAIGN_ID}.sqlite",
        receipt_path=call_root / f"{job_id}.json",
        expires_at_utc=datetime.now(timezone.utc) + timedelta(hours=1),
    )


class RequestReserveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TEST_ROOT.mkdir(parents=True, exist_ok=True)

    def test_reserve_rounds_up_to_whole_microdollar(self) -> None:
        self.assertEqual(request_reserve_microusd(256, 128, "0.30", "1.20"), 231)

    def test_ledger_reconciles_actual_cost_and_keeps_unknown_full_reserve(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as temporary:
            root = Path(temporary)
            approval = make_approval(root, job_id="WRENCH-TEST-LEDGER-0001")
            ledger = BudgetLedger(approval, storage_root=root)
            reserve = approval.request_reserve_microusd

            request_id, amount = ledger.reserve("case-1", "1" * 64)
            self.assertEqual(amount, reserve)
            ledger.mark_dispatched(request_id)
            actual = ledger.settle(
                request_id,
                provider_name="MiniMax",
                response_model=approval.expected_upstream_model,
                generation_id="gen-test-1",
                prompt_tokens=100,
                completion_tokens=20,
                total_tokens=120,
                actual_cost_usd="0.0001001",
                usage={"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120, "cost": 0.0001001},
                safe_result={"id": "case-1", "normalized_proposal": None},
            )
            self.assertEqual(actual, 101)
            summary = ledger.summary()
            self.assertEqual(summary["settled_spend_microusd"], 101)
            self.assertEqual(summary["outstanding_reserve_microusd"], 0)
            self.assertEqual(ledger.settled_cases()["case-1"]["actual_microusd"], 101)

            second_id, _ = ledger.reserve("case-2", "2" * 64)
            ledger.mark_dispatched(second_id)
            ledger.mark_unknown(second_id, "transport_ambiguous")
            summary = ledger.summary()
            self.assertEqual(summary["outstanding_reserve_microusd"], reserve)
            with self.assertRaisesRegex(BudgetError, "unresolved_provider_call"):
                ledger.reserve("case-3", "3" * 64)

    def test_cumulative_exposure_cannot_exceed_aggregate_cap(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as temporary:
            root = Path(temporary)
            request_ceiling = request_reserve_microusd(16_384, 128, "0.30", "1.20")
            approval = make_approval(root, job_id="WRENCH-TEST-LEDGER-0002", cap_microusd=request_ceiling + 99)
            ledger = BudgetLedger(approval, storage_root=root)
            request_id, reserve = ledger.reserve("case-1", "1" * 64)
            self.assertEqual(reserve, request_ceiling)
            ledger.mark_dispatched(request_id)
            ledger.settle(
                request_id,
                provider_name="MiniMax",
                response_model=approval.expected_upstream_model,
                generation_id="gen-cap-test",
                prompt_tokens=10,
                completion_tokens=2,
                total_tokens=12,
                actual_cost_usd="0.0001",
                usage={"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12, "cost": "0.0001"},
                safe_result={"id": "case-1"},
            )
            with self.assertRaisesRegex(BudgetError, "aggregate_cap_would_be_exceeded"):
                ledger.reserve("case-2", "2" * 64)
            self.assertEqual(ledger.summary()["request_count"], 1)

    def test_ledger_identity_change_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as temporary:
            root = Path(temporary)
            approval = make_approval(root, job_id="WRENCH-TEST-LEDGER-0003")
            original = BudgetLedger(approval, storage_root=root)
            original.reserve("case-1", "1" * 64)
            changed = make_approval(root, job_id=approval.job_id)
            changed = SubRouteApproval(**{**changed.__dict__, "approval_sha256": "d" * 64})
            ledger = BudgetLedger(changed, storage_root=root)
            with self.assertRaisesRegex(BudgetError, "ledger_approval_identity_mismatch"):
                ledger.reserve("case-2", "2" * 64)

    def test_campaign_cap_is_shared_across_separate_approved_jobs(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as temporary:
            root = Path(temporary)
            reserve = request_reserve_microusd(16_384, 128, "0.30", "1.20")
            cap = reserve + 99
            first_approval = make_approval(
                root,
                job_id="WRENCH-TEST-CAMPAIGN-0001",
                maximum_requests=1,
                cap_microusd=cap,
            )
            first = BudgetLedger(first_approval, storage_root=root)
            request_id, _ = first.reserve("case-1", "1" * 64)
            first.mark_dispatched(request_id)
            first.settle(
                request_id,
                provider_name="MiniMax",
                response_model=first_approval.expected_upstream_model,
                generation_id="gen-campaign-test",
                prompt_tokens=10,
                completion_tokens=2,
                total_tokens=12,
                actual_cost_usd="0.0001",
                usage={"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12, "cost": "0.0001"},
                safe_result={"id": "case-1"},
            )

            second_approval = make_approval(
                root,
                job_id="WRENCH-TEST-CAMPAIGN-0002",
                maximum_requests=1,
                cap_microusd=cap,
            )
            second = BudgetLedger(second_approval, storage_root=root)
            with self.assertRaisesRegex(BudgetError, "aggregate_cap_would_be_exceeded"):
                second.reserve("case-2", "2" * 64)
            self.assertEqual(first.summary()["request_count"], 1)
            self.assertEqual(first.summary()["settled_spend_microusd"], 100)

            expanded_approval = make_approval(
                root,
                job_id="WRENCH-TEST-CAMPAIGN-0003",
                maximum_requests=1,
                cap_microusd=cap + reserve,
            )
            expanded = BudgetLedger(expanded_approval, storage_root=root)
            with self.assertRaisesRegex(BudgetError, "campaign_ledger_approval_identity_mismatch"):
                expanded.summary()


class SubRouteCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=TEST_ROOT)
        self.root = Path(self.temporary.name)
        self.data_root = self.root
        self.repo_root = REPO_ROOT
        self.job_id = "WRENCH-TEST-CAPTURE-0001"
        self.approvals_root = self.data_root / "artifacts" / "wrench-gateway-model-research" / "approvals"
        self.calls_root = self.data_root / "artifacts" / "wrench-gateway-model-research" / "subroute-calls"
        self.datasets_root = self.data_root / "datasets"
        self.approvals_root.mkdir(parents=True)
        self.datasets_root.mkdir(parents=True)
        self.cases_path = self.datasets_root / "cases.jsonl"
        case = {
            "id": "synthetic-1",
            "synthetic": True,
            "split": "dev",
            "system": "Return one bounded proposal.",
            "prompt": "synthetic input text",
        }
        self.cases_path.write_text(json.dumps(case, ensure_ascii=False) + "\n", encoding="utf-8")
        self.approval_path = self.approvals_root / f"{self.job_id}.json"
        self.approval = self._approval_payload()
        self.approval_path.write_text(json.dumps(self.approval, sort_keys=True), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _approval_payload(self) -> dict:
        return {
            "schema": "wrench.subroute-spend-approval.v1",
            "status": "APPROVED",
            "approved_by": "human",
            "approval_id": "test-owner-approval",
            "job_id": self.job_id,
            "approved_head": _git_head(self.repo_root),
            "issued_at_utc": datetime.now(timezone.utc).isoformat(),
            "expires_at_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "owner_authorization_ref": "test-only synthetic fixture",
            "data_scope": "wrench_authored_synthetic_only",
            "caller_bundle_sha256": caller_bundle_sha256(self.repo_root),
            "campaign_id": CAMPAIGN_ID,
            "endpoint": "http://127.0.0.1:4000/v1/chat/completions",
            "model_alias": "openrouter",
            "expected_upstream_model": "minimax/minimax-m3",
            "upstream_provider": "minimax",
            "aggregate_cap_usd": "0.01",
            "maximum_requests": 1,
            "maximum_input_tokens": 16_384,
            "maximum_output_tokens": 128,
            "maximum_request_body_bytes": 12_288,
            "maximum_input_rate_usd_per_million_tokens": "0.30",
            "maximum_output_rate_usd_per_million_tokens": "1.20",
            "cases_path": str(self.cases_path.resolve()),
            "cases_sha256": hashlib.sha256(self.cases_path.read_bytes()).hexdigest(),
            "ledger_path": str((self.calls_root / f"{CAMPAIGN_ID}.sqlite").resolve()),
            "receipt_path": str((self.calls_root / f"{self.job_id}.json").resolve()),
            "automatic_retries": 0,
            "allow_fallbacks": False,
        }

    def test_mock_provider_capture_records_cost_and_never_persists_prompt_or_raw_output(self) -> None:
        calls = []

        def mock_transport(request_body: bytes):
            calls.append(request_body)
            response = {
                "id": "chatcmpl-test",
                "model": "openrouter",
                "choices": [{"message": {"content": '{"schema":"wrench.proposal.v1","action":"read_file","path":"src/a.py","max_bytes":100,"raw_sentinel":"SYNTHETIC_RAW_ONLY_ABC"}'}}],
                "openrouter_metadata": {
                    "endpoints": {"available": [{"model": "minimax/minimax-m3", "provider": "MiniMax", "selected": True}]}
                },
                "usage": {"prompt_tokens": 40, "completion_tokens": 10, "total_tokens": 50, "cost": 0.0001},
            }
            return response, "gen-test-id", 12.5

        receipt = capture(
            self.approval_path,
            self.cases_path,
            data_root=self.data_root,
            repo_root=self.repo_root,
            transport=mock_transport,
        )
        self.assertEqual(len(calls), 1)
        body = json.loads(calls[0])
        self.assertEqual(body["model"], "openrouter")
        self.assertFalse(body["provider"]["allow_fallbacks"])
        self.assertEqual(body["provider"]["only"], ["minimax"])
        self.assertEqual(body["metadata"]["wrench_openrouter_provider_controls"], body["provider"])
        self.assertEqual(receipt["results"][0]["response_model"], "minimax/minimax-m3")
        self.assertEqual(receipt["results"][0]["provider"], "MiniMax")
        self.assertEqual(receipt["budget_ledger"]["settled_spend_microusd"], 100)
        saved = Path(self.approval["receipt_path"]).read_bytes()
        self.assertNotIn(b"synthetic input text", saved)
        self.assertNotIn(b"SYNTHETIC_RAW_ONLY_ABC", saved)
        self.assertIsNone(receipt["results"][0]["raw_model_output"])

    def test_missing_approval_fails_before_transport(self) -> None:
        called = False

        def mock_transport(_request_body: bytes):
            nonlocal called
            called = True
            raise AssertionError("transport must not be called without approval")

        with self.assertRaises(BudgetError):
            capture(
                self.approvals_root / "MISSING-APPROVAL-0001.json",
                self.cases_path,
                data_root=self.data_root,
                repo_root=self.repo_root,
                transport=mock_transport,
            )
        self.assertFalse(called)

    def test_missing_subroute_key_fails_before_ledger_or_transport(self) -> None:
        with patch.dict(os.environ, {"WRENCH_SUBROUTE_API_KEY": "", "GATEWAY_MASTER_KEY": ""}):
            with self.assertRaisesRegex(BudgetError, "subroute_auth_credential_unavailable"):
                capture(
                    self.approval_path,
                    self.cases_path,
                    data_root=self.data_root,
                    repo_root=self.repo_root,
                )
        self.assertFalse((self.calls_root / f"{CAMPAIGN_ID}.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
