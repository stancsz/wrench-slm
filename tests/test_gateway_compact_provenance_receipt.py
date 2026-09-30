from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from examples.gateway_context_mvp import run_demo as demo
from examples.gateway_context_mvp.run_paired_local_context_baseline import (
    CASES,
    _canonical_sha256,
    build_compact_provenance_receipt,
    load_answer_blind_path_manifest,
)


def _context() -> dict[str, object]:
    selected_ids = ["segment-alpha", "segment-beta"]
    source_receipt: dict[str, object] = {
        "schema": "wrench.selected-segment-source-references.v1",
        "snapshot_sha256": "a" * 64,
        "selected_segment_ids": selected_ids,
        "references": [
            {"segment_id": "segment-alpha", "source_path": "src/a.py"},
            {"segment_id": "segment-beta", "source_path": "src/b.py"},
        ],
    }
    source_receipt["receipt_sha256"] = _canonical_sha256(source_receipt)
    return {
        "compact_label_to_segment_id": {"E1": "segment-alpha", "E2": "segment-beta"},
        "selected_source_references": source_receipt,
    }


class CompactProvenanceReceiptTests(unittest.TestCase):
    def test_binds_labels_sources_and_rendered_prompt(self) -> None:
        receipt = build_compact_provenance_receipt(_context(), "<chat>exact rendered prompt")

        self.assertEqual(receipt["compact_label_to_segment_id"], {
            "E1": "segment-alpha",
            "E2": "segment-beta",
        })
        self.assertEqual(receipt["selected_source_references"]["selected_segment_ids"], [
            "segment-alpha",
            "segment-beta",
        ])
        self.assertTrue(receipt["rendered_prompt_sha256"])
        self.assertTrue(receipt["source_reference_receipt_sha256"])
        self.assertTrue(receipt["provenance_binding_sha256"])

    def test_binding_changes_with_rendered_prompt(self) -> None:
        context = _context()

        first = build_compact_provenance_receipt(context, "prompt one")
        second = build_compact_provenance_receipt(context, "prompt two")

        self.assertNotEqual(first["provenance_binding_sha256"], second["provenance_binding_sha256"])

    def test_rejects_reordered_or_swapped_sidecars(self) -> None:
        reordered = _context()
        reordered["compact_label_to_segment_id"] = {
            "E1": "segment-beta",
            "E2": "segment-alpha",
        }
        with self.assertRaisesRegex(ValueError, "compact_label_mapping_mismatch"):
            build_compact_provenance_receipt(reordered, "prompt")

        swapped = _context()
        source_receipt = copy.deepcopy(swapped["selected_source_references"])
        source_receipt["references"].reverse()
        swapped["selected_source_references"] = source_receipt
        with self.assertRaisesRegex(ValueError, "compact_source_reference_order_mismatch"):
            build_compact_provenance_receipt(swapped, "prompt")

    def test_rejects_modified_source_receipt_digest(self) -> None:
        changed = _context()
        source_receipt = copy.deepcopy(changed["selected_source_references"])
        source_receipt["references"][0]["source_path"] = "src/other.py"
        changed["selected_source_references"] = source_receipt

        with self.assertRaisesRegex(ValueError, "compact_source_reference_digest_mismatch"):
            build_compact_provenance_receipt(changed, "prompt")

    def test_path_manifest_binds_requests_and_fixture_without_answer_labels(self) -> None:
        manifest = {
            "schema": "wrench.answer-blind-source-path-manifest.v1",
            "fixture_sha256": hashlib.sha256(
                demo._canonical_json(demo.FIXTURE_FILES).encode("utf-8")
            ).hexdigest(),
            "cases": {
                case_id: {
                    "request_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
                    "source_paths": [
                        "src/retry.py" if case_id == "retry-function" else "config/service.toml"
                    ],
                    "annotation_basis": "request_and_repository_path_review_before_this_run",
                }
                for case_id, question, _ in CASES
            },
        }
        payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with patch.object(Path, "read_bytes", return_value=payload):
            paths, digest = load_answer_blind_path_manifest("in-memory.json")

        self.assertEqual(paths["retry-function"], ("src/retry.py",))
        self.assertEqual(paths["retry-policy"], ("config/service.toml",))
        self.assertEqual(digest, hashlib.sha256(payload).hexdigest())

    def test_path_manifest_rejects_answer_fields_and_stale_requests(self) -> None:
        manifest = {
            "schema": "wrench.answer-blind-source-path-manifest.v1",
            "fixture_sha256": hashlib.sha256(
                demo._canonical_json(demo.FIXTURE_FILES).encode("utf-8")
            ).hexdigest(),
            "cases": {
                case_id: {
                    "request_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
                    "source_paths": [
                        "src/retry.py" if case_id == "retry-function" else "config/service.toml"
                    ],
                    "annotation_basis": "request_and_repository_path_review_before_this_run",
                }
                for case_id, question, _ in CASES
            },
        }
        bad_answer = copy.deepcopy(manifest)
        bad_answer["cases"]["retry-function"]["expected_answer"] = "should_not_exist"
        payload = json.dumps(bad_answer).encode("utf-8")
        with patch.object(Path, "read_bytes", return_value=payload):
            with self.assertRaisesRegex(ValueError, "answer_blind_path_manifest_entry_invalid"):
                load_answer_blind_path_manifest("in-memory.json")

        bad_request = copy.deepcopy(manifest)
        bad_request["cases"]["retry-function"]["request_sha256"] = "0" * 64
        payload = json.dumps(bad_request).encode("utf-8")
        with patch.object(Path, "read_bytes", return_value=payload):
            with self.assertRaisesRegex(ValueError, "answer_blind_path_manifest_request_mismatch"):
                load_answer_blind_path_manifest("in-memory.json")


if __name__ == "__main__":
    unittest.main()
