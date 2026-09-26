from __future__ import annotations

import unittest
from types import SimpleNamespace

from tools.run_local_context_integration_screen_01 import ScreenError, _check_expected


class ContextIntegrationOracleTests(unittest.TestCase):
    def test_exact_expected_statuses_and_incomplete_outcome_are_checked(self):
        result = SimpleNamespace(
            status=SimpleNamespace(value="source_misses"),
            route="none",
            reason=None,
            prompt=None,
            prompt_gate=None,
            retrieval_misses=(("miss-1", "stale"),),
            outcome_receipt=SimpleNamespace(
                status=SimpleNamespace(value="incomplete"),
                receipt=SimpleNamespace(payload_json='{"outcome":{"status":"unknown"}}'),
            ),
            sources=(),
            selected_evidence_ids=(),
            omitted_evidence=(),
        )
        observed = _check_expected(result, {
            "case_id": "stale",
            "expected": {
                "status": "source_misses",
                "route": "none",
                "prompt_present": False,
                "prompt_gate_status": None,
                "retrieval_miss_statuses": ["stale"],
                "outcome_receipt_status": "incomplete",
            },
        }, "0" * 64)
        self.assertEqual(observed["retrieval_miss_statuses"], ["stale"])

    def test_oracle_mismatch_fails_closed(self):
        result = SimpleNamespace(
            status=SimpleNamespace(value="ready"),
            route="none",
            reason=None,
            prompt="{}",
            prompt_gate=SimpleNamespace(status=SimpleNamespace(value="ready"), prompt_sha256="0" * 64, exact_token_count=2),
            retrieval_misses=(),
            outcome_receipt=None,
            sources=(),
            selected_evidence_ids=(),
            omitted_evidence=(),
        )
        with self.assertRaisesRegex(ScreenError, "oracle_mismatch:status"):
            _check_expected(result, {
                "case_id": "wrong",
                "expected": {"status": "prompt_rejected"},
            }, "0" * 64)


if __name__ == "__main__":
    unittest.main()
