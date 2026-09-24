from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from wrench_harness.snapshot import SnapshotAdmissionError, bind_source_root
from wrench_harness.snapshot_root_inventory import (
    InventoryRecord,
    RootInventoryPolicy,
    create_snapshot_from_inventory,
    inventory_source_root,
    validate_root_inventory_receipt,
    _canonical,
    _manifest_payload,
    _receipt_payload,
)


def _policy(*scopes: str, exclusions: tuple[str, ...] = (), **limits: int) -> RootInventoryPolicy:
    return RootInventoryPolicy(tuple(scopes), exclusions, **limits)


def _rehash_receipt(receipt, records, *, entries_seen=None):
    entries_seen = receipt.entries_seen if entries_seen is None else entries_seen
    manifest_sha256 = hashlib.sha256(
        _canonical(
            _manifest_payload(
                receipt.normalized_root,
                receipt.root_location_sha256,
                receipt.root_identity,
                receipt.policy,
                records,
            )
        )
    ).hexdigest()
    payload = _canonical(
        _receipt_payload(
            receipt.normalized_root,
            receipt.root_location_sha256,
            receipt.root_identity,
            receipt.policy,
            records,
            entries_seen,
            receipt.excluded_entries,
            receipt.errors,
            receipt.truncated_by,
            receipt.complete,
            manifest_sha256,
            0,
        )
    )
    from dataclasses import replace

    return replace(
        receipt,
        records=records,
        entries_seen=entries_seen,
        manifest_sha256=manifest_sha256,
        receipt_sha256=hashlib.sha256(payload).hexdigest(),
        output_bytes=len(payload),
    )


def test_scoped_inventory_is_sorted_root_bound_and_admits_snapshot(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "z.py").write_text("z = 2\n", encoding="utf-8")
    (tmp_path / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
    (tmp_path / "outside.txt").write_text("outside\n", encoding="utf-8")
    binding = bind_source_root(tmp_path)

    receipt = inventory_source_root(binding, _policy("src"))

    assert receipt.complete
    assert [row.path for row in receipt.records] == ["src/a.py", "src/z.py"]
    assert receipt.normalized_root == str(tmp_path.resolve())
    assert receipt.root_identity == binding.root_identity
    assert validate_root_inventory_receipt(receipt)
    snapshot = create_snapshot_from_inventory(binding, receipt)
    assert tuple((row.path, row.size_bytes, row.sha256) for row in snapshot.sources) == tuple(
        (row.path, row.size_bytes, row.sha256) for row in receipt.records
    )


def test_explicit_exclusion_is_reported_and_complete_within_policy(tmp_path: Path) -> None:
    (tmp_path / "src" / "generated").mkdir(parents=True)
    (tmp_path / "src" / "keep.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "src" / "generated" / "large.bin").write_bytes(b"x")

    receipt = inventory_source_root(tmp_path, _policy("src", exclusions=("src/generated",)))

    assert receipt.complete
    assert receipt.excluded_entries == 1
    assert [row.path for row in receipt.records] == ["src/keep.py"]


def test_caps_return_incomplete_receipt_and_snapshot_admission_fails(tmp_path: Path) -> None:
    (tmp_path / "tree").mkdir()
    for name in ("a", "b", "c"):
        (tmp_path / "tree" / name).write_text(name, encoding="utf-8")

    receipt = inventory_source_root(tmp_path, _policy("tree", max_entries=2))

    assert not receipt.complete
    assert "entry_limit" in receipt.truncated_by
    assert len(receipt.records) <= 2
    with pytest.raises(SnapshotAdmissionError, match="incomplete_or_invalid"):
        create_snapshot_from_inventory(tmp_path, receipt)


def test_depth_cap_is_visible_and_does_not_claim_completion(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "file").write_text("value", encoding="utf-8")

    receipt = inventory_source_root(tmp_path, _policy(".", max_depth=1))

    assert not receipt.complete
    assert "depth_limit" in receipt.truncated_by
    assert any(row.code == "depth_limit" for row in receipt.errors)


def test_path_scopes_are_disjoint_and_policy_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(SnapshotAdmissionError, match="overlapping_inventory_scopes"):
        inventory_source_root(tmp_path, _policy(".", "src"))
    with pytest.raises(SnapshotAdmissionError, match="invalid_inventory_policy"):
        inventory_source_root(tmp_path, object())  # type: ignore[arg-type]


def test_invalid_or_unsafe_inputs_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(SnapshotAdmissionError):
        inventory_source_root(tmp_path, _policy("../outside"))
    assert inventory_source_root(tmp_path, _policy(".")).complete


def test_policy_exclusions_and_duplicate_scope_rejections(tmp_path: Path) -> None:
    with pytest.raises(SnapshotAdmissionError, match="duplicate_inventory_policy_path"):
        inventory_source_root(tmp_path, _policy(".", exclusions=("x", "x")))


@pytest.mark.parametrize(
    ("scope", "exclusion"),
    (("src", "src"), ("src/nested", "src")),
)
def test_exclusion_cannot_cover_scope(tmp_path: Path, scope: str, exclusion: str) -> None:
    with pytest.raises(SnapshotAdmissionError, match="inventory_exclusion_covers_scope"):
        inventory_source_root(tmp_path, _policy(scope, exclusions=(exclusion,)))


def test_rehashed_out_of_scope_record_cannot_be_admitted(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "inside.py").write_text("inside", encoding="utf-8")
    outside_data = b"outside"
    (tmp_path / "outside.py").write_bytes(outside_data)
    receipt = inventory_source_root(tmp_path, _policy("src"))
    forged_row = InventoryRecord("outside.py", len(outside_data), hashlib.sha256(outside_data).hexdigest())
    forged = _rehash_receipt(receipt, (forged_row,))

    assert not validate_root_inventory_receipt(forged)
    with pytest.raises(SnapshotAdmissionError, match="incomplete_or_invalid"):
        create_snapshot_from_inventory(tmp_path, forged)


def test_rehashed_omitted_in_scope_file_is_rejected_by_fresh_inventory(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "one.py").write_text("one", encoding="utf-8")
    (tmp_path / "src" / "two.py").write_text("two", encoding="utf-8")
    receipt = inventory_source_root(tmp_path, _policy("src"))
    assert len(receipt.records) == 2

    forged = _rehash_receipt(receipt, (receipt.records[0],))

    assert validate_root_inventory_receipt(forged)
    with pytest.raises(SnapshotAdmissionError, match="root_inventory_changed_since_receipt"):
        create_snapshot_from_inventory(tmp_path, forged)


def test_record_and_exclusion_counts_cannot_exceed_seen_entries(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "one.py").write_text("one", encoding="utf-8")
    receipt = inventory_source_root(tmp_path, _policy("src"))

    forged = _rehash_receipt(receipt, receipt.records, entries_seen=0)

    assert not validate_root_inventory_receipt(forged)


def test_windows_scope_overlap_is_case_insensitive(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows path comparison only")
    with pytest.raises(SnapshotAdmissionError, match="overlapping_inventory_scopes"):
        inventory_source_root(tmp_path, _policy("src", "SRC/nested"))


def test_windows_exclusions_are_case_insensitive(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows path comparison only")
    (tmp_path / "src" / "generated").mkdir(parents=True)
    (tmp_path / "src" / "generated" / "skip.py").write_text("skip", encoding="utf-8")

    receipt = inventory_source_root(tmp_path, _policy(".", exclusions=("SRC/GENERATED",)))

    assert receipt.complete
    assert receipt.excluded_entries == 1
    assert receipt.records == ()


def test_windows_exclusion_ancestor_is_case_insensitive(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows path comparison only")
    with pytest.raises(SnapshotAdmissionError, match="inventory_exclusion_covers_scope"):
        inventory_source_root(tmp_path, _policy("Src/Nested", exclusions=("sRc",)))


def test_receipt_tampering_is_rejected(tmp_path: Path) -> None:
    from dataclasses import replace

    (tmp_path / "a.txt").write_text("one", encoding="utf-8")
    receipt = inventory_source_root(tmp_path, _policy("."))
    assert not validate_root_inventory_receipt(replace(receipt, excluded_entries=1))
    assert not validate_root_inventory_receipt(replace(receipt, records=(InventoryRecord("b.txt", 3, receipt.records[0].sha256),)))


def test_per_file_limit_is_an_error_and_incomplete(tmp_path: Path) -> None:
    (tmp_path / "oversized").write_bytes(b"x" * (256 * 1024 + 1))

    receipt = inventory_source_root(tmp_path, _policy("."))

    assert not receipt.complete
    assert receipt.records == ()
    assert [(row.path, row.code) for row in receipt.errors] == [("oversized", "source_size_limit")]


def test_symlink_entries_are_counted_as_errors_without_following(tmp_path: Path) -> None:
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    try:
        (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    receipt = inventory_source_root(tmp_path, _policy("."))

    assert not receipt.complete
    assert receipt.records == ()
    assert receipt.errors[0].code == "reparse_point_forbidden"


def test_exact_entry_cap_can_be_complete(tmp_path: Path) -> None:
    (tmp_path / "tree").mkdir()
    (tmp_path / "tree" / "a").write_text("a", encoding="utf-8")
    (tmp_path / "tree" / "b").write_text("b", encoding="utf-8")

    receipt = inventory_source_root(tmp_path, _policy("tree", max_entries=2))

    assert receipt.complete
    assert receipt.entries_seen == 2
    assert len(receipt.records) == 2


def test_nested_entries_obey_one_global_cap(tmp_path: Path) -> None:
    (tmp_path / "tree" / "nested").mkdir(parents=True)
    (tmp_path / "tree" / "nested" / "a").write_text("a", encoding="utf-8")
    (tmp_path / "tree" / "b").write_text("b", encoding="utf-8")

    receipt = inventory_source_root(tmp_path, _policy("tree", max_entries=2))

    assert not receipt.complete
    assert receipt.entries_seen <= 2
    assert "entry_limit" in receipt.truncated_by


def test_scope_ancestor_symlink_is_rejected_without_traversal(tmp_path: Path) -> None:
    outside = tmp_path.parent / (tmp_path.name + "-scope-outside")
    (outside / "nested").mkdir(parents=True)
    (outside / "nested" / "secret.txt").write_text("secret", encoding="utf-8")
    try:
        (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(SnapshotAdmissionError, match="reparse_point_forbidden"):
        inventory_source_root(tmp_path, _policy("linked/nested"))
