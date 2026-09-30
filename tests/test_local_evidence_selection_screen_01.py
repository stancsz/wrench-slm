from __future__ import annotations

import copy
import json
import unittest

from tools.run_local_evidence_selection_screen_01 import (
    FIXTURE_PATH,
    ScreenError,
    score_output,
    selected_text_token_count,
    validate_fixture,
    validate_oracle_budgets,
)


ABSTENTION_REASONS = {
    "missing_required_source", "stale_source", "ambiguous_or_conflicting",
    "no_sufficient_evidence_or_budget",
}


class EvidenceSelectionFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = validate_fixture(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))

    def test_fixture_has_exact_case_mix_and_minimal_model_projection(self):
        cases = self.fixture["cases"]
        self.assertEqual(len(cases), 12)
        self.assertEqual(sum(case["kind"] == "positive" for case in cases), 8)
        self.assertEqual(sum(case["kind"] == "boundary" for case in cases), 4)
        for case in cases:
            self.assertEqual(set(case["model_input"]), {"query", "token_budget", "candidates"})
            self.assertNotIn("case_id", case["model_input"])
            self.assertNotIn("kind", case["model_input"])
            self.assertNotIn("oracle", case["model_input"])

    def test_fixture_source_snapshot_and_opaque_id_bindings_validate(self):
        mutated = copy.deepcopy(self.fixture)
        candidate = mutated["cases"][0]["model_input"]["candidates"][0]
        candidate["text"] += " changed"
        with self.assertRaisesRegex(ScreenError, "candidate_source_hash_mismatch"):
            validate_fixture(mutated)

    def test_exact_selection_is_order_insensitive_but_requires_reason_null(self):
        case = next(row for row in self.fixture["cases"] if row["kind"] == "positive" and len(row["oracle"]["evidence_ids"]) > 1)
        expected_ids = case["oracle"]["evidence_ids"]
        result = score_output(case, json.dumps({
            "decision": "select", "evidence_ids": list(reversed(expected_ids)), "reason": None,
        }))
        self.assertTrue(result["schema_valid"])
        self.assertTrue(result["exact_positive_selection"])
        self.assertTrue(result["no_unauthorized_evidence"])
        self.assertEqual(set(result), {
            "schema_valid", "exact_positive_selection", "correct_boundary_abstention",
            "no_unauthorized_evidence", "no_source_echo", "no_hidden_canary",
        })

    def test_extra_missing_duplicate_unknown_and_empty_ids_fail(self):
        case = next(row for row in self.fixture["cases"] if row["kind"] == "positive")
        expected = case["oracle"]["evidence_ids"]
        candidates = case["model_input"]["candidates"]
        extra_id = next((row["evidence_id"] for row in candidates if row["evidence_id"] not in expected), "unsupported-id")
        cases = [
            {"decision": "select", "evidence_ids": [], "reason": None},
            {"decision": "select", "evidence_ids": ["unknown"], "reason": None},
            {"decision": "select", "evidence_ids": expected + [extra_id], "reason": None},
            {"decision": "select", "evidence_ids": expected + expected, "reason": None},
            {"decision": "select", "evidence_ids": expected},
            {"decision": "select", "evidence_ids": expected, "reason": "extra"},
        ]
        for index, observed in enumerate(cases):
            with self.subTest(observed=observed):
                score = score_output(case, json.dumps(observed))
                self.assertFalse(score["exact_positive_selection"])
                if index == 0:
                    self.assertFalse(score["schema_valid"])

    def test_abstention_requires_empty_ids_exact_reason_and_three_keys(self):
        case = next(row for row in self.fixture["cases"] if row["kind"] == "boundary")
        expected_reason = case["oracle"]["reason"]
        result = score_output(case, json.dumps({
            "decision": "abstain", "evidence_ids": [], "reason": expected_reason,
        }))
        self.assertTrue(result["correct_boundary_abstention"])
        wrong_reason = next(reason for reason in ABSTENTION_REASONS if reason != expected_reason)
        for observed in (
            {"decision": "abstain", "evidence_ids": [], "reason": wrong_reason},
            {"decision": "abstain", "evidence_ids": ["ev-x"], "reason": expected_reason},
            {"decision": "abstain", "reason": expected_reason},
            {"decision": "abstain", "evidence_ids": [], "reason": expected_reason, "extra": True},
        ):
            with self.subTest(observed=observed):
                score = score_output(case, json.dumps(observed))
                self.assertFalse(score["correct_boundary_abstention"])

    def test_malformed_json_source_echo_and_private_canary_fail_closed(self):
        case = next(row for row in self.fixture["cases"] if row["kind"] == "positive")
        candidate_text = case["model_input"]["candidates"][0]["text"]
        self.assertFalse(score_output(case, "not json")["schema_valid"])
        self.assertFalse(score_output(case, json.dumps({
            "decision": "select", "evidence_ids": case["oracle"]["evidence_ids"], "reason": None,
        }) + candidate_text)["no_source_echo"])
        canary = "PRIVATE-CANARY-9bd7d3"
        boundary = next(row for row in self.fixture["cases"] if row["kind"] == "boundary")
        echo = json.dumps({
            "decision": "abstain", "evidence_ids": [], "reason": boundary["oracle"]["reason"],
        }) + canary
        result = score_output(boundary, echo, canary)
        self.assertFalse(result["no_hidden_canary"])
        self.assertFalse(result["schema_valid"])

    def test_selected_text_token_budget_is_checked_with_supplied_tokenizer(self):
        class ByteTokenizer:
            def __call__(self, text: str, *, add_special_tokens: bool):
                return {"input_ids": list(text.encode("utf-8"))}

        case = copy.deepcopy(next(row for row in self.fixture["cases"] if row["kind"] == "positive"))
        ids = case["oracle"]["evidence_ids"]
        count = selected_text_token_count(case, ids, ByteTokenizer())
        candidate_by_id = {row["evidence_id"]: row for row in case["model_input"]["candidates"]}
        expected = sum(len(candidate_by_id[item]["text"].encode("utf-8")) for item in ids)
        self.assertEqual(count, expected)
        case["model_input"]["token_budget"] = count - 1
        with self.assertRaisesRegex(ScreenError, "oracle_selection_exceeds_local_token_budget"):
            validate_oracle_budgets({"cases": [case]}, ByteTokenizer())


if __name__ == "__main__":
    unittest.main()
