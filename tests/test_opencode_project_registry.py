import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from wrench_harness.opencode_project_registry import (
    ExactTokenGateStatus,
    MAX_PROJECTS,
    OpenCodeProjectRegistry,
    POLICY_ID,
    ProjectRegistryError,
    SCHEMA,
    _reject_reparse_or_wrong_type,
)
from wrench_harness.e0_context_pipeline import MAX_SOURCE_BYTES


class OpenCodeProjectRegistryTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory(prefix=f"{self._testMethodName}-")
        self.tmp_path = Path(self._temporary.name)

    def tearDown(self):
        self._temporary.cleanup()

    def _enroll(self, *, project_id="prj_alpha", root_name="repo", paths=None):
        data_root = self.tmp_path / "wrench-data"
        data_root.mkdir(exist_ok=True)
        source_root = self.tmp_path / root_name
        source_root.mkdir(exist_ok=True)
        registry = OpenCodeProjectRegistry(data_root)
        project = registry.enroll_project(
            project_id,
            source_root,
            paths or ("src/main.py", "tests/test_main.py"),
        )
        return registry, project, source_root, data_root

    @staticmethod
    def _record(session_id: str, root: Path, **overrides):
        record = {"id": session_id, "location": {"directory": str(root)}}
        record.update(overrides)
        return record

    @staticmethod
    def _profile_document(project):
        return {
            "project_id": project.project_id,
            "configured_root": os.fspath(project.binding.configured_root),
            "root_location_sha256": project.binding.root_location_sha256,
            "root_identity": project.binding.root_identity,
            "source_paths": list(project.source_paths),
            "exclusions": list(project.exclusions),
            "policy_id": project.policy_id,
            "max_file_bytes": project.max_file_bytes,
            "max_total_bytes": project.max_total_bytes,
        }

    def test_registry_is_written_only_by_explicit_enrollment_and_store_is_derived(self):
        data_root = self.tmp_path / "wrench-data"
        data_root.mkdir()
        root = self.tmp_path / "repo"
        root.mkdir()
        registry = OpenCodeProjectRegistry(data_root)
        self.assertFalse(registry.registry_path.exists())
        self.assertEqual(registry.list_projects(), ())

        enrolled = registry.enroll_project("prj_alpha", root, ("src/main.py",))

        self.assertTrue(registry.registry_path.is_file())
        self.assertEqual(enrolled.project_id, "prj_alpha")
        self.assertEqual(
            enrolled.store_path,
            data_root / "artifacts" / "opencode-projects" / "prj_alpha",
        )
        self.assertTrue(enrolled.store_path.is_relative_to(data_root))
        self.assertFalse(enrolled.store_path.exists())
        self.assertIs(enrolled.exact_token_gate, ExactTokenGateStatus.UNAVAILABLE)
        self.assertEqual(enrolled.policy_id, POLICY_ID)
        self.assertNotIn(os.fspath(root), repr(enrolled))
        self.assertNotIn("src/main.py", repr(enrolled))

    def test_resolves_only_matching_event_session_and_enrolled_root(self):
        registry, project, root, _ = self._enroll()
        resolved = registry.resolve_session(
            "ses_fixture123", self._record("ses_fixture123", root)
        )
        self.assertEqual(resolved.project_id, project.project_id)
        self.assertEqual(resolved.session_id, "ses_fixture123")
        self.assertEqual(resolved.binding.root_identity, project.binding.root_identity)
        self.assertEqual(resolved.source_paths, ("src/main.py", "tests/test_main.py"))
        self.assertIs(resolved.exact_token_gate, ExactTokenGateStatus.UNAVAILABLE)

    def test_rejects_session_record_id_mismatch(self):
        registry, _, root, _ = self._enroll()
        with self.assertRaisesRegex(ProjectRegistryError, "session_id_mismatch"):
            registry.resolve_session("ses_event123", self._record("ses_other123", root))

    def test_rejects_nonempty_or_ambiguous_session_subpath(self):
        registry, _, root, _ = self._enroll()
        for subpath in ("src", "..", None, 7):
            with self.subTest(subpath=subpath):
                with self.assertRaisesRegex(ProjectRegistryError, "ambiguous_session_subpath"):
                    registry.resolve_session(
                        "ses_fixture123",
                        self._record("ses_fixture123", root, subpath=subpath),
                    )

    def test_rejects_unenrolled_root(self):
        registry, _, _, _ = self._enroll()
        other_root = self.tmp_path / "other"
        other_root.mkdir()
        with self.assertRaisesRegex(ProjectRegistryError, "enrolled_root_match_not_unique"):
            registry.resolve_session(
                "ses_fixture123", self._record("ses_fixture123", other_root)
            )

    def test_rejects_root_replaced_after_enrollment(self):
        registry, _, root, _ = self._enroll()
        retired = self.tmp_path / "repo-old"
        root.rename(retired)
        root.mkdir()
        with self.assertRaisesRegex(ProjectRegistryError, "enrolled_root_replaced"):
            registry.resolve_session("ses_fixture123", self._record("ses_fixture123", root))

    def test_rejects_reparse_data_root_when_supported(self):
        data_root = self.tmp_path / "wrench-data"
        data_root.mkdir()
        with patch("wrench_harness.snapshot._has_reparse_attribute", return_value=True):
            with self.assertRaisesRegex(ProjectRegistryError, "data_root_unusable"):
                OpenCodeProjectRegistry(data_root)

    def test_rejects_reparse_registry_file(self):
        path = self.tmp_path / "entry"
        fake = SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
        with patch.object(Path, "lstat", return_value=fake):
            with self.assertRaisesRegex(ProjectRegistryError, "registry_path_unsafe"):
                _reject_reparse_or_wrong_type(path, want_directory=False)

    def test_rejects_reparse_opencode_parent_before_registry_read(self):
        registry, _, _, _ = self._enroll()
        target = registry.registry_path.parent
        original_lstat = Path.lstat

        def fake_lstat(path, *args, **kwargs):
            if path == target:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
            return original_lstat(path, *args, **kwargs)

        with patch.object(Path, "lstat", fake_lstat):
            with self.assertRaisesRegex(ProjectRegistryError, "registry_path_unsafe"):
                registry.list_projects()

    def test_rejects_reparse_artifacts_ancestor_before_returning_store_path(self):
        registry, _, root, data_root = self._enroll()
        artifacts = data_root / "artifacts"
        artifacts.mkdir()
        original_lstat = Path.lstat

        def fake_lstat(path, *args, **kwargs):
            if path == artifacts:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
            return original_lstat(path, *args, **kwargs)

        with patch.object(Path, "lstat", fake_lstat):
            with self.assertRaisesRegex(ProjectRegistryError, "registry_path_unsafe"):
                registry.resolve_session(
                    "ses_fixture123", self._record("ses_fixture123", root)
                )

    def test_rejects_reparse_project_store_ancestor(self):
        registry, _, root, data_root = self._enroll()
        artifacts = data_root / "artifacts"
        project_stores = artifacts / "opencode-projects"
        project_stores.mkdir(parents=True)
        original_lstat = Path.lstat

        def fake_lstat(path, *args, **kwargs):
            if path == project_stores:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
            return original_lstat(path, *args, **kwargs)

        with patch.object(Path, "lstat", fake_lstat):
            with self.assertRaisesRegex(ProjectRegistryError, "registry_path_unsafe"):
                registry.resolve_session(
                    "ses_fixture123", self._record("ses_fixture123", root)
                )

    def test_failed_atomic_replace_preserves_previous_registry(self):
        registry, _, root, _ = self._enroll()
        second_root = self.tmp_path / "second-repo"
        second_root.mkdir()

        with patch("wrench_harness.opencode_project_registry.os.replace", side_effect=OSError("synthetic replace failure")):
            with self.assertRaisesRegex(ProjectRegistryError, "registry_write_failed"):
                registry.enroll_project("prj_beta", second_root, ("src/beta.py",))

        projects = registry.list_projects()
        self.assertEqual([item.project_id for item in projects], ["prj_alpha"])
        self.assertEqual(
            registry.resolve_session(
                "ses_fixture123", self._record("ses_fixture123", root)
            ).project_id,
            "prj_alpha",
        )
        self.assertEqual(list(registry.registry_path.parent.glob(".projects-*.tmp")), [])

    def test_rejects_malformed_registry_documents(self):
        cases = (
            (b'{"schema":"wrong","projects":[]}', "registry_schema_unsupported"),
            (b'{"schema":"wrench.opencode-project-registry.v1","projects":[],"extra":1}', "registry_fields_invalid"),
            (b'{"schema":"wrench.opencode-project-registry.v1","schema":"wrench.opencode-project-registry.v1","projects":[]}', "duplicate_json_field"),
            (b'{"schema":"wrench.opencode-project-registry.v1","projects":[', "registry_invalid"),
        )
        for raw, code in cases:
            with self.subTest(code=code):
                data_root = self.tmp_path / f"data-{code}"
                data_root.mkdir()
                root = self.tmp_path / f"repo-{code}"
                root.mkdir()
                registry = OpenCodeProjectRegistry(data_root)
                registry.enroll_project("prj_alpha", root, ("src/main.py",))
                registry.registry_path.write_bytes(raw)
                with self.assertRaisesRegex(ProjectRegistryError, code):
                    registry.list_projects()

    def test_rejects_unknown_profile_fields(self):
        registry, project, _, _ = self._enroll()
        row = self._profile_document(project)
        row["implicit_cwd"] = True
        registry.registry_path.write_text(
            json.dumps({"schema": SCHEMA, "projects": [row]}), encoding="utf-8"
        )
        with self.assertRaisesRegex(ProjectRegistryError, "profile_fields_invalid"):
            registry.list_projects()

    def test_rejects_duplicate_profiles_in_persisted_registry(self):
        registry, project, _, _ = self._enroll()
        row = self._profile_document(project)
        registry.registry_path.write_text(
            json.dumps({"schema": SCHEMA, "projects": [row, row]}), encoding="utf-8"
        )
        with self.assertRaisesRegex(ProjectRegistryError, "duplicate_project_id"):
            registry.list_projects()

    def test_rejects_duplicate_enrollment_id_or_root(self):
        registry, _, root, _ = self._enroll()
        with self.assertRaisesRegex(ProjectRegistryError, "project_id_already_enrolled"):
            registry.enroll_project("prj_alpha", root, ("src/main.py",))
        with self.assertRaisesRegex(ProjectRegistryError, "root_already_enrolled"):
            registry.enroll_project("prj_beta", Path(os.fspath(root).upper()), ("src/main.py",))

    def test_rejects_persisted_distinct_ids_with_path_alias_roots(self):
        registry, project, _, _ = self._enroll()
        alias = self._profile_document(project)
        alias["project_id"] = "prj_beta"
        alias["configured_root"] = alias["configured_root"].upper()
        registry.registry_path.write_text(
            json.dumps({"schema": SCHEMA, "projects": [self._profile_document(project), alias]}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ProjectRegistryError, "duplicate_enrolled_root"):
            registry.list_projects()

    def test_rejects_path_policy_and_cap_violations(self):
        cases = (
            ((), {}, "source_paths_limit_exceeded"),
            (("../secret.txt",), {}, "source_paths_invalid"),
            (("C:/secret.txt",), {}, "source_paths_invalid"),
            (("src/a.py", "src/./a.py"), {}, "source_paths_duplicate"),
            (("src/a.py",), {"policy_id": "auto-discover"}, "policy_id_unsupported"),
            (("src/a.py",), {"max_file_bytes": MAX_SOURCE_BYTES + 1}, "byte_cap_invalid"),
            (("src/a.py",), {"max_total_bytes": MAX_SOURCE_BYTES * 16}, "byte_cap_invalid"),
            (("src/a.py",), {"max_file_bytes": 20, "max_total_bytes": 10}, "byte_cap_invalid"),
            (("src/private/key.txt",), {"exclusions": ("src/private",)}, "source_path_excluded"),
            ((f"src/{'x' * 1025}.py",), {}, "source_paths_invalid"),
        )
        for index, (paths, kwargs, code) in enumerate(cases):
            with self.subTest(code=code):
                data_root = self.tmp_path / f"data-{index}"
                data_root.mkdir()
                root = self.tmp_path / f"repo-{index}"
                root.mkdir()
                registry = OpenCodeProjectRegistry(data_root)
                with self.assertRaisesRegex(ProjectRegistryError, code):
                    registry.enroll_project("prj_alpha", root, paths, **kwargs)
                self.assertFalse(registry.registry_path.exists())

    def test_enforces_finite_path_count_and_profile_count(self):
        data_root = self.tmp_path / "wrench-data"
        data_root.mkdir()
        root = self.tmp_path / "repo"
        root.mkdir()
        registry = OpenCodeProjectRegistry(data_root)
        with self.assertRaisesRegex(ProjectRegistryError, "source_paths_limit_exceeded"):
            registry.enroll_project("prj_alpha", root, tuple(f"f{i}.py" for i in range(17)))
        for index in range(MAX_PROJECTS):
            project_root = self.tmp_path / f"repo-{index}"
            project_root.mkdir()
            registry.enroll_project(f"prj_{index:02d}", project_root, ("src/main.py",))
        extra_root = self.tmp_path / "repo-extra"
        extra_root.mkdir()
        with self.assertRaisesRegex(ProjectRegistryError, "project_limit_exceeded"):
            registry.enroll_project("prj_extra", extra_root, ("src/main.py",))

    def test_profile_round_trip_and_revalidation_after_reload(self):
        registry, project, root, data_root = self._enroll()
        reopened = OpenCodeProjectRegistry(data_root)
        loaded = reopened.resolve_session(
            "ses_fixture123", self._record("ses_fixture123", root)
        )
        self.assertEqual(loaded.project_id, project.project_id)
        self.assertEqual(loaded.binding, project.binding)
        self.assertEqual(loaded.store_path, project.store_path)


if __name__ == "__main__":
    unittest.main()
