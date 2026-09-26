"""Focused in-memory mechanics tests for the config-draft synthetic screen."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_local_config_review_draft_screen_01 as screen


class FakeTranscript:
    def __init__(self, tokenizer, messages, resource_check=None):
        self.messages = messages
        self.prompt_tokens = 17
        self.completion_tokens = 5
        self.calls = []
        user = messages[-1]["content"]
        self.case = next(case for case in screen.validate_fixture(json.loads(screen.FIXTURE.read_text(encoding="utf-8")))[0].values()
                         if case["prompt"] == user)
        self.responses = [json.dumps({"name": "read_file", "arguments": {"path": path, "max_bytes": screen.MAX_READ_BYTES}})
                          for path in self.case["required_read_paths"]]
        self.responses.append(json.dumps(screen._expected_answer(self.case)))

    def generate(self, model, max_new_tokens):
        self.calls.append({"status": "completed"})
        return self.responses.pop(0)


class LocalConfigReviewDraftScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.digest = screen.load_fixture()

    def test_fixture_is_hash_pinned_and_balanced(self):
        self.assertEqual(self.digest, screen.EXPECTED_FIXTURE_SHA256)
        self.assertEqual(sum(c["class"] == "positive" for c in self.cases.values()), 6)
        self.assertEqual(sum(c["class"] == "boundary" for c in self.cases.values()), 6)

    def test_all_twelve_oracles_pass_with_actual_read_events(self):
        with patch.object(screen.base, "Transcript", FakeTranscript):
            for case in self.cases.values():
                with self.subTest(case=case["case_id"]):
                    result = screen.run_case(case, model=object(), tokenizer=object())
                    self.assertEqual(result["status"], "completed")
                    self.assertTrue(result["score"]["case_pass"])
                    self.assertEqual([event["arguments"]["path"] for event in result["tool_events"]],
                                     case["required_read_paths"])
                    if case["class"] == "positive":
                        self.assertTrue(result["score"]["evidence_grounded_in_actual_read"])

    def test_malformed_unknown_state_is_unresolved(self):
        case = self.cases["boundary-outside-root"]
        answer = dict(screen._expected_answer(case), status="unknown", reason="outside_root")
        score = screen._score(case, json.dumps(answer), [], [], {})
        self.assertFalse(score["valid_json_schema"])
        self.assertFalse(score["case_pass"])

    def test_python_network_connections_are_blocked(self):
        with self.assertRaisesRegex(RuntimeError, "local_screen_network_connections_disabled"):
            screen.socket.create_connection(("127.0.0.1", 4000), timeout=0.1)
        connection = screen.socket.socket()
        try:
            with self.assertRaisesRegex(RuntimeError, "local_screen_network_connections_disabled"):
                connection.connect(("127.0.0.1", 4000))
        finally:
            connection.close()

    def test_oracle_exact_answers_do_not_count_without_required_tool_flow(self):
        positive = self.cases["positive-relay-port"]
        positive_score = screen._score(
            positive, json.dumps(screen._expected_answer(positive)), [], [],
            dict(positive["_files_for_host"]),
        )
        self.assertTrue(positive_score["answer_exact"])
        self.assertFalse(positive_score["case_pass"])
        self.assertFalse(positive_score["accepted_draft"])

        boundary = self.cases["boundary-missing"]
        boundary_score = screen._score(
            boundary, json.dumps(screen._expected_answer(boundary)), [], [],
            dict(boundary["_files_for_host"]),
        )
        self.assertTrue(boundary_score["answer_exact"])
        self.assertFalse(boundary_score["case_pass"])
        self.assertFalse(boundary_score["correct_abstention"])

    def test_diff_is_in_memory_only_and_rejects_duplicate_lines(self):
        case = self.cases["positive-relay-port"]
        original = dict(case["_files_for_host"])
        answer = screen._expected_answer(case)
        changed, applied = screen.apply_draft_to_copy(original, answer)
        self.assertTrue(applied)
        self.assertNotEqual(changed, original)
        self.assertEqual(original, case["_files_for_host"])
        duplicate = {"config/relay.toml": "listen_port = 70000\nlisten_port = 70000\n"}
        self.assertFalse(screen.apply_draft_to_copy(duplicate, answer)[1])

if __name__ == "__main__":
    unittest.main()
