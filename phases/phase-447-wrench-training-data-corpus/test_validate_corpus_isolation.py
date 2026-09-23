import importlib.util
from contextlib import redirect_stderr
import io
import tempfile
import sys
from unittest import mock
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("validate_corpus.py")
SPEC = importlib.util.spec_from_file_location("phase447_validate_corpus", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


def row(row_id, split, repository="repo-a", task_family="family-a", template="template-a"):
    return {
        "id": row_id,
        "split": split,
        "template_id": template,
        "provenance": {"repository_id": repository, "task_family_id": task_family},
    }


class IsolationTests(unittest.TestCase):
    def test_repository_cannot_cross_splits(self):
        errors = validator.isolation_errors([
            row("train-1", "train", repository="repo-shared"),
            row("dev-1", "development", repository="repo-shared", task_family="family-b", template="template-b"),
        ])
        self.assertTrue(any("repository isolation group" in error for error in errors))

    def test_underlying_task_family_cannot_cross_splits(self):
        errors = validator.isolation_errors([
            row("train-1", "train", repository="repo-a"),
            row("dev-1", "development", repository="repo-b", task_family="family-a", template="template-b"),
        ])
        self.assertTrue(any("task_family isolation group" in error for error in errors))

    def test_template_group_cannot_cross_splits(self):
        errors = validator.isolation_errors([
            row("train-1", "train", template="shared-template"),
            row("dev-1", "development", repository="repo-b", task_family="family-b", template="shared-template"),
        ])
        self.assertTrue(any("template group isolation" in error for error in errors))

    def test_missing_provenance_fails_closed(self):
        errors = validator.isolation_errors([row("train-1", "train", repository="", task_family="")])
        self.assertTrue(any("repository isolation ID is required" in error for error in errors))
        self.assertTrue(any("task_family isolation ID is required" in error for error in errors))

    def test_path_and_line_number_paraphrase_is_near_duplicate_across_splits(self):
        prompt_a = "Open src/main.py line 12 and show the function."
        prompt_b = "Open src/main.py line 18 and show the function."
        rows = [
            {"id": "train-1", "split": "train", "near_duplicate_signature": validator.near_duplicate_signature(prompt_a)},
            {"id": "dev-1", "split": "development", "near_duplicate_signature": validator.near_duplicate_signature(prompt_b)},
        ]
        errors = validator.near_duplicate_errors(rows)
        self.assertEqual(len(errors), 1)
        self.assertIn("near-duplicate model input across splits", errors[0])

    def test_dissimilar_prompts_are_not_flagged(self):
        prompts = ["Read the current branch status.", "Explain this unrelated cooking recipe."]
        rows = [
            {"id": f"row-{index}", "split": split, "near_duplicate_signature": validator.near_duplicate_signature(prompt)}
            for index, (split, prompt) in enumerate(zip(("train", "development"), prompts))
        ]
        self.assertEqual(validator.near_duplicate_errors(rows), [])

    def test_near_duplicate_candidate_work_is_capped_and_fails_closed(self):
        signature = validator.near_duplicate_signature("Read this file and return the requested lines.")
        rows = [
            {"id": f"row-{index}", "split": "train", "near_duplicate_signature": signature}
            for index in range(140)
        ]
        errors = validator.near_duplicate_errors(rows, max_hamming=-1)
        self.assertTrue(any("candidate limit exceeded" in error for error in errors))

    def test_candidate_schema_is_not_accepted_as_production_row(self):
        candidate = {
            "id": "candidate-1",
            "schema": "wrench.training-candidate.v1",
            "split": "review_quarantine",
            "allocation_stratum": "balanced_core",
            "category": "eligible",
            "family": "read_file",
            "template_id": "template-1",
            "system": "system",
            "prompt": "read file",
            "context_ref": "fixture",
            "context_sha256": "0" * 64,
            "expected_status": "accepted",
            "expected_proposal": {"action": "read_file"},
            "abstention_reason": None,
            "oracle_ref": "oracle-1",
            "oracle_sha256": "0" * 64,
            "provenance": {
                "kind": "verified_authored",
                "source_ref": "source-1",
                "source_sha256": "0" * 64,
                "authorization": "project_authored",
                "repository_id": "repo-a",
                "task_family_id": "family-a",
            },
            "review": {},
            "fingerprint_sha256": "0" * 64,
        }
        registries = {name: {} for name in ("sources", "contexts", "oracles", "reviews")}
        errors, _ = validator.validate_row(candidate, "train", 1, registries)
        self.assertIn("candidate-1: schema must be wrench.training-example.v1", errors)
        self.assertIn("candidate-1: split must be train", errors)

    def test_row_validation_requires_repo_and_task_family_provenance(self):
        candidate = {
            "id": "row-1",
            "schema": validator.SCHEMA,
            "split": "train",
            "allocation_stratum": "balanced_core",
            "category": "eligible",
            "family": "read_file",
            "template_id": "template-1",
            "system": "system",
            "prompt": "read file",
            "context_ref": "fixture",
            "context_sha256": "0" * 64,
            "expected_status": "accepted",
            "expected_proposal": {"action": "read_file"},
            "abstention_reason": None,
            "oracle_ref": "oracle-1",
            "oracle_sha256": "0" * 64,
            "provenance": {
                "kind": "verified_authored",
                "source_ref": "source-1",
                "source_sha256": "0" * 64,
                "authorization": "project_authored",
                "repository_id": "",
                "task_family_id": "",
            },
            "review": {},
            "fingerprint_sha256": validator.fingerprint("system", "read file"),
        }
        registries = {name: {} for name in ("sources", "contexts", "oracles", "reviews")}
        errors, _ = validator.validate_row(candidate, "train", 1, registries)
        self.assertIn("row-1: provenance.repository_id is required for split isolation", errors)
        self.assertIn("row-1: provenance.task_family_id is required for split isolation", errors)

    def test_isolation_provenance_must_match_approved_source_registry(self):
        candidate = {
            "id": "row-1",
            "schema": validator.SCHEMA,
            "split": "train",
            "allocation_stratum": "balanced_core",
            "category": "eligible",
            "family": "read_file",
            "template_id": "template-1",
            "system": "system",
            "prompt": "read file",
            "context_ref": "fixture",
            "context_sha256": "0" * 64,
            "expected_status": "accepted",
            "expected_proposal": {"action": "read_file"},
            "abstention_reason": None,
            "oracle_ref": "oracle-1",
            "oracle_sha256": "0" * 64,
            "provenance": {
                "kind": "verified_authored",
                "source_ref": "source-1",
                "source_sha256": "0" * 64,
                "authorization": "project_authored",
                "repository_id": "repo-a",
                "task_family_id": "family-a",
            },
            "review": {},
            "fingerprint_sha256": validator.fingerprint("system", "read file"),
        }
        registries = {
            "sources": {
                "source-1": {
                    "kind": "verified_authored",
                    "sha256": "0" * 64,
                    "authorization": "project_authored",
                    "repository_id": "repo-other",
                    "task_family_id": "family-a",
                    "status": "approved",
                }
            },
            "contexts": {},
            "oracles": {},
            "reviews": {},
        }
        errors, _ = validator.validate_row(candidate, "train", 1, registries)
        self.assertIn("row-1: provenance repository_id does not match the corpus manifest", errors)


class PathGuardTests(unittest.TestCase):
    def test_sealed_manifest_path_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "sealed-final-manifest.json"
            with mock.patch.object(sys, "argv", ["validate_corpus.py", "--manifest", str(manifest)]):
                with mock.patch.object(Path, "read_text", side_effect=AssertionError("must not read")):
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                        validator.main()
            self.assertEqual(raised.exception.code, 2)

    def test_ordinary_manifest_alias_to_sealed_target_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alias = root / "ordinary-manifest.json"
            sealed = root / "sealed" / "manifest.json"
            original_resolve = Path.resolve

            def resolve_with_alias(self, strict=False):
                if self == alias:
                    return sealed
                return original_resolve(self, strict=strict)

            with mock.patch.object(sys, "argv", ["validate_corpus.py", "--manifest", str(alias)]):
                with mock.patch.object(Path, "resolve", resolve_with_alias), mock.patch.object(
                    Path, "read_text", side_effect=AssertionError("must not read")
                ):
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                        validator.main()
            self.assertEqual(raised.exception.code, 2)

    def test_sealed_component_in_parent_path_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            sealed_dir = Path(directory) / "sealed-final-storage"
            sealed_dir.mkdir()
            candidate = sealed_dir / "train.jsonl"
            candidate.write_text("dummy only\n", encoding="utf-8")
            with mock.patch.object(Path, "open", side_effect=AssertionError("must not open")):
                errors, rows, digest = validator.validate_file(candidate, "train", None, {})
            self.assertTrue(any("refusing sealed" in error for error in errors))
            self.assertEqual(rows, [])
            self.assertEqual(digest, "")

    def test_resolved_symlink_alias_to_sealed_path_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sealed = root / "final.jsonl"
            sealed.write_text("dummy only\n", encoding="utf-8")
            alias = root / "ordinary-train.jsonl"
            original_resolve = Path.resolve

            def resolve_with_alias(self, strict=False):
                if self == alias:
                    return sealed
                return original_resolve(self, strict=strict)

            with mock.patch.object(Path, "resolve", resolve_with_alias), mock.patch.object(
                Path, "open", side_effect=AssertionError("must not open")
            ):
                errors, _, digest = validator.validate_file(alias, "train", None, {}, (sealed,))
            self.assertTrue(any("refusing sealed" in error for error in errors))
            self.assertEqual(digest, "")

    def test_report_path_aliases_input_lexically_and_through_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "train.jsonl"
            source.write_text("dummy only\n", encoding="utf-8")
            self.assertTrue(validator.report_path_conflicts(source, (source,)))
            link = root / "report-alias.json"
            original_resolve = Path.resolve

            def resolve_with_alias(self, strict=False):
                if self == link:
                    return source
                return original_resolve(self, strict=strict)

            with mock.patch.object(Path, "resolve", resolve_with_alias):
                self.assertTrue(validator.report_path_conflicts(link, (source,)))

    def test_report_path_detects_existing_hardlink_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "train.jsonl"
            report_alias = root / "report.json"
            source.write_text("dummy only\n", encoding="utf-8")
            try:
                report_alias.hardlink_to(source)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"hardlinks unavailable: {type(exc).__name__}")
            self.assertTrue(validator.report_path_conflicts(report_alias, (source,)))


class DiagnosticCapTests(unittest.TestCase):
    def test_pathological_row_errors_are_bounded_and_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ordinary-train.jsonl"
            path.write_text("not-json\n" * (validator.MAX_DIAGNOSTICS + 23), encoding="utf-8")
            errors, rows, digest = validator.validate_file(path, "train", None, {})
            self.assertEqual(len(errors), validator.MAX_DIAGNOSTICS)
            self.assertEqual(errors.suppressed, 23)
            self.assertEqual(rows, [])
            self.assertTrue(digest)

    def test_near_duplicate_errors_are_bounded_and_still_report_suppression(self):
        signature = validator.near_duplicate_signature("Read this file and return the requested lines.")
        rows = [
            {"id": f"row-{index}", "split": "train", "near_duplicate_signature": signature}
            for index in range(140)
        ]
        errors = validator.near_duplicate_errors(rows)
        self.assertEqual(len(errors), validator.MAX_DIAGNOSTICS)
        self.assertGreater(errors.suppressed, 0)
        collected = validator.BoundedErrors()
        collected.extend(errors)
        metadata = validator.diagnostic_metadata(collected)
        self.assertEqual(metadata["error_count"], len(errors) + errors.suppressed)
        self.assertEqual(metadata["diagnostics_suppressed"], metadata["error_count"] - 100)
        self.assertTrue(metadata["diagnostics_truncated"])


if __name__ == "__main__":
    unittest.main()
