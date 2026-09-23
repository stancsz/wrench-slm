"""Synthetic fixtures for the local redacted-request intake contract."""
from __future__ import annotations

import hashlib
import json

import pytest

from tools.intake_system_one_real_requests import parse_rows, run


def _rows():
    wanted = {"fit": 12, "calibration": 4, "sealed": 4}
    groups = {key: [] for key in wanted}
    candidate = 0
    while any(len(groups[key]) < count for key, count in wanted.items()):
        workflow = f"workflow-{candidate}"
        bucket = int(hashlib.sha256(workflow.encode()).hexdigest()[:8], 16) % 100
        split = "fit" if bucket < 70 else "calibration" if bucket < 85 else "sealed"
        if len(groups[split]) < wanted[split]:
            groups[split].append(workflow)
        candidate += 1
    rows = []
    for workflows in groups.values():
        for workflow in workflows:
            for label in ("abstain", "not_abstain"):
                rows.append({"request_id": f"{workflow}-{label}",
                             "workflow_id": workflow,
                             "prompt": f"Fixture {workflow}: {label} bounded tool request.",
                             "label": label, "redacted": True,
                             "source": "real_wrench", "label_source": "human_review"})
    return rows


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _setup(tmp_path, rows, frozen_prompt="a separate frozen prompt"):
    source = tmp_path / "data/private/input.jsonl"
    output = tmp_path / "data/private/processed"
    suite = tmp_path / "phases/system-one-binary-5k-20260922/cases.jsonl"
    _write_jsonl(source, rows)
    _write_jsonl(suite, [{"prompt": frozen_prompt}])
    return source, output


def test_intake_keeps_workflows_apart_and_outputs_no_identifiers(tmp_path):
    rows = _rows()
    source, output = _setup(tmp_path, rows)
    manifest = run(tmp_path, source.relative_to(tmp_path), output.relative_to(tmp_path))
    assert manifest["status"] == "REDACTED_LOCAL_INTAKE_ONLY"
    assert manifest["counts"]["unique_rows"] == 40
    assert manifest["frozen_suite_prompt_overlap"] == 0
    splits = {name: [json.loads(line) for line in
                     (output / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
              for name in ("fit", "calibration", "sealed")}
    assert sum(map(len, splits.values())) == 40
    assert all({row["label"] for row in split} == {"abstain", "not_abstain"}
               for split in splits.values())
    workflow_sets = [{row["workflow_id_hash"] for row in split} for split in splits.values()]
    assert len(set.union(*workflow_sets)) == sum(map(len, workflow_sets))
    assert "workflow-" not in (output / "manifest.json").read_text(encoding="utf-8")
    assert "request_id" not in splits["fit"][0]
    assert "workflow_id" not in splits["fit"][0]


def test_conflicting_labels_rejected():
    rows = _rows()
    rows[1]["prompt"] = rows[0]["prompt"]
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    with pytest.raises(ValueError, match="conflicting duplicate label"):
        parse_rows(raw)


@pytest.mark.parametrize("prompt", [
    "Email alice@example.com to start the request",
    "Read sk-12345678901234567890 from the request",
    "Use AKIA1234567890123456 for the request",
    "Bearer abcdefghijklmnopqrstuvwxyz0123456789",
])
def test_sensitive_prompt_rejected(prompt):
    rows = _rows()
    rows[0]["prompt"] = prompt
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    with pytest.raises(ValueError, match="potential sensitive text"):
        parse_rows(raw)


def test_rejects_frozen_overlap_before_writing(tmp_path):
    rows = _rows()
    source, output = _setup(tmp_path, rows, frozen_prompt=rows[0]["prompt"])
    with pytest.raises(ValueError, match="overlaps frozen diagnostic suite"):
        run(tmp_path, source, output)
    assert not output.exists()


def test_paths_must_remain_private_and_failure_leaves_no_output(tmp_path):
    rows = _rows()
    source, output = _setup(tmp_path, rows)
    with pytest.raises(ValueError, match="must stay under data/private"):
        run(tmp_path, source, tmp_path / "outside")
    assert not output.exists()
    rows[0]["redacted"] = False
    _write_jsonl(source, rows)
    with pytest.raises(ValueError, match="invalid real request row"):
        run(tmp_path, source, output)
    assert not output.exists()
