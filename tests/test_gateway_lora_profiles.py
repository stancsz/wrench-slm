from __future__ import annotations

import unittest
import tempfile
import os
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.train_gateway_lora_screen_02_gpu import (
    ADAPTER_PROFILES,
    ATTENTION_PREFLIGHT_JOB_ID,
    EXPECTED_FIT_OPTIMIZER_STEPS,
    FIT_JOB_ID,
    _run_main,
    claim_job_id,
    finalize_adapter_no_replace,
    minimum_destination_free_bytes,
    minimum_resource_fractions,
    select_lora_targets,
)


class Linear:
    pass


def qwen035_08b_named_modules() -> list[tuple[str, Linear]]:
    modules: list[tuple[str, Linear]] = []
    full_attention_suffixes = ("q_proj", "k_proj", "v_proj", "o_proj")
    linear_attention_suffixes = (
        "in_proj_qkv", "in_proj_z", "in_proj_a", "in_proj_b", "out_proj",
    )
    mlp_suffixes = ("gate_proj", "up_proj", "down_proj")
    for layer in range(24):
        if layer % 4 == 3:
            modules.extend(
                (f"model.language_model.layers.{layer}.self_attn.{suffix}", Linear())
                for suffix in full_attention_suffixes
            )
        else:
            modules.extend(
                (f"model.language_model.layers.{layer}.linear_attn.{suffix}", Linear())
                for suffix in linear_attention_suffixes
            )
        modules.extend(
            (f"model.language_model.layers.{layer}.mlp.{suffix}", Linear())
            for suffix in mlp_suffixes
        )
    return modules


class AdapterProfileTests(unittest.TestCase):
    def test_softmax_attention_profile_selects_only_24_full_attention_projections(self) -> None:
        targets = select_lora_targets(
            qwen035_08b_named_modules(), Linear, "softmax-attention-only",
        )

        self.assertEqual(len(targets), 24)
        self.assertTrue(all(".self_attn." in name for name in targets))
        self.assertEqual({name.rsplit(".", 1)[-1] for name in targets}, {
            "q_proj", "k_proj", "v_proj", "o_proj",
        })

    def test_all_projection_profile_preserves_the_186_target_baseline(self) -> None:
        targets = select_lora_targets(
            qwen035_08b_named_modules(), Linear, "all-projections",
        )

        self.assertEqual(len(targets), 186)
        self.assertEqual({name.rsplit(".", 1)[-1] for name in targets}, {
            "q_proj", "k_proj", "v_proj", "o_proj", "in_proj_qkv", "in_proj_z",
            "in_proj_a", "in_proj_b", "out_proj", "gate_proj", "up_proj", "down_proj",
        })

    def test_attention_profile_rejects_a_missing_projection(self) -> None:
        modules = qwen035_08b_named_modules()
        modules = [row for row in modules if not row[0].endswith(".self_attn.o_proj")]

        with self.assertRaisesRegex(RuntimeError, "target module mismatch"):
            select_lora_targets(modules, Linear, "softmax-attention-only")

    def test_job_claim_is_exclusive_and_rejects_id_reuse(self) -> None:
        tmp_root = Path(__file__).resolve().parents[1] / "tmp"
        tmp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as scratch:
            claim_dir = Path(scratch) / "unique-job"
            self.assertEqual(claim_job_id(claim_dir), claim_dir)
            marker = claim_dir / "owner-marker"
            marker.write_text("first owner", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "already claimed"):
                claim_job_id(claim_dir)

            self.assertEqual(marker.read_text(encoding="utf-8"), "first owner")

    @unittest.skipUnless(os.name == "nt", "candidate rename semantics are pinned to Windows")
    def test_candidate_finalization_never_replaces_an_existing_destination(self) -> None:
        tmp_root = Path(__file__).resolve().parents[1] / "tmp"
        tmp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as scratch:
            root = Path(scratch)
            staging = root / "staging"
            destination = root / "candidate"
            staging.mkdir()
            destination.mkdir()
            (staging / "candidate.bin").write_bytes(b"new")
            marker = destination / "preserve.txt"
            marker.write_text("existing candidate", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "destination already exists"):
                finalize_adapter_no_replace(staging, destination)

            self.assertEqual(marker.read_text(encoding="utf-8"), "existing candidate")
            self.assertTrue((staging / "candidate.bin").is_file())

    @unittest.skipUnless(os.name == "nt", "candidate rename semantics are pinned to Windows")
    def test_candidate_finalization_renames_to_an_absent_destination(self) -> None:
        tmp_root = Path(__file__).resolve().parents[1] / "tmp"
        tmp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as scratch:
            root = Path(scratch)
            staging = root / "staging"
            destination = root / "candidate"
            staging.mkdir()
            (staging / "candidate.bin").write_bytes(b"candidate")

            finalize_adapter_no_replace(staging, destination)

            self.assertFalse(staging.exists())
            self.assertEqual((destination / "candidate.bin").read_bytes(), b"candidate")

    def test_resource_summary_records_the_minimum_ram_and_vram_fractions(self) -> None:
        rows = [
            {"ram_free_fraction": 0.25, "gpu_free_fraction": 0.6},
            {"ram_free_fraction": 0.12, "gpu_free_fraction": 0.5},
        ]

        self.assertEqual(minimum_resource_fractions(rows), {
            "minimum_ram_free_fraction": 0.12,
            "minimum_gpu_free_fraction": 0.5,
        })

    def test_destination_headroom_is_added_to_the_job_reservation(self) -> None:
        operating_headroom = 5 * 1024 * 1024 * 1024

        self.assertEqual(minimum_destination_free_bytes(250_000_000), operating_headroom + 250_000_000)
        self.assertEqual(minimum_destination_free_bytes(1_500_000_000), operating_headroom + 1_500_000_000)
        with self.assertRaises(ValueError):
            minimum_destination_free_bytes(-1)

    def test_active_attention_profile_has_fresh_candidate_bound_paths(self) -> None:
        profile = ADAPTER_PROFILES["softmax-attention-only"]

        self.assertEqual(profile["expected_target_count"], 24)
        self.assertEqual(profile["expected_trainable_parameter_count"], 540_672)
        self.assertEqual(profile["preflight_job_id"], ATTENTION_PREFLIGHT_JOB_ID)
        self.assertIn("05-attention-only", str(profile["preflight_log_dir"]))
        self.assertTrue(FIT_JOB_ID.endswith("FIT-20260927-03-ATTN"))
        self.assertEqual(EXPECTED_FIT_OPTIMIZER_STEPS, 96)

    def test_mode_must_be_explicit_before_runtime_or_artifact_admission(self) -> None:
        argv = ["wrench-runner", "--storage-reservation-job-id", FIT_JOB_ID]
        runtime = patch("tools.train_gateway_lora_screen_02_gpu.enforce_runtime_bootstrap")
        with patch("sys.argv", argv), runtime as bootstrap, redirect_stderr(StringIO()), self.assertRaises(SystemExit) as raised:
            _run_main()

        self.assertEqual(raised.exception.code, 2)
        bootstrap.assert_not_called()

    def test_active_runner_rejects_historical_all_projection_profile(self) -> None:
        argv = [
            "wrench-runner", "--fit", "--adapter-profile", "all-projections",
            "--storage-reservation-job-id", FIT_JOB_ID,
        ]
        with patch("sys.argv", argv), redirect_stderr(StringIO()), self.assertRaises(SystemExit) as raised:
            _run_main()

        self.assertEqual(raised.exception.code, 2)

    def test_explicit_fit_mode_is_wired_to_runtime_admission(self) -> None:
        argv = ["wrench-runner", "--fit", "--storage-reservation-job-id", FIT_JOB_ID]
        with patch("sys.argv", argv), patch(
            "tools.train_gateway_lora_screen_02_gpu.enforce_runtime_bootstrap",
            side_effect=RuntimeError("test runtime sentinel"),
        ) as bootstrap, self.assertRaisesRegex(SystemExit, "runtime admission failed"):
            _run_main()

        bootstrap.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
