import json
import hashlib
import unittest
from dataclasses import replace

from wrench_harness.frontier_usage import (
    UsageArmEpisode,
    UsageCaptureError,
    aggregate_paired_frontier_usage,
    capture_openai_compatible_usage,
)


def _receipt(
    pair_id,
    arm,
    request_id,
    attempt_index,
    input_tokens,
    output_tokens,
    cached=0,
    response_model="frontier-test-model",
    episode_manifest_sha256=None,
):
    if episode_manifest_sha256 is None:
        episode_manifest_sha256 = hashlib.sha256(f"episode:{pair_id}".encode()).hexdigest()
    payload = {
        "id": f"provider-{request_id}",
        "model": response_model,
        "choices": [{"message": {"content": "SYNTHETIC_RESPONSE_BODY_SENTINEL"}}],
        "usage": {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "prompt_tokens_details": {"cached_tokens": cached},
        },
    }
    return capture_openai_compatible_usage(
        response_body=json.dumps(payload).encode("utf-8"),
        http_status=200,
        pair_id=pair_id,
        arm=arm,
        episode_manifest_sha256=episode_manifest_sha256,
        request_id=request_id,
        attempt_index=attempt_index,
        provider_route="synthetic-frontier-route",
    )


class FrontierUsageTests(unittest.TestCase):
    def test_aggregates_paired_usage_retries_cached_subset_and_zero_frontier_arm(self):
        baseline_first = _receipt("p1", "baseline", "b1", 0, 1000, 100, 400)
        baseline_retry = _receipt("p1", "baseline", "b2", 1, 200, 50, 0)
        wrench_first = _receipt("p1", "wrench", "w1", 0, 100, 20, 25)
        baseline_second = _receipt("p2", "baseline", "b3", 0, 800, 100, 100)
        result = aggregate_paired_frontier_usage((
            UsageArmEpisode("p1", baseline_first.episode_manifest_sha256, "baseline", (baseline_first, baseline_retry), True),
            UsageArmEpisode("p1", wrench_first.episode_manifest_sha256, "wrench", (wrench_first,), True),
            UsageArmEpisode("p2", baseline_second.episode_manifest_sha256, "baseline", (baseline_second,), True),
            UsageArmEpisode("p2", hashlib.sha256(b"episode:p2").hexdigest(), "wrench", (), True),
        ))
        self.assertEqual(result.pair_count, 2)
        self.assertEqual(result.response_model, "frontier-test-model")
        self.assertEqual(result.baseline_request_count, 3)
        self.assertEqual(result.wrench_request_count, 1)
        self.assertEqual(result.wrench_frontier_episode_count, 1)
        self.assertEqual(result.baseline_total_tokens, 2250)
        self.assertEqual(result.wrench_total_tokens, 120)
        self.assertAlmostEqual(result.reported_token_reduction_fraction, 1 - 120 / 2250)
        self.assertEqual(result.baseline_cached_input_tokens, 500)
        self.assertFalse(result.response_usage_is_billing_verified)

    def test_mixed_upstream_models_under_same_route_fail_closed(self):
        baseline = _receipt("p", "baseline", "b", 0, 100, 10)
        wrench = _receipt("p", "wrench", "w", 0, 10, 2, response_model="other-model")
        with self.assertRaisesRegex(UsageCaptureError, "response_model_mixed_or_missing"):
            aggregate_paired_frontier_usage((
                UsageArmEpisode("p", baseline.episode_manifest_sha256, "baseline", (baseline,), True),
                UsageArmEpisode("p", wrench.episode_manifest_sha256, "wrench", (wrench,), True),
            ))

    def test_same_pair_id_with_different_frozen_episode_manifests_fails_closed(self):
        baseline_hash = hashlib.sha256(b"frozen task and fixture manifest A").hexdigest()
        wrench_hash = hashlib.sha256(b"frozen task and fixture manifest B").hexdigest()
        baseline = _receipt(
            "p", "baseline", "b", 0, 100, 10,
            episode_manifest_sha256=baseline_hash,
        )
        wrench = _receipt(
            "p", "wrench", "w", 0, 10, 2,
            episode_manifest_sha256=wrench_hash,
        )
        with self.assertRaisesRegex(UsageCaptureError, "paired_episode_identity_mismatch"):
            aggregate_paired_frontier_usage((
                UsageArmEpisode("p", baseline_hash, "baseline", (baseline,), True),
                UsageArmEpisode("p", wrench_hash, "wrench", (wrench,), True),
            ))

    def test_episode_manifest_digest_is_receipt_bound(self):
        receipt = _receipt("p", "baseline", "b", 0, 10, 2)
        tampered = replace(
            receipt,
            episode_manifest_sha256=hashlib.sha256(b"different task").hexdigest(),
        )
        with self.assertRaisesRegex(UsageCaptureError, "receipt_integrity_mismatch"):
            aggregate_paired_frontier_usage((
                UsageArmEpisode("p", tampered.episode_manifest_sha256, "baseline", (tampered,), True),
                UsageArmEpisode("p", tampered.episode_manifest_sha256, "wrench", (), True),
            ))

    def test_missing_usage_is_unmeasured_not_zero(self):
        payload = json.dumps({"model": "frontier-test-model", "choices": []}).encode()
        with self.assertRaisesRegex(UsageCaptureError, "provider_usage_missing"):
            capture_openai_compatible_usage(
                response_body=payload, http_status=200, pair_id="p", arm="baseline",
                episode_manifest_sha256=hashlib.sha256(b"episode:p").hexdigest(),
                request_id="r", attempt_index=0, provider_route="synthetic-route",
            )

    def test_invalid_cached_or_total_count_is_rejected(self):
        for usage, reason in (
            ({"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6,
              "prompt_tokens_details": {"cached_tokens": 6}}, "cached_tokens_exceed_input"),
            ({"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 99}, "total_tokens_mismatch"),
            ({"prompt_tokens": True, "completion_tokens": 1}, "prompt_tokens_invalid"),
        ):
            with self.subTest(reason=reason):
                body = json.dumps({"model": "m", "usage": usage}).encode()
                with self.assertRaisesRegex(UsageCaptureError, reason):
                    capture_openai_compatible_usage(
                        response_body=body, http_status=200, pair_id="p", arm="baseline",
                        episode_manifest_sha256=hashlib.sha256(b"episode:p").hexdigest(),
                        request_id="r", attempt_index=0, provider_route="route",
                    )

    def test_incomplete_pair_and_attempt_gap_fail_closed(self):
        base = _receipt("p", "baseline", "b", 0, 10, 2)
        with self.assertRaisesRegex(UsageCaptureError, "unpaired_episode"):
            aggregate_paired_frontier_usage((UsageArmEpisode("p", base.episode_manifest_sha256, "baseline", (base,), True),))
        retry_gap = _receipt("p", "baseline", "b2", 2, 1, 1)
        with self.assertRaisesRegex(UsageCaptureError, "attempt_indexes_not_contiguous"):
            aggregate_paired_frontier_usage((
                UsageArmEpisode("p", base.episode_manifest_sha256, "baseline", (base, retry_gap), True),
                UsageArmEpisode("p", base.episode_manifest_sha256, "wrench", (), True),
            ))

    def test_receipt_does_not_retain_response_text(self):
        receipt = _receipt("p", "baseline", "b", 0, 10, 2)
        self.assertNotIn("SYNTHETIC_RESPONSE_BODY_SENTINEL", repr(receipt))

    def test_tampered_count_fails_receipt_integrity(self):
        receipt = _receipt("p", "baseline", "b", 0, 10, 2)
        tampered = replace(receipt, input_tokens=999)
        with self.assertRaisesRegex(UsageCaptureError, "receipt_integrity_mismatch"):
            aggregate_paired_frontier_usage((
                UsageArmEpisode("p", tampered.episode_manifest_sha256, "baseline", (tampered,), True),
                UsageArmEpisode("p", tampered.episode_manifest_sha256, "wrench", (), True),
            ))


if __name__ == "__main__":
    unittest.main()
