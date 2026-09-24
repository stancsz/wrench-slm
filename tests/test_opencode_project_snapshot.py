import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wrench_harness.opencode_project_registry import (
    ExactTokenGateStatus,
    OpenCodeProjectRegistry,
    ProjectRegistryError,
)
from wrench_harness.opencode_project_snapshot import (
    OpenCodeProjectSnapshot,
    ProjectSnapshotError,
    ProjectSnapshotStatus,
    prepare_opencode_project_snapshot,
)
from wrench_harness.snapshot import (
    SnapshotAdmissionError,
    SourceRootBinding,
    SourceSnapshot,
)


TEST_TMP_ROOT = Path(
    r"C:\wrench-slm-data\tmp\W2-NS-E0-ENROLLED-SNAPSHOT-20260924"
)


class OpenCodeProjectSnapshotTests(unittest.TestCase):
    def setUp(self):
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(
            prefix=f"{self._testMethodName}-", dir=TEST_TMP_ROOT
        )
        self.tmp_path = Path(self._temporary.name)
        self.data_root = self.tmp_path / "wrench-data"
        self.data_root.mkdir()
        self.source_root = self.tmp_path / "repo"
        self.source_root.mkdir()
        self.registry = OpenCodeProjectRegistry(self.data_root)

    def tearDown(self):
        self._temporary.cleanup()

    @staticmethod
    def _record(session_id, root, **overrides):
        record = {"id": session_id, "location": {"directory": str(root)}}
        record.update(overrides)
        return record

    def _enroll(self, paths=("src/main.py", "README.md"), *, file_cap=64 * 1024, total_cap=512 * 1024):
        for path in paths:
            target = self.source_root.joinpath(*path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"synthetic")
        return self.registry.enroll_project(
            "prj_fixture",
            self.source_root,
            paths,
            max_file_bytes=file_cap,
            max_total_bytes=total_cap,
        )

    def _prepare(self, paths=("src/main.py",)):
        return prepare_opencode_project_snapshot(
            self.registry,
            "ses_fixture123",
            self._record("ses_fixture123", self.source_root),
            paths,
        )

    def test_returns_bound_snapshot_input_only_and_does_not_persist(self):
        enrolled = self._enroll()
        result = self._prepare(("src/main.py", "README.md"))

        self.assertIsInstance(result, OpenCodeProjectSnapshot)
        self.assertIs(result.status, ProjectSnapshotStatus.SNAPSHOT_INPUT_READY)
        self.assertEqual(result.project_id, enrolled.project_id)
        self.assertEqual(result.session_id, "ses_fixture123")
        self.assertEqual(result.binding, enrolled.binding)
        self.assertIsInstance(result.binding, SourceRootBinding)
        self.assertIsInstance(result.snapshot, SourceSnapshot)
        self.assertEqual(result.snapshot.root_identity, enrolled.binding.root_identity)
        self.assertEqual(result.selected_paths, ("README.md", "src/main.py"))
        self.assertIs(result.exact_token_gate, ExactTokenGateStatus.UNAVAILABLE)
        self.assertNotIn("synthetic", repr(result))
        self.assertFalse(enrolled.store_path.exists())
        self.assertEqual(set(path.name for path in self.data_root.iterdir()), {"opencode"})

    def test_rejects_event_record_session_and_subpath_mismatch(self):
        self._enroll()
        cases = (
            ("ses_event123", self._record("ses_other123", self.source_root)),
            ("ses_fixture123", self._record("ses_fixture123", self.source_root, subpath="src")),
        )
        for event_id, record in cases:
            with self.subTest(event=event_id, record=record):
                with self.assertRaises((ProjectRegistryError, ProjectSnapshotError)):
                    prepare_opencode_project_snapshot(
                        self.registry, event_id, record, ("src/main.py",)
                    )

    def test_rejects_replaced_enrolled_root(self):
        self._enroll()
        retired = self.tmp_path / "repo-old"
        self.source_root.rename(retired)
        self.source_root.mkdir()
        with self.assertRaisesRegex(ProjectSnapshotError, "enrolled_root_replaced"):
            self._prepare(("src/main.py",))

    def test_rejects_invalid_containers_empty_and_unenrolled_paths_before_read(self):
        self._enroll()
        bad_inputs = (
            "src/main.py",
            self.source_root / "src" / "main.py",
            (),
            ("src/../README.md",),
            ("not-enrolled.py",),
            ("src/main.py", "src/./main.py"),
            ("src/main.py", "src/main.py"),
        )
        with patch("wrench_harness.opencode_project_snapshot.create_snapshot") as reader:
            for paths in bad_inputs:
                with self.subTest(paths=paths):
                    with self.assertRaises(ProjectSnapshotError):
                        self._prepare(paths)
            reader.assert_not_called()

    def test_rejects_overlong_or_nonfinite_selection_after_bounded_consumption(self):
        self._enroll(paths=("a.py",))
        consumed = []

        def endless():
            while True:
                consumed.append(len(consumed))
                yield "a.py"

        with self.assertRaisesRegex(ProjectSnapshotError, "selected_path_count_limit_exceeded"):
            self._prepare(endless())
        self.assertEqual(len(consumed), 2)

    def test_enforces_tighter_per_file_cap_during_secure_read(self):
        self._enroll(paths=("src/main.py",), file_cap=4, total_cap=8)
        with self.assertRaisesRegex(ProjectSnapshotError, "source_size_limit_exceeded"):
            self._prepare(("src/main.py",))

    def test_enforces_tighter_aggregate_cap_during_secure_read(self):
        self._enroll(paths=("a.py", "b.py"), file_cap=8, total_cap=12)
        for path in ("a.py", "b.py"):
            (self.source_root / path).write_bytes(b"1234567")
        with self.assertRaisesRegex(ProjectSnapshotError, "snapshot_size_limit_exceeded"):
            self._prepare(("a.py", "b.py"))

    def test_rejects_invalid_root_and_source_change_fail_closed(self):
        self._enroll()
        outside = self.tmp_path / "other"
        outside.mkdir()
        with self.assertRaisesRegex(ProjectSnapshotError, "enrolled_root_match_not_unique"):
            prepare_opencode_project_snapshot(
                self.registry,
                "ses_fixture123",
                self._record("ses_fixture123", outside),
                ("src/main.py",),
            )
        for failure in ("source_changed_during_read", "reparse_point_forbidden"):
            with self.subTest(failure=failure):
                with patch(
                    "wrench_harness.snapshot._read_stable_source",
                    side_effect=SnapshotAdmissionError(failure),
                ):
                    with self.assertRaisesRegex(ProjectSnapshotError, failure):
                        self._prepare(("src/main.py",))

    def test_profile_caps_above_global_snapshot_limits_are_rejected_by_registry(self):
        self.source_root.joinpath("src").mkdir()
        (self.source_root / "src" / "main.py").write_bytes(b"x")
        with self.assertRaises(ProjectRegistryError):
            self.registry.enroll_project(
                "prj_fixture",
                self.source_root,
                ("src/main.py",),
                max_file_bytes=256 * 1024,
                max_total_bytes=4 * 1024 * 1024,
            )


if __name__ == "__main__":
    unittest.main()
