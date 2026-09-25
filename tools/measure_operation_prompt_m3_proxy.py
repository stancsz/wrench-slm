"""Measure offline M3-tokenizer prompt-input reduction on explicit operations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

TOKENIZER_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-local-acceptability\minimax-m3-tokenizer-f0e1c1e")
TOKENIZER_DIR = TOKENIZER_ROOT / "tokenizer"
ASSET_INVENTORY = TOKENIZER_ROOT / "source_inventory.json"
ASSET_RECEIPT = TOKENIZER_ROOT / "fetch_receipt.json"
RUNTIME_LOCK = ROOT / "tools" / "wrench-local-runtime-windows-cp313.lock"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "e0_synthetic_matched_tasks_v1"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
SIDECAR_PATH = FIXTURE_DIR / "manifest.sha256"
REVIEW_PATH = ROOT / "docs" / "evals" / "wrench-e0-synthetic-matched-tasks" / "review.md"
ARTIFACT_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-local-acceptability")
TMP_ROOT = ARTIFACT_ROOT / "tmp"

JOB_ID = "LOCAL-M3-OPS-PROXY-20260925-02"
NONCE = "M3OP02-A42C"
SCHEMA = "wrench.synthetic-operation-m3-input-proxy.v1"
MODEL_REVISION = "f0e1c1e04d40177e4673a22097036854f536e9c0"
EXPECTED_MANIFEST_SHA256 = "871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5"
EXPECTED_INVENTORY_SHA256 = "86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c"
EXPECTED_LOCK_SHA256 = "0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420"
EXPECTED_TEMPLATE_SHA256 = "11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64"
EXPECTED_SELECTED_ASSETS = {
    "LICENSE": (3339, "b53f2fdda3049b0e9013207be51efc2d372cda1fcfdd8bb4bb8b22658ca5db9c"),
    "added_tokens.json": (1660, "63f277741fb061e615cb604286a845d971178ba4716732a59cf42b3752c0ce4e"),
    "chat_template.jinja": (11756, EXPECTED_TEMPLATE_SHA256),
    "config.json": (5254, "c9c97ce1e4eece60012d5a10ea87717458bfb1f19c2c7a615a3dbff83d090c6b"),
    "merges.txt": (2414077, "ca47ea60cf5bd48832586adc264f439d0ea4254176b24a95f85eaa9750e2b5f9"),
    "special_tokens_map.json": (277, "401b624ec44507183d1dc65c74f7f3387699a77971aa19fa5a0cc57a3989ba97"),
    "tokenizer.json": (9731500, "bb1f1626cf01448f1e3b6036d0a061ffc66c91d9046aada14ea23a5441b5ad6e"),
    "tokenizer_config.json": (11288, "15caca9f74fbce9b86dc014e9324cbefa56703d81ccd6d56020faa1c41d2eae5"),
    "vocab.json": (4705413, "b44c066b5dc34c800c4e3ecbd85f3e95ce3bfdbf8a5fe30223e005175103578a"),
}
CASE_IDS = ("loc-a", "loc-b", "triage-a", "triage-b", "context-a", "context-b", "evidence-specific")
SYSTEM_MESSAGE = (
    "Use only the supplied repository context to perform the user's explicit, "
    "bounded read or search request. Do not invent source facts."
)

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_context_pipeline import PreparationStatus, _evidence_id
from wrench_harness.e0_route_preparation import RoutePreparationStatus, route_and_prepare_e0_context
from wrench_harness.namespace_registry import NamespaceRegistry
from wrench_harness.prompt_compiler import _render_untrusted_context, materialize_prompt_messages
from wrench_harness.snapshot import bind_source_root, create_snapshot
from wrench_harness.synthetic_fixture_admission import validate_synthetic_fixture_admission


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _token_ids(encoded: object) -> list[int]:
    if isinstance(encoded, Mapping):
        if "input_ids" not in encoded:
            raise ValueError("tokenizer_output_missing_input_ids")
        encoded = encoded["input_ids"]
    if hasattr(encoded, "tolist"):
        encoded = encoded.tolist()
    if isinstance(encoded, tuple):
        encoded = list(encoded)
    if type(encoded) is not list:
        raise ValueError("tokenizer_input_ids_not_a_list")
    if encoded and type(encoded[0]) is list:
        if len(encoded) != 1:
            raise ValueError("tokenizer_returned_multiple_conversations")
        encoded = encoded[0]
    if any(type(token) is not int for token in encoded):
        raise ValueError("tokenizer_input_ids_not_integer_sequence")
    return encoded


def _load_and_verify_tokenizer():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HOME"] = str(Path(r"C:\wrench-slm-data\cache\huggingface"))
    os.environ["TORCH_HOME"] = str(Path(r"C:\wrench-slm-data\cache\torch"))
    inventory_bytes = ASSET_INVENTORY.read_bytes()
    if _sha256(inventory_bytes) != EXPECTED_INVENTORY_SHA256:
        raise ValueError("pinned_tokenizer_inventory_hash_mismatch")
    inventory = json.loads(inventory_bytes)
    receipt = json.loads(ASSET_RECEIPT.read_text(encoding="utf-8"))
    if (
        inventory.get("repository") != "MiniMaxAI/MiniMax-M3"
        or inventory.get("revision") != MODEL_REVISION
        or inventory.get("model_weights_downloaded") is not False
        or receipt.get("repository") != "MiniMaxAI/MiniMax-M3"
        or receipt.get("revision") != MODEL_REVISION
        or receipt.get("source_inventory_sha256") != EXPECTED_INVENTORY_SHA256
        or receipt.get("model_weights_downloaded") is not False
    ):
        raise ValueError("pinned_tokenizer_fetch_identity_mismatch")
    if _file_sha256(RUNTIME_LOCK) != EXPECTED_LOCK_SHA256:
        raise ValueError("runtime_lock_hash_mismatch")
    recorded_assets = {
        row["path"]: row["size_bytes"]
        for row in inventory["files"]
        if row["path"] in EXPECTED_SELECTED_ASSETS
    }
    if set(recorded_assets) != set(EXPECTED_SELECTED_ASSETS):
        raise ValueError("selected_tokenizer_inventory_set_mismatch")
    actual_assets: dict[str, dict[str, object]] = {}
    for name, (expected_size, expected_hash) in EXPECTED_SELECTED_ASSETS.items():
        path = TOKENIZER_ROOT / name if name == "LICENSE" else TOKENIZER_DIR / name
        actual_size = path.stat().st_size
        actual_hash = _file_sha256(path)
        if (actual_size, actual_hash) != (expected_size, expected_hash) or recorded_assets[name] != expected_size:
            raise ValueError("tokenizer_asset_identity_mismatch:" + name)
        actual_assets[name] = {"size_bytes": actual_size, "sha256": actual_hash}
    if sum(item["size_bytes"] for item in actual_assets.values()) != 16_884_564:
        raise ValueError("tokenizer_asset_total_size_mismatch")
    if set(path.name for path in TOKENIZER_DIR.iterdir() if path.is_file()) != set(EXPECTED_SELECTED_ASSETS) - {"LICENSE"}:
        raise ValueError("unexpected_tokenizer_directory_files")

    if sys.version_info[:3] != (3, 13, 15):
        raise ValueError("python_runtime_version_mismatch")
    versions = {
        "transformers": importlib.metadata.version("transformers"),
        "tokenizers": importlib.metadata.version("tokenizers"),
        "huggingface_hub": importlib.metadata.version("huggingface-hub"),
    }
    if versions != {"transformers": "5.17.0", "tokenizers": "0.23.2", "huggingface_hub": "1.33.0"}:
        raise ValueError("tokenizer_runtime_package_version_mismatch")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(TOKENIZER_DIR), local_files_only=True, trust_remote_code=False, use_fast=True
    )
    template = tokenizer.chat_template
    if type(template) is not str or _sha256(template.encode("utf-8")) != EXPECTED_TEMPLATE_SHA256:
        raise ValueError("loaded_chat_template_hash_mismatch")
    return tokenizer, versions, actual_assets, _sha256(template.encode("utf-8"))


def _count_template_ids(tokenizer, messages: list[dict[str, object]]) -> int:
    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    return len(_token_ids(encoded))


def _render_template(tokenizer, messages: list[dict[str, object]]) -> str:
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    if type(rendered) is not str:
        raise ValueError("chat_template_render_not_text")
    return rendered


def _fixture() -> tuple[dict[str, Any], str, dict[str, dict[str, Any]]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sidecar_digest, sidecar_name = SIDECAR_PATH.read_text(encoding="ascii").split()
    if sidecar_name != MANIFEST_PATH.name or _sha256(_canonical_bytes(manifest)) != sidecar_digest:
        raise ValueError("synthetic_fixture_manifest_identity_mismatch")
    if sidecar_digest != EXPECTED_MANIFEST_SHA256:
        raise ValueError("synthetic_fixture_protocol_hash_mismatch")
    review = manifest["admission"]["review"]
    if review["receipt_path"] != "docs/evals/wrench-e0-synthetic-matched-tasks/review.md":
        raise ValueError("synthetic_fixture_review_path_changed")
    admission = validate_synthetic_fixture_admission(
        manifest,
        manifest_sha256=sidecar_digest,
        requested_usage="open_development_fixture_only",
        review_receipt_path=review["receipt_path"],
        review_receipt_bytes=REVIEW_PATH.read_bytes(),
    )
    if not admission.admitted:
        raise ValueError("synthetic_fixture_admission_rejected:" + str(admission.reason))
    cases = {
        case["case_id"]: {"group": pair["group"], "pair_id": pair["pair_id"], **case}
        for pair in manifest["pairs"]
        for case in pair["cases"]
        if case.get("case_id") in CASE_IDS
    }
    if set(cases) != set(CASE_IDS):
        raise ValueError("synthetic_operation_case_set_mismatch")
    return manifest, sidecar_digest, cases


def _prepare_case(root: Path, case: dict[str, Any]):
    for source in case["files"]:
        data = source["content_utf8"].encode("utf-8")
        if _sha256(data) != source["sha256"]:
            raise ValueError("fixture_source_hash_mismatch")
        path = root.joinpath(*source["path"].split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    binding = bind_source_root(root)
    paths = tuple(source["path"] for source in case["files"])
    snapshot = create_snapshot(binding, paths)
    return binding, snapshot


def _baseline_message(files: list[dict[str, Any]], snapshot_sha256: str) -> dict[str, object]:
    sections: list[str] = []
    for source in sorted(files, key=lambda item: item["path"]):
        content = source["content_utf8"]
        digest = source["sha256"]
        evidence_id = _evidence_id(snapshot_sha256, source["path"], digest)
        sections.append(f"[context:{evidence_id}]\nPath: {source['path']}\n{content}")
    assembled = "\n\n".join(sections)
    return {"role": "user", "content": _render_untrusted_context(assembled)}


def _message_list(base_messages: tuple[dict[str, object], ...], context: dict[str, object]) -> list[dict[str, object]]:
    messages = [dict(message) for message in base_messages]
    messages.insert(1, dict(context))
    return messages


def _source_ids_match(route, preparation) -> bool:
    route_sources = {row.path: row.content_sha256 for row in route.evidence if row.status == "ok"}
    prepared_sources = {row.path: row.content_sha256 for row in preparation.sources if row.status == "ok"}
    return bool(route_sources) and route_sources == prepared_sources


def _route_matches_operation_oracle(case: dict[str, Any], route) -> bool:
    mechanics = case["expected_mechanics"]
    if route.status.value != mechanics["status"] or route.action != mechanics["action"]:
        return False
    expected = mechanics["observation"]
    actual = route.observation
    if type(actual) is not dict:
        return False
    for key, value in expected.items():
        if actual.get(key) != value:
            return False
    if mechanics["action"] == "read_file":
        source = next((row for row in case["files"] if row["path"] == expected["path"]), None)
        return source is not None and actual.get("bytes") == len(source["content_utf8"].encode("utf-8"))
    return True


def _untrusted_payload(context_message_content: str) -> str:
    begin = "BEGIN UNTRUSTED SOURCE JSON STRING\n"
    end = "\nEND UNTRUSTED SOURCE JSON STRING"
    if context_message_content.count(begin) != 1 or context_message_content.count(end) != 1:
        raise ValueError("untrusted_context_wrapper_markers_invalid")
    payload_start = context_message_content.index(begin) + len(begin)
    payload_end = context_message_content.index(end, payload_start)
    payload = json.loads(context_message_content[payload_start:payload_end])
    if type(payload) is not str:
        raise ValueError("untrusted_context_payload_not_text")
    return payload


def _oracle_context_complete(case: dict[str, Any], prompt: str, content: str, route) -> tuple[bool, str | None]:
    assembled_context = _untrusted_payload(content)
    oracle = case["expected_mechanics"]["observation"]
    if case["expected_mechanics"]["action"] == "read_file":
        path = oracle["path"]
        source = next((row for row in case["files"] if row["path"] == path), None)
        if source is None or path not in prompt or source["content_utf8"] not in assembled_context:
            return False, "required_path_or_exact_source_not_visible"
        return True, None

    matches = oracle["matches"]
    if matches:
        for match in matches:
            if match["path"] not in prompt and match["path"] not in assembled_context:
                return False, "matched_source_path_not_visible"
            if match["text"] not in assembled_context:
                return False, "matched_source_quote_not_visible"
        return True, None

    # A bounded empty result is supported only if every exact source in the
    # search root was carried through route evidence into the context message.
    scoped = [row for row in case["files"] if row["path"].startswith(oracle["root"].rstrip("/") + "/")]
    for source in scoped:
        if source["content_utf8"] not in assembled_context:
            return False, "empty_search_scope_source_not_visible"
    if len(route.evidence) != len(scoped) or not scoped:
        return False, "empty_search_scope_evidence_incomplete"
    return True, None


def _git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def _worktree_dirty() -> bool:
    output = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return bool(output.strip())


def _measure_case(case: dict[str, Any], tokenizer, scratch: Path) -> dict[str, object]:
    case_id = case["case_id"]
    case_root = scratch / ("source-" + case_id)
    case_root.mkdir()
    binding, snapshot = _prepare_case(case_root, case)
    prompt = case["prompt"]
    base_messages = (
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": prompt},
    )
    baseline_message = _baseline_message(case["files"], snapshot.snapshot_sha256)
    baseline_messages = _message_list(base_messages, baseline_message)
    baseline_tokens = _count_template_ids(tokenizer, baseline_messages)
    baseline_rendered = _render_template(tokenizer, baseline_messages)
    if _count_template_ids(tokenizer, baseline_messages) != len(_token_ids(tokenizer(baseline_rendered, add_special_tokens=False)["input_ids"])):
        raise ValueError("baseline_chat_template_tokenization_parity_failed")

    def serializer(messages):
        return _render_template(tokenizer, materialize_prompt_messages(messages))

    def counter(rendered):
        if type(rendered) is not str:
            raise TypeError("serializer_must_return_rendered_text")
        return len(_token_ids(tokenizer(rendered, add_special_tokens=False)["input_ids"]))

    result = route_and_prepare_e0_context(
        prompt,
        root_binding=binding,
        snapshot=snapshot,
        store=ArtifactStore(scratch / ("store-" + case_id)),
        query=prompt,
        source_order_start=1,
        context_token_budget=8192,
        prompt_token_budget=8192,
        namespace_registry=NamespaceRegistry([]),
        schema_lookups=(),
        base_messages=base_messages,
        context_position=1,
        message_format="generic",
        serializer=serializer,
        tokenizer_counter=counter,
        serializer_id="minimax-m3-chat-template-v1:" + EXPECTED_TEMPLATE_SHA256,
        tokenizer_id="MiniMaxAI/MiniMax-M3@" + MODEL_REVISION,
    )
    if result.status is not RoutePreparationStatus.JOINED or result.preparation is None:
        return {
            "case_id": case_id,
            "pair_id": case["pair_id"],
            "baseline_input_tokens": baseline_tokens,
            "wrench_input_tokens": None,
            "reduction_percent": None,
            "eligibility": "excluded",
            "exclusion_reason": "route_preparation_" + result.status.value,
            "route_status": result.route_result.status.value,
            "route_action": result.route_result.action,
            "preparation_status": None,
            "prompt_digest_sha256": _sha256(_canonical_bytes(base_messages)),
        }
    if not _route_matches_operation_oracle(case, result.route_result):
        raise ValueError("route_result_does_not_match_frozen_operation_oracle")
    prep = result.preparation
    if prep.status is not PreparationStatus.READY or prep.context_message_json is None:
        return {
            "case_id": case_id,
            "pair_id": case["pair_id"],
            "baseline_input_tokens": baseline_tokens,
            "wrench_input_tokens": None,
            "reduction_percent": None,
            "eligibility": "excluded",
            "exclusion_reason": "preparation_" + prep.status.value,
            "route_status": result.route_result.status.value,
            "route_action": result.route_result.action,
            "preparation_status": prep.status.value,
            "prompt_digest_sha256": _sha256(_canonical_bytes(base_messages)),
        }
    if not _source_ids_match(result.route_result, prep):
        raise ValueError("route_preparation_source_identity_mismatch")
    context = json.loads(prep.context_message_json)
    if type(context) is not dict or context.get("role") != "user" or type(context.get("content")) is not str:
        raise ValueError("wrench_context_message_shape_invalid")
    wrench_messages = _message_list(base_messages, context)
    if [message for idx, message in enumerate(wrench_messages) if idx != 1] != list(base_messages):
        raise ValueError("wrench_noncontext_messages_changed")
    if [message for idx, message in enumerate(baseline_messages) if idx != 1] != list(base_messages):
        raise ValueError("baseline_noncontext_messages_changed")
    wrench_tokens = _count_template_ids(tokenizer, wrench_messages)
    wrench_rendered = _render_template(tokenizer, wrench_messages)
    serialized_counter_tokens = len(_token_ids(tokenizer(wrench_rendered, add_special_tokens=False)["input_ids"]))
    gate_tokens = prep.prompt_gate.exact_token_count
    if serialized_counter_tokens != wrench_tokens or gate_tokens != wrench_tokens:
        raise ValueError("wrench_prompt_gate_token_count_mismatch")
    context_content = context["content"]
    evidence_complete, exclusion_reason = _oracle_context_complete(
        case, prompt, context_content, result.route_result
    )
    eligible = evidence_complete and baseline_tokens > 0 and wrench_tokens > 0
    reduction = 100.0 * (1.0 - wrench_tokens / baseline_tokens) if eligible else None
    return {
        "case_id": case_id,
        "pair_id": case["pair_id"],
        "baseline_input_tokens": baseline_tokens,
        "wrench_input_tokens": wrench_tokens,
        "reduction_percent": reduction,
        "eligibility": "eligible" if eligible else "excluded",
        "exclusion_reason": exclusion_reason if not eligible else None,
        "route_status": result.route_result.status.value,
        "route_action": result.route_result.action,
        "preparation_status": prep.status.value,
        "baseline_prompt_sha256": _sha256(baseline_rendered.encode("utf-8")),
        "wrench_prompt_sha256": _sha256(wrench_rendered.encode("utf-8")),
        "prompt_digest_sha256": _sha256(_canonical_bytes(base_messages)),
        "baseline_snapshot_file_count": len(case["files"]),
        "baseline_snapshot_bytes": sum(len(item["content_utf8"].encode("utf-8")) for item in case["files"]),
    }


def _summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    eligible = [row for row in rows if row["eligibility"] == "eligible"]
    if not eligible:
        return {
            "eligible_count": 0,
            "excluded_count": len(rows),
            "mean_per_task_reduction_percent": None,
            "ratio_of_sums_reduction_percent": None,
            "baseline_input_tokens_sum": None,
            "wrench_input_tokens_sum": None,
        }
    baseline_sum = sum(int(row["baseline_input_tokens"]) for row in eligible)
    wrench_sum = sum(int(row["wrench_input_tokens"]) for row in eligible)
    percentages = [float(row["reduction_percent"]) for row in eligible]
    return {
        "eligible_count": len(eligible),
        "excluded_count": len(rows) - len(eligible),
        "mean_per_task_reduction_percent": sum(percentages) / len(percentages),
        "ratio_of_sums_reduction_percent": 100.0 * (1.0 - wrench_sum / baseline_sum) if baseline_sum else None,
        "baseline_input_tokens_sum": baseline_sum,
        "wrench_input_tokens_sum": wrench_sum,
    }


def measure(output: Path) -> dict[str, object]:
    output = output.resolve()
    try:
        output.relative_to(ARTIFACT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("receipt_must_be_under_approved_artifact_root") from exc
    if output.exists():
        raise FileExistsError("refusing_to_overwrite_existing_receipt")
    manifest, manifest_digest, cases = _fixture()
    if sys.executable.lower() != str(Path(r"C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe")).lower():
        raise ValueError("unexpected_python_executable")
    tokenizer, runtime_versions, tokenizer_assets, template_digest = _load_and_verify_tokenizer()
    runner_path = Path(__file__).resolve()
    source_paths = (
        runner_path,
        ROOT / "src" / "wrench_harness" / "e0_route_preparation.py",
        ROOT / "src" / "wrench_harness" / "e0_rule_route.py",
        ROOT / "src" / "wrench_harness" / "e0_context_pipeline.py",
        ROOT / "src" / "wrench_harness" / "prompt_compiler.py",
        ROOT / "src" / "wrench_harness" / "context.py",
        ROOT / "src" / "wrench_harness" / "artifact_store.py",
        ROOT / "src" / "wrench_harness" / "snapshot.py",
        ROOT / "src" / "wrench_harness" / "mechanical.py",
        MANIFEST_PATH,
        REVIEW_PATH,
        RUNTIME_LOCK,
    )
    source_hashes = {path.relative_to(ROOT).as_posix(): _file_sha256(path) for path in source_paths if path.is_relative_to(ROOT)}
    started = time.perf_counter_ns()
    rows: list[dict[str, object]] = []
    output.parent.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="m3-operation-proxy-02-", dir=TMP_ROOT) as scratch_name:
        scratch = Path(scratch_name)
        for case_id in CASE_IDS:
            rows.append(_measure_case(cases[case_id], tokenizer, scratch))
    pair_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        pair_groups[str(row["pair_id"])].append(row)
    pair_summaries = {key: _summarize(value) for key, value in sorted(pair_groups.items())}
    total_summary = _summarize(rows)
    report: dict[str, object] = {
        "schema": SCHEMA,
        "job_id": JOB_ID,
        "nonce": NONCE,
        "status": "complete",
        "claim_scope": "synthetic_m3_tokenizer_prompt_input_reduction_only",
        "repo_head": _git_head(),
        "worktree_was_dirty": _worktree_dirty(),
        "fixture_manifest_sha256": manifest_digest,
        "fixture_review_receipt_sha256": manifest["admission"]["review"]["receipt_sha256"],
        "runner_sha256": _file_sha256(runner_path),
        "measured_source_sha256": source_hashes,
        "tokenizer_repository": "MiniMaxAI/MiniMax-M3",
        "tokenizer_revision": MODEL_REVISION,
        "tokenizer_inventory_sha256": EXPECTED_INVENTORY_SHA256,
        "tokenizer_assets": tokenizer_assets,
        "tokenizer_template_sha256": template_digest,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_is_fast": bool(getattr(tokenizer, "is_fast", False)),
        "runtime_python": platform.python_version(),
        "runtime_executable": sys.executable,
        "runtime_package_versions": runtime_versions,
        "runtime_lock_sha256": EXPECTED_LOCK_SHA256,
        "generation_prefix_included": True,
        "generated_tokens_counted": False,
        "token_ids_persisted": False,
        "rendered_prompts_persisted": False,
        "frontier_token_savings_percent": None,
        "frontier_usage_pairs": 0,
        "frontier_calls": 0,
        "case_count": len(rows),
        "total": total_summary,
        "pair_summaries": pair_summaries,
        "cases": rows,
        "elapsed_ns": time.perf_counter_ns() - started,
        "note": "Tiny open-development synthetic proxy; not task utility, provider billing, or observed frontier savings.",
    }
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = measure(args.output)
    print(json.dumps({
        "status": report["status"],
        "total": report["total"],
        "frontier_token_savings_percent": report["frontier_token_savings_percent"],
        "frontier_usage_pairs": report["frontier_usage_pairs"],
        "receipt": str(args.output.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
