from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace

from wrench_harness.opencode_request_capture import (
    CaptureError,
    MAX_PAIRED_EPISODES,
    MAX_REQUEST_BODY_BYTES,
    RequestArmEpisode,
    aggregate_paired_request_bytes,
    capture_opencode_request,
)


URL = "http://127.0.0.1:4000/v1/chat/completions"
VERSION = "2.0.12"


def _body(content: str, *, with_tools: bool = True, model_alias: str = "wrench-local") -> bytes:
    tool_field = (
        ',"tools":[{"type":"function","function":{"name":"read_file",'
        '"parameters":{"type":"object","properties":{"path":{"type":"string"}}}}}]'
        if with_tools
        else ""
    )
    escaped = content.replace("\\", "\\\\").replace('"', '\\"')
    return (
        f'{{"model":"{model_alias}","messages":[{{"role":"system","content":"rules"}},'
        f'{{"role":"user","content":"{escaped}"}}]{tool_field},"stream":true}}'
    ).encode("utf-8")


def _capture(
    pair_id: str,
    arm: str,
    request_id: str,
    content: str,
    attempt: int = 0,
    model_alias: str = "wrench-local",
):
    return capture_opencode_request(
        method="POST",
        url=URL,
        body=_body(content, model_alias=model_alias),
        opencode_version=VERSION,
        pair_id=pair_id,
        arm=arm,
        request_id=request_id,
        attempt_index=attempt,
    )


class OpenCodeRequestCaptureTests(unittest.TestCase):
    def test_records_exact_raw_body_digest_and_content_free_components(self):
        body = _body("PRIVATE_PROMPT_SENTINEL Ω")
        capture = capture_opencode_request(
            method="POST",
            url=URL,
            body=body,
            opencode_version=VERSION,
            pair_id="episode-1",
            arm="baseline",
            request_id="request-1",
            attempt_index=0,
        )
        self.assertEqual(capture.request_sha256, hashlib.sha256(body).hexdigest())
        self.assertEqual(capture.body_bytes, len(body))
        self.assertEqual(capture.message_count, 2)
        self.assertEqual(capture.role_counts, (("system", 1), ("user", 1)))
        self.assertEqual(capture.tool_schema_count, 1)
        self.assertIsNone(capture.input_tokens)
        self.assertIn("messages", {item.name for item in capture.fields})
        self.assertIn("tools", {item.name for item in capture.fields})
        self.assertEqual(
            capture.envelope_bytes + sum(item.raw_value_bytes for item in capture.fields),
            len(body),
        )
        self.assertNotIn("PRIVATE_PROMPT_SENTINEL", repr(capture))
        self.assertNotIn("Ω", repr(capture))

    def test_hashes_top_level_raw_values_including_tool_schema(self):
        body = b'{ "model" : "wrench-local", "messages" : [{"role":"user","content":"x"}], "tools" : [] }'
        capture = capture_opencode_request(
            method="POST",
            url="http://localhost:4000/v1/chat/completions",
            body=body,
            opencode_version=VERSION,
            pair_id="episode-1",
            arm="wrench",
            request_id="request-1",
            attempt_index=0,
        )
        fields = {item.name: item for item in capture.fields}
        self.assertEqual(fields["model"].sha256, hashlib.sha256(b'"wrench-local"').hexdigest())
        self.assertEqual(fields["tools"].sha256, hashlib.sha256(b"[]").hexdigest())

    def test_unknown_field_names_are_hashed_instead_of_retained(self):
        body = (
            b'{"model":"wrench-local","messages":[{"role":"user","content":"x"}],'
            b'"UNTRUSTED_FIELD_NAME_SENTINEL":"value"}'
        )
        capture = capture_opencode_request(
            method="POST",
            url=URL,
            body=body,
            opencode_version=VERSION,
            pair_id="episode-1",
            arm="wrench",
            request_id="request-1",
            attempt_index=0,
        )
        self.assertNotIn("UNTRUSTED_FIELD_NAME_SENTINEL", repr(capture))
        self.assertTrue(any(item.name.startswith("unknown_sha256_") for item in capture.fields))

    def test_rejects_wrong_route_version_shape_duplicate_keys_and_oversize(self):
        base = dict(
            method="POST",
            url=URL,
            body=_body("ok"),
            opencode_version=VERSION,
            pair_id="episode-1",
            arm="wrench",
            request_id="request-1",
            attempt_index=0,
        )
        for updates, reason in (
            ({"url": "http://127.0.0.1:4001/v1/chat/completions"}, "route_unsupported"),
            ({"opencode_version": "2.0.14"}, "opencode_version_unsupported"),
            ({"body": b'{"model":"a","model":"b","messages":[]}'}, "request_json_invalid"),
            ({"body": _body("x").replace(b'"role":"user"', b'"role":"user","role":"tool"')}, "request_json_invalid"),
            ({"body": _body("x")[0:0] + b" " * (MAX_REQUEST_BODY_BYTES + 1)}, "request_body_size_invalid"),
            ({"body": b'{"model":"x","messages":[{"role":"bogus"}]}'}, "message_shape_unsupported"),
        ):
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(CaptureError, reason):
                    capture_opencode_request(**(base | updates))

    def test_paired_aggregate_counts_retries_and_zero_request_episode(self):
        baseline_one = _capture("pair-1", "baseline", "b1", "large baseline context " * 4, 0)
        baseline_retry = _capture("pair-1", "baseline", "b2", "retry context " * 3, 1)
        wrench_one = _capture("pair-1", "wrench", "w1", "selected evidence", 0)
        baseline_two = _capture("pair-2", "baseline", "b3", "second full context", 0)
        result = aggregate_paired_request_bytes((
            RequestArmEpisode("pair-1", "baseline", (baseline_one, baseline_retry), True),
            RequestArmEpisode("pair-1", "wrench", (wrench_one,), True),
            RequestArmEpisode("pair-2", "baseline", (baseline_two,), True),
            RequestArmEpisode("pair-2", "wrench", (), True),
        ))
        expected_baseline = baseline_one.body_bytes + baseline_retry.body_bytes + baseline_two.body_bytes
        expected_wrench = wrench_one.body_bytes
        self.assertEqual(result.pair_count, 2)
        self.assertEqual(result.baseline_request_count, 3)
        self.assertEqual(result.wrench_request_count, 1)
        self.assertEqual(result.wrench_zero_request_episodes, 1)
        self.assertEqual(result.baseline_body_bytes, expected_baseline)
        self.assertEqual(result.wrench_body_bytes, expected_wrench)
        self.assertGreater(result.retained_receipt_metadata_bytes, 0)
        self.assertAlmostEqual(
            result.body_byte_reduction_fraction,
            (expected_baseline - expected_wrench) / expected_baseline,
        )
        self.assertFalse(result.body_byte_reduction_is_token_reduction)
        self.assertIsNone(result.input_token_reduction_fraction)
        self.assertIsNone(result.frontier_success_retention)
        self.assertIsNone(result.all_in_cost_reduction_fraction)
        self.assertIsNone(result.task_success_rates)

    def test_aggregate_rejects_mixed_aliases_and_excessive_episode_count(self):
        pair_one_baseline = _capture("pair-1", "baseline", "b1", "base", model_alias="route-a")
        pair_one_wrench = _capture("pair-1", "wrench", "w1", "small", model_alias="route-a")
        pair_two_baseline = _capture("pair-2", "baseline", "b2", "base", model_alias="route-b")
        pair_two_wrench = _capture("pair-2", "wrench", "w2", "small", model_alias="route-b")
        with self.assertRaisesRegex(CaptureError, "model_alias_mixed_or_missing"):
            aggregate_paired_request_bytes((
                RequestArmEpisode("pair-1", "baseline", (pair_one_baseline,), True),
                RequestArmEpisode("pair-1", "wrench", (pair_one_wrench,), True),
                RequestArmEpisode("pair-2", "baseline", (pair_two_baseline,), True),
                RequestArmEpisode("pair-2", "wrench", (pair_two_wrench,), True),
            ))
        with self.assertRaisesRegex(CaptureError, "paired_episode_limit_exceeded"):
            aggregate_paired_request_bytes(tuple(None for _ in range(MAX_PAIRED_EPISODES + 1)))

    def test_aggregate_rejects_attempt_index_gaps_and_duplicates(self):
        wrench = _capture("pair-1", "wrench", "w1", "selected")
        cases = (
            (
                (_capture("pair-1", "baseline", "b1", "first", 0),
                 _capture("pair-1", "baseline", "b3", "third", 2)),
                "gap",
            ),
            (
                (_capture("pair-1", "baseline", "b1", "first", 0),
                 _capture("pair-1", "baseline", "b2", "duplicate", 0)),
                "duplicate",
            ),
        )
        for baseline_captures, label in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(CaptureError, "request_attempt_indices_not_contiguous"):
                    aggregate_paired_request_bytes((
                        RequestArmEpisode("pair-1", "baseline", baseline_captures, True),
                        RequestArmEpisode("pair-1", "wrench", (wrench,), True),
                    ))

    def test_rejects_incomplete_mismatched_tampered_and_unpaired_receipts(self):
        baseline = _capture("pair-1", "baseline", "b1", "baseline")
        wrench = _capture("pair-1", "wrench", "w1", "selected")
        valid_pair = (
            RequestArmEpisode("pair-1", "baseline", (baseline,), True),
            RequestArmEpisode("pair-1", "wrench", (wrench,), True),
        )
        with self.assertRaisesRegex(CaptureError, "capture_incomplete"):
            aggregate_paired_request_bytes((
                valid_pair[0],
                replace(valid_pair[1], capture_complete=False),
            ))
        with self.assertRaisesRegex(CaptureError, "capture_integrity_mismatch"):
            aggregate_paired_request_bytes((
                valid_pair[0],
                replace(valid_pair[1], captures=(replace(wrench, body_bytes=wrench.body_bytes + 1),)),
            ))
        other_route = replace(wrench, route_identity="http://127.0.0.1:4001/v1/chat/completions")
        with self.assertRaisesRegex(CaptureError, "capture_contract_invalid"):
            aggregate_paired_request_bytes((valid_pair[0], replace(valid_pair[1], captures=(other_route,))))
        with self.assertRaisesRegex(CaptureError, "paired_arm_missing"):
            aggregate_paired_request_bytes((valid_pair[0],))


if __name__ == "__main__":
    unittest.main()
