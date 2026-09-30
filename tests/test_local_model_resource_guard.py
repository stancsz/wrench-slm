import ast
import unittest
from pathlib import Path
from unittest.mock import patch

from examples.gateway_context_mvp import run_local_model_mvp


class _CriteriaBase:
    pass


class _CriteriaList(list):
    pass


class LocalModelResourceGuardTests(unittest.TestCase):
    def test_sampler_latches_ram_or_vram_floor_breach(self):
        sampler = run_local_model_mvp.ResourceSampler()
        low_ram = {
            "ram_free_fraction": 0.099,
            "vram_free_fraction": 0.80,
        }
        with patch.object(run_local_model_mvp, "sample_resources", return_value=low_ram):
            sampler.start()
            sampler.join(timeout=2)

        self.assertFalse(sampler.is_alive())
        self.assertEqual(sampler.error, "runtime_resource_floor_breached")
        self.assertTrue(sampler.floor_breached.is_set())
        self.assertTrue(run_local_model_mvp.resource_stop_requested(sampler))

    def test_transformers_stopping_criteria_checks_live_sampler_state(self):
        sampler = run_local_model_mvp.ResourceSampler()
        criteria = run_local_model_mvp.build_resource_stopping_criteria(
            sampler, _CriteriaBase, _CriteriaList
        )
        self.assertEqual(len(criteria), 1)
        stop = criteria[0]
        self.assertFalse(stop(None, None))

        sampler.floor_breached.set()
        self.assertTrue(stop(None, None))

    def test_sampler_error_also_stops_generation(self):
        sampler = run_local_model_mvp.ResourceSampler()
        sampler.error = "resource_sample_failed:TimeoutError"
        self.assertTrue(run_local_model_mvp.resource_stop_requested(sampler))

    def test_all_local_model_runners_wire_resource_stop_criteria(self):
        repo_root = Path(__file__).resolve().parents[1]
        runners = (
            "run_local_model_matrix.py",
            "run_local_model_budget_sweep.py",
            "run_paired_local_context_baseline.py",
        )
        for runner in runners:
            with self.subTest(runner=runner):
                path = repo_root / "examples" / "gateway_context_mvp" / runner
                tree = ast.parse(path.read_text(encoding="utf-8"))
                generate_calls = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "generate"
                ]
                self.assertTrue(generate_calls)
                self.assertTrue(
                    all(any(keyword.arg == "stopping_criteria" for keyword in node.keywords)
                        for node in generate_calls)
                )
                self.assertIn("build_resource_stopping_criteria", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
