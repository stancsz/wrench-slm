from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch as mock_patch

from wrench_harness.execution_state import (
    EvidenceSource,
    ExecutionStateError,
    StateFieldSpec,
    stable_source_evidence_id,
)
from wrench_harness.execution_state_store import ExecutionStateStore


TASK_SHA256 = "a" * 64
OBSERVATION_SHA256 = "b" * 64
TEST_SHA256 = "c" * 64
EVIDENCE = {"obs-1": OBSERVATION_SHA256, "test-1": TEST_SHA256}
FIELDS = {
    "task_summary": StateFieldSpec("string", required=True, max_chars=256),
    "changed_files": StateFieldSpec("string_list", max_chars=128, max_items=8),
    "verified": StateFieldSpec("boolean"),
}


def proposal(*changes: dict[str, object], revision: int = 0) -> dict[str, object]:
    return {
        "schema": "wrench.execution-state-patch.v1",
        "session_id": "session-1",
        "base_revision": revision,
        "changes": list(changes),
    }


def set_change(field: str, value: object, evidence_id: str = "obs-1") -> dict[str, object]:
    return {
        "op": "set",
        "field": field,
        "value": value,
        "evidence_ids": [evidence_id],
    }


class ExecutionStateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch_root = Path.cwd() / "tmp" / "wrench-state-store-tests-iter095"
        if self.scratch_root.exists():
            raise RuntimeError(f"scratch path already exists: {self.scratch_root}")
        self.scratch_root.mkdir(parents=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.scratch_root)
        self.store_root = Path(self.temp.name) / "session"
        self.store = self.make_store()

    def tearDown(self) -> None:
        self.temp.cleanup()
        try:
            self.scratch_root.rmdir()
        except OSError:
            pass

    def make_store(
        self,
        *,
        field_specs=FIELDS,
        task_spec_sha256=TASK_SHA256,
        root: Path | None = None,
        max_events: int = 4096,
        max_bytes: int = 64 * 1024 * 1024,
    ) -> ExecutionStateStore:
        return ExecutionStateStore(
            root or self.store_root,
            session_id="session-1",
            task_spec_sha256=task_spec_sha256,
            field_specs=field_specs,
            max_events=max_events,
            max_bytes=max_bytes,
        )

    def assert_code(self, expected_code: str, operation) -> None:
        with self.assertRaises(ExecutionStateError) as error:
            operation()
        self.assertEqual(error.exception.code, expected_code)

    def test_commit_and_restart_replay_state_and_evidence(self) -> None:
        initial = self.store.load(evidence_hashes={})
        self.assertEqual(initial.state.revision, 0)
        committed = self.store.commit(
            proposal(set_change("task_summary", "Parser failure confirmed")),
            evidence_hashes=EVIDENCE,
        )
        self.assertEqual(committed.event_count, 1)
        self.assertEqual(committed.result.state.revision, 1)

        restarted = self.make_store().load(evidence_hashes=EVIDENCE)
        self.assertEqual(restarted.state.sha256, committed.result.state.sha256)
        self.assertEqual(restarted.event_count, 1)
        self.assertEqual(restarted.last_event_sha256, committed.event_sha256)

    def test_source_path_metadata_survives_restart_and_binds_stable_identity(self) -> None:
        namespace = "d" * 64
        digest = OBSERVATION_SHA256
        evidence_id = stable_source_evidence_id(namespace, "src/parser.py", digest)
        source = EvidenceSource(namespace, "src/parser.py")
        manifest = {evidence_id: digest}
        proposal_value = proposal(set_change("task_summary", "Parser behavior pinned", evidence_id))

        committed = self.store.commit(
            proposal_value,
            evidence_hashes=manifest,
            evidence_sources={evidence_id: source},
        )
        restarted = self.make_store().load(evidence_hashes=manifest)
        revalidation = self.make_store().load_for_revalidation()

        ref = restarted.state.facts["task_summary"].evidence[0]
        self.assertEqual(ref.source, source)
        self.assertEqual(restarted.state.sha256, committed.result.state.sha256)
        self.assertEqual(restarted.last_event_sha256, committed.event_sha256)
        self.assertFalse(revalidation.current_evidence_verified)
        self.assertEqual(revalidation.state.sha256, committed.result.state.sha256)
        self.assertEqual(revalidation.state.facts["task_summary"].evidence[0].source, source)
        self.assertNotEqual(
            evidence_id,
            stable_source_evidence_id(namespace, "src/parser.py", "e" * 64),
        )

    def test_source_path_metadata_must_match_the_stable_evidence_id(self) -> None:
        namespace = "d" * 64
        digest = OBSERVATION_SHA256
        evidence_id = stable_source_evidence_id(namespace, "src/parser.py", digest)
        proposal_value = proposal(set_change("task_summary", "Parser behavior pinned", evidence_id))

        self.assert_code(
            "state_evidence_sources_invalid",
            lambda: self.store.commit(
                proposal_value,
                evidence_hashes={evidence_id: digest},
                evidence_sources={evidence_id: EvidenceSource(namespace, "src/other.py")},
            ),
        )

    def test_stale_revision_cannot_overwrite_a_committed_update(self) -> None:
        self.store.commit(
            proposal(set_change("task_summary", "First result")),
            evidence_hashes=EVIDENCE,
        )
        self.assert_code(
            "state_patch_stale",
            lambda: self.store.commit(
                proposal(set_change("verified", True, "test-1"), revision=0),
                evidence_hashes=EVIDENCE,
            ),
        )
        self.assertEqual(self.store.load(evidence_hashes=EVIDENCE).event_count, 1)

    def test_complete_staging_record_is_recovered_after_interrupted_publish(self) -> None:
        with mock_patch(
            "wrench_harness.execution_state_store.os.replace",
            side_effect=OSError("simulated interruption before event publication"),
        ):
            self.assert_code(
                "state_store_publish_failed",
                lambda: self.store.commit(
                    proposal(set_change("task_summary", "Recovered result")),
                    evidence_hashes=EVIDENCE,
                ),
            )

        recovered = self.make_store().load(evidence_hashes=EVIDENCE)
        self.assertTrue(recovered.recovered_staged_event)
        self.assertEqual(recovered.state.revision, 1)
        self.assertEqual(recovered.state.facts["task_summary"].value, "Recovered result")

    def test_partial_staging_record_is_ignored_and_preserved(self) -> None:
        self.store.load(evidence_hashes={})
        events = self.store_root / "events"
        partial = events / f"revision-00000001.{uuid.uuid4().hex}.tmp"
        partial.write_bytes(b"{partial")

        loaded = self.store.load(evidence_hashes={})
        self.assertEqual(loaded.state.revision, 0)
        self.assertEqual(loaded.ignored_staging_files, (partial.name,))
        self.assertTrue(partial.exists())

    def test_corrupt_committed_event_fails_closed(self) -> None:
        self.store.commit(
            proposal(set_change("task_summary", "Original result")),
            evidence_hashes=EVIDENCE,
        )
        event = self.store_root / "events" / "revision-00000001.json"
        raw = event.read_text(encoding="utf-8")
        event.write_text(raw.replace("Original result", "Altered result"), encoding="utf-8")

        self.assert_code(
            "state_store_event_hash_mismatch",
            lambda: self.store.load(evidence_hashes=EVIDENCE),
        )

    def test_load_requires_current_evidence_for_all_live_state_facts(self) -> None:
        self.store.commit(
            proposal(set_change("task_summary", "Evidence-backed result")),
            evidence_hashes=EVIDENCE,
        )
        self.assert_code(
            "state_store_evidence_unavailable",
            lambda: self.make_store().load(evidence_hashes={}),
        )

    def test_restart_rejects_changed_field_schema_or_task_identity(self) -> None:
        self.store.commit(
            proposal(set_change("task_summary", "Schema-bound result")),
            evidence_hashes=EVIDENCE,
        )
        changed_fields = dict(FIELDS)
        changed_fields["task_summary"] = StateFieldSpec("string", required=True, max_chars=128)
        self.assert_code(
            "state_store_field_schema_mismatch",
            lambda: self.make_store(field_specs=changed_fields).load(evidence_hashes=EVIDENCE),
        )
        self.assert_code(
            "state_store_task_spec_mismatch",
            lambda: self.make_store(task_spec_sha256="d" * 64).load(evidence_hashes=EVIDENCE),
        )

    def test_recovery_respects_configured_event_count_limit(self) -> None:
        self.store.commit(
            proposal(set_change("task_summary", "First result")),
            evidence_hashes=EVIDENCE,
        )
        self.store.commit(
            proposal(set_change("verified", True, "test-1"), revision=1),
            evidence_hashes=EVIDENCE,
        )
        events = self.store_root / "events"
        second_event = events / "revision-00000002.json"
        staged_event = events / f"revision-00000002.{uuid.uuid4().hex}.tmp"
        second_event.replace(staged_event)

        capped_store = self.make_store(max_events=1)
        self.assert_code(
            "state_store_event_limit_exceeded",
            lambda: capped_store.load(evidence_hashes=EVIDENCE),
        )

    def test_store_root_rejects_parent_traversal(self) -> None:
        with self.assertRaisesRegex(ValueError, "state_store_root_parent_traversal_invalid"):
            self.make_store(root=Path.cwd() / "tmp" / ".." / "outside")

    def test_two_store_instances_conflict_on_same_base_revision(self) -> None:
        other_store = self.make_store()
        first = self.store.commit(
            proposal(set_change("task_summary", "Winner")),
            evidence_hashes=EVIDENCE,
        )
        self.assertEqual(first.result.state.revision, 1)
        self.assert_code(
            "state_patch_stale",
            lambda: other_store.commit(
                proposal(set_change("task_summary", "Stale writer")),
                evidence_hashes=EVIDENCE,
            ),
        )
        final = self.store.load(evidence_hashes=EVIDENCE)
        self.assertEqual(final.state.facts["task_summary"].value, "Winner")

    def test_two_valid_pending_events_for_the_same_revision_are_ambiguous(self) -> None:
        committed = self.store.commit(
            proposal(set_change("task_summary", "Pending result")),
            evidence_hashes=EVIDENCE,
        )
        event_path = self.store_root / "events" / "revision-00000001.json"
        event_bytes = event_path.read_bytes()
        event_path.unlink()
        events = self.store_root / "events"
        (events / f"revision-00000001.{uuid.uuid4().hex}.tmp").write_bytes(event_bytes)
        (events / f"revision-00000001.{uuid.uuid4().hex}.tmp").write_bytes(event_bytes)

        self.assert_code(
            "state_store_ambiguous_staged_events",
            lambda: self.store.load(evidence_hashes=EVIDENCE),
        )


if __name__ == "__main__":
    unittest.main()
