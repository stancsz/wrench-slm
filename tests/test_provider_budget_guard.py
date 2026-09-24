from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch
import os

from tools import capture_minimax_teacher_traces
from tools import provider_budget_guard
from tools.provider_budget_guard import (
    CHILD_SCHEMA,
    admit,
    debit_attempt,
    sha256,
    _canonical_json,
)


ROOT = Path(__file__).resolve().parents[1]
APPROVAL = ROOT / "phases/phase-447-wrench-training-data-corpus/minimax-data-approval.json"


def _receipt(approval_path: Path, cases: Path, source_path: Path, output_path: Path) -> dict:
    raw_approval = approval_path.read_bytes()
    receipt = {
        "schema": CHILD_SCHEMA,
        "approval_sha256": sha256(raw_approval),
        "cases_canonical_sha256": sha256(cases.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")),
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": "minimax/minimax-m3",
        "provider": "minimax",
        "allow_fallbacks": False,
        "workers": 1,
        "maximum_requests": 1,
        "maximum_input_tokens": 256,
        "maximum_output_tokens": 128,
        "immutable_maximum_rates_usd_per_million_tokens": {
            "model": "minimax/minimax-m3",
            "input": "1.00",
            "output": "1.00",
            "source_reference": "owner-supplied immutable rate card",
            "source_path": str(source_path.resolve()),
            "source_sha256": sha256(source_path.read_bytes()),
        },
        "maximum_request_reserve_usd": "0.000384",
        "cumulative_reserve_usd": "0.000384",
        "output_path": str(output_path.resolve()),
    }
    receipt["task_hash"] = sha256(_canonical_json(receipt))
    return receipt


class ProviderBudgetGuardTests(unittest.TestCase):
  def setUp(self) -> None:
    self.data_root_temp = tempfile.TemporaryDirectory()
    self.addCleanup(self.data_root_temp.cleanup)
    self.data_root = Path(self.data_root_temp.name) / "wrench-slm-data"
    (self.data_root / "artifacts").mkdir(parents=True)
    (self.data_root / "datasets").mkdir(parents=True)
    self.output = self.data_root / "artifacts" / "pilot.json"
    self.rate_source = self.data_root / "pricing.json"
    self.rate_source.write_text(json.dumps({"model": "minimax/minimax-m3", "input": "1.00", "output": "1.00"}), encoding="utf-8")
    self.data_root_patch = patch.object(provider_budget_guard, "DATA_ROOT", self.data_root.resolve())
    self.data_root_patch.start()
    self.addCleanup(self.data_root_patch.stop)

  def test_admission_requires_hash_bound_approval_cases_and_reconciliation(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      cases = tmp_path / "cases.jsonl"
      cases.write_text('{"id":"synthetic-1","prompt":"safe fixture"}\n', encoding="utf-8")
      child = tmp_path / "child.json"
      child.write_text(json.dumps(_receipt(APPROVAL, cases, self.rate_source, self.output)), encoding="utf-8")

      admitted = admit(
          APPROVAL, child, cases,
          endpoint="https://openrouter.ai/api/v1/chat/completions",
          model="minimax/minimax-m3", max_tokens=128, workers=1,
          prior_spend_usd="0", prior_charge_status="RECONCILED_NOT_CHARGED",
          reconciliation_reference="billing receipt checked by owner",
          remaining_cap_usd="100",
          output_path=self.output,
      )
      self.assertEqual(admitted["maximum_requests"], 1)
      self.assertEqual(admitted["cumulative_reserve_usd"], "0.000384")

      with self.assertRaisesRegex(ValueError, "UNKNOWN"):
          admit(
              APPROVAL, child, cases,
              endpoint="https://openrouter.ai/api/v1/chat/completions",
              model="minimax/minimax-m3", max_tokens=128, workers=1,
              prior_spend_usd="0", prior_charge_status="UNKNOWN",
              reconciliation_reference="unresolved 401", remaining_cap_usd="100",
              output_path=self.output,
          )


  def test_admission_rejects_case_mutation(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      cases = tmp_path / "cases.jsonl"
      cases.write_text('{"id":"synthetic-1"}\n', encoding="utf-8")
      child = tmp_path / "child.json"
      receipt = _receipt(APPROVAL, cases, self.rate_source, self.output)
      receipt["task_hash"] = sha256(_canonical_json({k: v for k, v in receipt.items() if k != "task_hash"}))
      child.write_text(json.dumps(receipt), encoding="utf-8")
      cases.write_text('{"id":"changed"}\n', encoding="utf-8")
      with self.assertRaisesRegex(ValueError, "cases_canonical_sha256"):
          admit(
              APPROVAL, child, cases,
              endpoint="https://openrouter.ai/api/v1/chat/completions",
              model="minimax/minimax-m3", max_tokens=128, workers=1,
              prior_spend_usd="0", prior_charge_status="RECONCILED_NOT_CHARGED",
              reconciliation_reference="checked", remaining_cap_usd="100",
              output_path=self.output,
          )

  def test_admission_rejects_mutated_pricing_source_and_wrong_output(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      cases = tmp_path / "cases.jsonl"
      cases.write_text('{"id":"synthetic-1"}\n', encoding="utf-8")
      receipt = _receipt(APPROVAL, cases, self.rate_source, self.output)
      child = tmp_path / "child.json"
      child.write_text(json.dumps(receipt), encoding="utf-8")
      self.rate_source.write_text(json.dumps({"model": "minimax/minimax-m3", "input": "9", "output": "9"}), encoding="utf-8")
      with self.assertRaisesRegex(ValueError, "SHA-256"):
          admit(
              APPROVAL, child, cases, endpoint="https://openrouter.ai/api/v1/chat/completions",
              model="minimax/minimax-m3", max_tokens=128, workers=1,
              prior_spend_usd="0", prior_charge_status="RECONCILED_NOT_CHARGED",
              reconciliation_reference="checked", remaining_cap_usd="100", output_path=self.output,
          )
      self.rate_source.write_text(json.dumps({"model": "minimax/minimax-m3", "input": "1.00", "output": "1.00"}), encoding="utf-8")
      receipt = _receipt(APPROVAL, cases, self.rate_source, self.output)
      receipt["task_hash"] = sha256(_canonical_json({k: v for k, v in receipt.items() if k != "task_hash"}))
      child.write_text(json.dumps(receipt), encoding="utf-8")
      with self.assertRaisesRegex(ValueError, "output_path"):
          admit(
              APPROVAL, child, cases, endpoint="https://openrouter.ai/api/v1/chat/completions",
              model="minimax/minimax-m3", max_tokens=128, workers=1,
              prior_spend_usd="0", prior_charge_status="RECONCILED_NOT_CHARGED",
              reconciliation_reference="checked", remaining_cap_usd="100",
              output_path=self.data_root / "artifacts" / "different.json",
          )


  def test_attempt_without_usage_debits_full_request_reserve(self) -> None:
    self.assertEqual(debit_attempt("0.25", None), "0.25")
    self.assertEqual(debit_attempt("0.25", "0.10"), "0.10")
    with self.assertRaisesRegex(ValueError, "exceeds"):
        debit_attempt("0.25", "0.26")

  def test_unknown_charge_rejects_before_any_post(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      cases = tmp_path / "cases.jsonl"
      cases.write_text('{"id":"synthetic-1","prompt":"fixture"}\n', encoding="utf-8")
      child = tmp_path / "child.json"
      child.write_text(json.dumps(_receipt(APPROVAL, cases, self.rate_source, self.output)), encoding="utf-8")
      args = Namespace(
          approval=APPROVAL, child_receipt=child, cases=cases,
          endpoint="https://openrouter.ai/api/v1/chat/completions",
          model="minimax/minimax-m3", max_tokens=128, workers=1,
          prior_spend_usd="0", prior_charge_status="UNKNOWN",
          reconciliation_reference="unresolved prior 401", remaining_cap_usd="100",
          output=self.output,
          limit=None, auth_env=None, timeout=1,
      )
      with patch.object(capture_minimax_teacher_traces.urllib.request, "urlopen") as post:
          with self.assertRaisesRegex(ValueError, "UNKNOWN"):
              capture_minimax_teacher_traces.capture(args)
          post.assert_not_called()

  def test_mocked_post_is_provider_pinned_and_retains_only_normalized_data(self) -> None:
    class Response:
      def __enter__(self):
        return self
      def __exit__(self, *_args):
        return False
      def __iter__(self):
        yield b'data: {"model":"minimax/minimax-m3","choices":[{"delta":{"content":"{\\"schema\\":\\"wrench.proposal.v1\\",\\"action\\":\\"read_file\\",\\"path\\":\\"a.py\\",\\"max_bytes\\":10}"}}]}\n'
        yield b'data: {"usage":{"prompt_tokens":10,"completion_tokens":4,"cost":0.000014}}\n'
        yield b'data: [DONE]\n'

    row = {"id": "must-not-persist", "prompt": "a synthetic prompt"}
    with patch.object(capture_minimax_teacher_traces.urllib.request, "urlopen", return_value=Response()) as post:
      result = capture_minimax_teacher_traces._request(
          "https://openrouter.ai/api/v1/chat/completions", "minimax/minimax-m3", row,
          1, 128, "0.001", 5000, "1", "2", None,
      )
    sent = json.loads(post.call_args.args[0].data.decode("utf-8"))
    self.assertEqual(sent["provider"]["only"], ["minimax"])
    self.assertIs(sent["provider"]["allow_fallbacks"], False)
    self.assertIs(sent["provider"]["enforce_distillable_text"], True)
    self.assertEqual(sent["provider"]["data_collection"], "deny")
    self.assertEqual(sent["provider"]["max_price"], {"prompt": 1.0, "completion": 2.0})
    self.assertNotIn("must-not-persist", json.dumps(result))
    self.assertNotIn("raw_model_output", result)
    self.assertIn("response_content_sha256", result)

  def test_missing_auth_rejects_before_any_post(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      cases = tmp_path / "cases.jsonl"
      cases.write_text('{"id":"synthetic-1","synthetic":true,"prompt":"fixture"}\n', encoding="utf-8")
      child = tmp_path / "child.json"
      child.write_text(json.dumps(_receipt(APPROVAL, cases, self.rate_source, self.output)), encoding="utf-8")
      args = Namespace(
          approval=APPROVAL, child_receipt=child, cases=cases,
          endpoint="https://openrouter.ai/api/v1/chat/completions",
          model="minimax/minimax-m3", max_tokens=128, workers=1,
          prior_spend_usd="0", prior_charge_status="RECONCILED_NOT_CHARGED",
          reconciliation_reference="billing receipt reconciled", remaining_cap_usd="100",
          output=self.output, limit=None, auth_env="OPENROUTER_API_KEY", timeout=1,
      )
      with patch.dict(os.environ, {}, clear=True):
        with patch.object(capture_minimax_teacher_traces.urllib.request, "urlopen") as post:
          with self.assertRaisesRegex(ValueError, "empty"):
              capture_minimax_teacher_traces.capture(args)
          post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
