from __future__ import annotations

import argparse
import contextlib
import io
import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from tools import check_wrench_storage_budget as budget


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "tmp" / "wrench-storage-budget-tests"


class StorageBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            SCRATCH_ROOT.rmdir()
        except OSError:
            pass

    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(dir=SCRATCH_ROOT)
        self.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name)

    def write_reservation(
        self,
        storage: Path,
        job_id: str,
        included_roots: list[Path],
        *,
        filename: str | None = None,
        required_roots: list[Path] | None = None,
        optional_cache_roots: list[Path] | None = None,
    ) -> Path:
        directory = budget.reservation_dir(storage)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (filename or f"{job_id}.json")
        record = {
                "schema": budget.SCHEMA,
                "job_id": job_id,
                "reserve_bytes": 1,
                "included_roots": [str(root.resolve()) for root in included_roots],
            }
        if required_roots is not None:
            record["required_roots"] = [str(root.resolve()) for root in required_roots]
        if optional_cache_roots is not None:
            record["optional_cache_roots"] = [str(root.resolve()) for root in optional_cache_roots]
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def test_existing_reservation_roots_are_in_later_inventory(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        previously_included = self.root / "prior-external-root"
        repo.mkdir()
        storage.mkdir()
        previously_included.mkdir()
        (previously_included / "payload.bin").write_bytes(b"count me")
        self.write_reservation(storage, "prior-job", [previously_included])

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            roots = budget.inventory_roots(repo, storage, [])

        self.assertIn(previously_included.resolve(), roots)
        self.assertEqual(budget.directory_bytes(previously_included), (8, []))

    def test_missing_root_from_existing_reservation_blocks_inventory(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        missing = self.root / "prior-external-root"
        repo.mkdir()
        storage.mkdir()
        self.write_reservation(storage, "prior-job", [missing])

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            with self.assertRaisesRegex(FileNotFoundError, "prior-external-root"):
                budget.inventory_roots(repo, storage, [])

    def test_legacy_missing_default_cache_root_is_omitted_as_optional(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        missing_cache = self.root / "legacy-cache"
        repo.mkdir()
        storage.mkdir()
        self.write_reservation(storage, "prior-job", [missing_cache])

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[missing_cache]
        ):
            roots = budget.inventory_roots(repo, storage, [])

        self.assertNotIn(missing_cache.resolve(), roots)

    def test_new_record_keeps_persisted_cache_optional_after_candidate_changes(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        formerly_optional_cache = self.root / "former-cache"
        repo.mkdir()
        storage.mkdir()
        formerly_optional_cache.mkdir()
        self.write_reservation(
            storage,
            "prior-job",
            [repo, storage, formerly_optional_cache],
            required_roots=[repo, storage],
            optional_cache_roots=[formerly_optional_cache],
        )
        formerly_optional_cache.rmdir()

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            roots = budget.inventory_roots(repo, storage, [])

        self.assertNotIn(formerly_optional_cache.resolve(), roots)

    def test_new_reservation_explicit_root_blocks_even_if_it_matches_optional_cache(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        missing_cache = self.root / "legacy-cache"
        repo.mkdir()
        storage.mkdir()
        self.write_reservation(
            storage,
            "prior-job",
            [missing_cache],
            required_roots=[missing_cache],
            optional_cache_roots=[missing_cache],
        )

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[missing_cache]
        ):
            with self.assertRaisesRegex(FileNotFoundError, "legacy-cache"):
                budget.inventory_roots(repo, storage, [])

    def test_partial_new_scope_metadata_cannot_fall_back_to_legacy(self) -> None:
        for job_id, partial_fields in (
            ("scope-missing-optional", {"required_roots": []}),
            ("scope-missing-required", {"optional_cache_roots": []}),
        ):
            with self.subTest(job_id=job_id):
                repo = self.root / f"repo-{job_id}"
                storage = self.root / f"storage-{job_id}"
                missing_cache = self.root / f"cache-{job_id}"
                repo.mkdir()
                storage.mkdir()
                path = self.write_reservation(storage, job_id, [missing_cache])
                record = json.loads(path.read_text(encoding="utf-8"))
                record.update(partial_fields)
                path.write_text(json.dumps(record), encoding="utf-8")

                with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
                    budget, "managed_cache_roots", return_value=[missing_cache]
                ):
                    with self.assertRaisesRegex(OSError, "invalid active reservation inventory"):
                        budget.inventory_roots(repo, storage, [])

    def test_status_blocks_if_a_previously_included_root_cannot_be_scanned(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        previously_included = self.root / "prior-external-root"
        repo.mkdir()
        storage.mkdir()
        previously_included.mkdir()
        self.write_reservation(storage, "prior-job", [previously_included])
        args = argparse.Namespace(
            repo_root=repo,
            storage_root=storage,
            include_root=[],
            reserve_bytes=0,
        )
        output = io.StringIO()

        def fail_on_recorded_root(roots: list[Path]) -> tuple[int, dict[str, int], list[str]]:
            self.assertIn(previously_included.resolve(), roots)
            return 0, {}, [f"cannot scan {previously_included}: PermissionError"]

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ), patch.object(budget, "current_usage", side_effect=fail_on_recorded_root), contextlib.redirect_stdout(output):
            result = budget.status(args)

        self.assertEqual(result, 3)
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED_SCAN")

    def test_reservation_filename_must_match_job_id(self) -> None:
        storage = self.root / "storage"
        storage.mkdir()
        self.write_reservation(storage, "recorded-job", [], filename="different-job.json")

        reservations, errors = budget.load_reservations(storage)

        self.assertEqual(reservations, {})
        self.assertTrue(any("invalid reservation" in error for error in errors))

    def test_duplicate_reservation_ids_are_reported_instead_of_overwriting(self) -> None:
        storage = self.root / "storage"
        storage.mkdir()
        path = self.write_reservation(storage, "duplicate-job", [])

        with patch.object(Path, "glob", return_value=[path, path]):
            reservations, errors = budget.load_reservations(storage)

        self.assertEqual(list(reservations), ["duplicate-job"])
        self.assertTrue(any("duplicate reservation job id" in error for error in errors))

    def test_new_reservation_persists_required_and_optional_scopes(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        explicit = self.root / "explicit"
        optional_cache = self.root / "optional-cache"
        repo.mkdir()
        storage.mkdir()
        explicit.mkdir()
        optional_cache.mkdir()
        args = argparse.Namespace(
            job_id="scope-fields-test",
            reserve_bytes=100,
            repo_root=repo,
            storage_root=storage,
            include_root=[explicit],
        )
        output = io.StringIO()

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[optional_cache]
        ), contextlib.redirect_stdout(output):
            self.assertEqual(budget.reserve(args), 0)
            reservation = json.loads(
                (budget.reservation_dir(storage) / "scope-fields-test.json").read_text(encoding="utf-8")
            )
            self.assertIn(str(repo.resolve()), reservation["required_roots"])
            self.assertIn(str(storage.resolve()), reservation["required_roots"])
            self.assertIn(str(explicit.resolve()), reservation["required_roots"])
            self.assertEqual(reservation["optional_cache_roots"], [str(optional_cache.resolve())])
            self.assertEqual(budget.release(args), 0)

    def test_inventory_fails_closed_for_each_missing_required_root(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        repo.mkdir()
        storage.mkdir()
        worktree = self.root / "missing-worktree"

        with patch.object(budget, "discover_worktrees", return_value=[worktree]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            with self.assertRaisesRegex(FileNotFoundError, "missing-worktree"):
                budget.inventory_roots(repo, storage, [])

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            with self.assertRaisesRegex(FileNotFoundError, "missing-include"):
                budget.inventory_roots(repo, storage, [self.root / "missing-include"])
            with self.assertRaisesRegex(FileNotFoundError, "missing-repo"):
                budget.inventory_roots(self.root / "missing-repo", storage, [])
            with self.assertRaisesRegex(FileNotFoundError, "missing-storage"):
                budget.inventory_roots(repo, self.root / "missing-storage", [])

    def test_nested_explicit_root_is_checked_before_deduplication(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        repo.mkdir()
        storage.mkdir()

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            with self.assertRaisesRegex(FileNotFoundError, "nested-missing"):
                budget.inventory_roots(repo, storage, [repo / "nested-missing"])

    def test_required_storage_root_must_be_a_directory(self) -> None:
        repo = self.root / "repo"
        storage_file = self.root / "storage-file"
        repo.mkdir()
        storage_file.write_text("not a directory", encoding="utf-8")

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            with self.assertRaisesRegex(NotADirectoryError, "storage-file"):
                budget.inventory_roots(repo, storage_file, [])

    def test_empty_required_roots_are_allowed_but_absent_caches_are_omitted(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        worktree = self.root / "worktree"
        cache = self.root / "unused-cache"
        repo.mkdir()
        storage.mkdir()
        worktree.mkdir()

        with patch.object(budget, "discover_worktrees", return_value=[worktree]), patch.object(
            budget, "managed_cache_roots", return_value=[cache]
        ):
            roots = budget.inventory_roots(repo, storage, [])

        self.assertTrue({repo, storage, worktree}.issubset(set(roots)))
        self.assertNotIn(cache, roots)
        self.assertEqual(budget.directory_bytes(repo), (0, []))

    def test_uninspectable_optional_cache_blocks_inventory(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        cache_parent = self.root / "cache-file"
        repo.mkdir()
        storage.mkdir()
        cache_parent.write_text("not a directory", encoding="utf-8")

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[cache_parent / "cache"]
        ):
            with self.assertRaisesRegex(OSError, "optional cache root"):
                budget.inventory_roots(repo, storage, [])

    def test_explicit_file_root_remains_supported(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        included = self.root / "manifest.json"
        repo.mkdir()
        storage.mkdir()
        included.write_text("{}", encoding="utf-8")

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ):
            roots = budget.inventory_roots(repo, storage, [included])

        self.assertIn(included, roots)
        self.assertEqual(budget.directory_bytes(included), (2, []))

    def test_root_disappearing_after_inventory_blocks_scan(self) -> None:
        root = self.root / "disappeared"
        root.mkdir()
        root.rmdir()

        size, errors = budget.directory_bytes(root)

        self.assertEqual(size, 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing inventory root during scan", errors[0])

    def test_status_blocks_if_a_root_disappears_after_inventory(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        disappeared = self.root / "disappeared"
        repo.mkdir()
        storage.mkdir()
        disappeared.mkdir()
        disappeared.rmdir()
        args = argparse.Namespace(
            repo_root=repo,
            storage_root=storage,
            include_root=[],
            reserve_bytes=0,
        )
        output = io.StringIO()

        with patch.object(budget, "inventory_roots", return_value=[disappeared]), patch.object(
            budget, "load_reservations", return_value=({}, [])
        ), contextlib.redirect_stdout(output):
            result = budget.status(args)

        self.assertEqual(result, 3)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "BLOCKED_SCAN")
        self.assertIn("missing inventory root during scan", report["errors"][0])

    def test_status_blocks_when_an_explicit_root_is_missing(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        repo.mkdir()
        storage.mkdir()
        args = argparse.Namespace(
            repo_root=repo,
            storage_root=storage,
            include_root=[self.root / "missing-include"],
            reserve_bytes=0,
        )
        output = io.StringIO()

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ), contextlib.redirect_stdout(output):
            result = budget.status(args)

        self.assertEqual(result, 3)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "BLOCKED_SCAN")
        self.assertIn("missing-include", report["detail"])

    def test_status_blocks_when_a_worktree_is_missing(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        missing_worktree = self.root / "missing-worktree"
        repo.mkdir()
        storage.mkdir()
        args = argparse.Namespace(
            repo_root=repo,
            storage_root=storage,
            include_root=[],
            reserve_bytes=0,
        )
        output = io.StringIO()

        with patch.object(budget, "discover_worktrees", return_value=[missing_worktree]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ), contextlib.redirect_stdout(output):
            result = budget.status(args)

        self.assertEqual(result, 3)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "BLOCKED_SCAN")
        self.assertIn("missing-worktree", report["detail"])

    def test_reserve_does_not_create_missing_storage_root(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "missing-storage"
        repo.mkdir()
        args = argparse.Namespace(
            job_id="missing-root-test",
            reserve_bytes=1,
            repo_root=repo,
            storage_root=storage,
            include_root=[],
        )
        output = io.StringIO()

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ), contextlib.redirect_stdout(output):
            result = budget.reserve(args)

        self.assertEqual(result, 3)
        self.assertFalse(storage.exists())
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED_SCAN")

    def test_reserve_does_not_create_registry_for_missing_include_root(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        repo.mkdir()
        storage.mkdir()
        args = argparse.Namespace(
            job_id="missing-include-test",
            reserve_bytes=1,
            repo_root=repo,
            storage_root=storage,
            include_root=[self.root / "missing-include"],
        )
        output = io.StringIO()

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ), contextlib.redirect_stdout(output):
            result = budget.reserve(args)

        self.assertEqual(result, 3)
        self.assertFalse((storage / ".budget").exists())
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED_SCAN")

    def test_reserve_blocks_when_a_worktree_is_missing(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        missing_worktree = self.root / "missing-worktree"
        repo.mkdir()
        storage.mkdir()
        args = argparse.Namespace(
            job_id="missing-worktree-test",
            reserve_bytes=1,
            repo_root=repo,
            storage_root=storage,
            include_root=[],
        )
        output = io.StringIO()

        with patch.object(budget, "discover_worktrees", return_value=[missing_worktree]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ), contextlib.redirect_stdout(output):
            result = budget.reserve(args)

        self.assertEqual(result, 3)
        self.assertFalse((storage / ".budget").exists())
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "BLOCKED_SCAN")
        self.assertIn("missing-worktree", report["detail"])

    def test_reserve_does_not_recreate_storage_root_removed_before_lock(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        repo.mkdir()
        storage.mkdir()
        args = argparse.Namespace(
            job_id="removed-before-lock-test",
            reserve_bytes=1,
            repo_root=repo,
            storage_root=storage,
            include_root=[],
        )
        output = io.StringIO()
        original_registry_lock = budget.registry_lock

        @contextmanager
        def remove_storage_before_lock(path: Path):
            storage.rmdir()
            with original_registry_lock(path):
                yield

        with patch.object(budget, "discover_worktrees", return_value=[]), patch.object(
            budget, "managed_cache_roots", return_value=[]
        ), patch.object(budget, "registry_lock", remove_storage_before_lock), contextlib.redirect_stdout(output):
            result = budget.reserve(args)

        self.assertEqual(result, 3)
        self.assertFalse(storage.exists())
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED_SCAN")

    def test_reserve_rechecks_required_roots_under_lock(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        include = self.root / "included"
        repo.mkdir()
        storage.mkdir()
        include.mkdir()
        args = argparse.Namespace(
            job_id="removed-include-test",
            reserve_bytes=1,
            repo_root=repo,
            storage_root=storage,
            include_root=[include],
        )
        output = io.StringIO()
        inventory_calls = 0

        def disappear_during_locked_recheck(*_args: object) -> list[Path]:
            nonlocal inventory_calls
            inventory_calls += 1
            if inventory_calls == 1:
                return [repo, storage, include]
            include.rmdir()
            raise FileNotFoundError(f"required inventory root is missing: {include}")

        with patch.object(budget, "inventory_roots", side_effect=disappear_during_locked_recheck), contextlib.redirect_stdout(output):
            result = budget.reserve(args)

        self.assertEqual(result, 3)
        self.assertEqual(inventory_calls, 2)
        self.assertFalse(list((storage / ".budget" / "reservations").glob("*.json")))
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED_SCAN")

    def test_status_blocks_at_exact_budget_limit(self) -> None:
        root = self.root / "fixture"
        args = argparse.Namespace(
            repo_root=root,
            storage_root=root,
            include_root=[],
            reserve_bytes=10,
        )
        output = io.StringIO()

        with patch.object(budget, "inventory_roots", return_value=[root]), patch.object(
            budget,
            "current_usage",
            return_value=(budget.LIMIT_BYTES - 10, {str(root): budget.LIMIT_BYTES - 10}, []),
        ), patch.object(budget, "load_reservations", return_value=({}, [])), contextlib.redirect_stdout(output):
            result = budget.status(args)

        self.assertEqual(result, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "BLOCKED_LIMIT")
        self.assertEqual(report["projected_bytes"], budget.LIMIT_BYTES)

    def test_reserve_blocks_at_exact_budget_limit(self) -> None:
        repo = self.root / "repo"
        storage = self.root / "storage"
        repo.mkdir()
        storage.mkdir()
        args = argparse.Namespace(
            job_id="exact-budget-test",
            reserve_bytes=10,
            repo_root=repo,
            storage_root=storage,
            include_root=[],
        )
        output = io.StringIO()

        with patch.object(budget, "inventory_roots", return_value=[repo, storage]), patch.object(
            budget,
            "current_usage",
            return_value=(budget.LIMIT_BYTES - 10, {str(repo): budget.LIMIT_BYTES - 10}, []),
        ), patch.object(budget, "load_reservations", return_value=({}, [])), contextlib.redirect_stdout(output):
            result = budget.reserve(args)

        self.assertEqual(result, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "BLOCKED_LIMIT")
        self.assertEqual(report["projected_bytes"], budget.LIMIT_BYTES)


if __name__ == "__main__":
    unittest.main()
