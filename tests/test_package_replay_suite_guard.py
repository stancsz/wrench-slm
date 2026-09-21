from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import run_package_220_replay


def test_package_replay_rejects_historical_suite_by_default(tmp_path: Path):
    cases_dir = tmp_path / "suite"
    cases_dir.mkdir()
    (cases_dir / "cases.jsonl").write_text("{}\n", encoding="utf-8")
    (cases_dir / "manifest.json").write_text(
        json.dumps({"status": "HISTORICAL_REGRESSION_ONLY_SUPERSEDED_BY_MECHANICAL_WORKER_V1"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="historical or superseded"):
        run_package_220_replay._validate_suite_manifest(cases_dir / "cases.jsonl")


def test_package_replay_can_explicitly_allow_historical_suite(tmp_path: Path):
    cases_dir = tmp_path / "suite"
    cases_dir.mkdir()
    (cases_dir / "cases.jsonl").write_text("{}\n", encoding="utf-8")
    (cases_dir / "manifest.json").write_text(
        json.dumps({"status": "HISTORICAL_REGRESSION_ONLY_SUPERSEDED_BY_MECHANICAL_WORKER_V1"}),
        encoding="utf-8",
    )
    run_package_220_replay._validate_suite_manifest(cases_dir / "cases.jsonl", allow_historical_suite=True)
