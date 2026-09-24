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
