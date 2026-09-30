"""Measure Iteration 220 input token counts without loading model weights."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from examples.gateway_context_mvp import run_diverse_local_pilot_iter219 as pilot
from examples.gateway_context_mvp.build_iteration220_noise_manifest import (
    OUTPUT as MANIFEST,
    sha256_file,
)
from wrench_harness.context import ContextLedger
from wrench_harness.e0_context_pipeline import MAX_SOURCE_INGESTION_TOKENS
from wrench_harness.gateway_pilot_contracts import validate_diverse_manifest

APPROVED_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp")
TEMP_ROOT = APPROVED_ROOT / "tmp"
OUTPUT = APPROVED_ROOT / "iteration-220-context-only-token-screen.json"
JOB_ID = "WRENCH-CODETASK-ITER220-NOISE-FIXTURE-20260930-01"
MODEL_DIR = Path(
    r"C:\wrench-slm-data\weights\qwen35-4b-hf-cache\models--Qwen--Qwen3.5-4B\snapshots\851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
)
STORAGE_CHECKER = ROOT / "tools/check_wrench_storage_budget.py"
EXTERNAL_ROOTS = (
    r"C:\wrench-slm-data",
    r"\\wsl.localhost\docker-desktop\mnt\docker-desktop-disk\data\docker\volumes\local-ai-models\_data",
    str(Path.home() / ".codex/automations/wrench-hourly-token-reduction-monitor"),
)


def storage_admission() -> dict[str, Any]:
    command = [sys.executable, str(STORAGE_CHECKER), "status"]
    for root in EXTERNAL_ROOTS:
        command.extend(("--include-root", root))
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    report = json.loads(result.stdout)
    if result.returncode or report.get("status") != "WITHIN_LIMIT":
        raise RuntimeError("storage_admission_failed")
    if JOB_ID not in report.get("reservations", []):
        raise RuntimeError("storage_reservation_missing")
    free = shutil.disk_usage(OUTPUT.parent.anchor).free
    if free < 5 * 1024**3:
        raise RuntimeError("destination_headroom_below_5_gib")
    if OUTPUT.exists():
        raise FileExistsError("refusing_to_overwrite_iteration220_receipt")
    return {
        "status": report["status"],
        "reservation_id": JOB_ID,
        "projected_bytes": report["projected_bytes"],
        "budget_headroom_bytes": report["headroom_bytes"],
        "destination_free_bytes": free,
    }


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _full_context_messages(repository: dict[str, Any], episode: dict[str, Any]) -> list[dict[str, str]]:
    system, request = pilot._task_prompts(episode)
    files = repository["files"]
    context = "Synthetic repository context for " + repository["id"] + ":\n" + "\n".join(
        f"--- {path} ---\n{files[path]}" for path in sorted(files)
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": request},
        {"role": "user", "content": context},
    ]


def main() -> None:
    started = time.perf_counter()
    admission = storage_admission()
    if not MANIFEST.is_file() or not MODEL_DIR.is_dir():
        raise RuntimeError("local_manifest_or_tokenizer_snapshot_missing")

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HOME"] = r"C:\wrench-slm-data\cache\huggingface\gateway-demo"
    os.environ["TORCH_HOME"] = r"C:\wrench-slm-data\cache\torch\gateway-demo"

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validation = validate_diverse_manifest(manifest)
    manifest_sha = sha256_file(MANIFEST)
    goal_sha = pilot.actual_goal_sha256()

    # Importing only AutoTokenizer loads no model weights and performs no inference.
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_DIR,
        local_files_only=True,
        trust_remote_code=False,
    )
    context_errors: list[str] = []
    original_add_segment = ContextLedger.add_segment

    def capture_context_error(self, *args, **kwargs):
        try:
            return original_add_segment(self, *args, **kwargs)
        except Exception as exc:
            context_errors.append(str(exc))
            raise

    ContextLedger.add_segment = capture_context_error
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    try:
        for repository in manifest["repositories"]:
            for episode in repository["episodes"]:
                with tempfile.TemporaryDirectory(prefix=f"iter220-{episode['id']}-", dir=TEMP_ROOT) as work:
                    full_messages = _full_context_messages(repository, episode)
                    try:
                        _, prepared_messages, context_receipt = pilot._build_episode_context(
                            tokenizer,
                            f"{pilot.pinned.MODEL_ID}@{pilot.pinned.MODEL_REVISION}",
                            repository,
                            episode,
                            Path(work),
                            source_ingestion_token_limit=MAX_SOURCE_INGESTION_TOKENS,
                        )
                        rows.append({
                            "episode_id": episode["id"],
                            "preparation_status": "ready",
                            **context_receipt,
                        })
                    except RuntimeError as exc:
                        if not str(exc).startswith("context_preparation_failed:"):
                            raise
                        # Preserve the no-miss rule: a failed Wrench preparation gets
                        # the full context as a safe zero-saving fallback and stays in
                        # the denominator rather than disappearing from the pilot.
                        rendered_full, encoded_full = pilot._render_messages(tokenizer, full_messages)
                        quote_rows = episode["oracle"].get("quotes", [])
                        full_serialized = json.dumps(full_messages, ensure_ascii=False)
                        visible = sum(quote in full_serialized for quote in quote_rows)
                        rows.append({
                            "episode_id": episode["id"],
                            "preparation_status": "failed_full_context_fallback",
                            "preparation_error": str(exc),
                            "captured_context_admission_error": context_errors[-1] if context_errors else None,
                            "fallback_policy": "reuse_full_context_no_savings_credit",
                            "target_tokenizer_input_ids": {
                                "full_context": int(encoded_full["input_ids"].shape[-1]),
                                "wrench_prepared": int(encoded_full["input_ids"].shape[-1]),
                            },
                            "rendered_prompt_sha256": sha256_bytes(rendered_full.encode("utf-8")),
                            "oracle_quote_count": len(quote_rows),
                            "oracle_quotes_visible": visible,
                            "oracle_quotes_missing": len(quote_rows) - visible,
                            "cache_state": "cold_isolated_per_episode",
                            "retrieval_miss_count": None,
                            "omitted_evidence_count": None,
                        })
    finally:
        tokenizer = None
        ContextLedger.add_segment = original_add_segment

    baseline = sum(row["target_tokenizer_input_ids"]["full_context"] for row in rows)
    prepared = sum(row["target_tokenizer_input_ids"]["wrench_prepared"] for row in rows)
    reduction = (baseline - prepared) / baseline if baseline else None
    quote_total = sum(row["oracle_quote_count"] for row in rows)
    quote_visible = sum(row["oracle_quotes_visible"] for row in rows)
    receipt: dict[str, Any] = {
        "schema": "wrench.iteration220.context-only-token-screen.v1",
        "job_id": JOB_ID,
        "nonce": "f728236c-9bc3-4a31-884d-445f0d0a1d37",
        "scope": "synthetic tokenizer-only context-preparation screen",
        "model_weights_loaded": False,
        "generation_or_inference_performed": False,
        "provider_or_subroute_calls": 0,
        "frontier_tokens_or_cost": None,
        "task_success_measured": False,
        "repository_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip(),
        "goal_sha256_actual": goal_sha,
        "goal_sha256_declared_by_active_heartbeat": pilot.DECLARED_ACTIVE_GOAL_SHA256,
        "goal_hash_matches_heartbeat": goal_sha == pilot.DECLARED_ACTIVE_GOAL_SHA256,
        "manifest_sha256": manifest_sha,
        "manifest_validation": validation,
        "model_tokenizer": f"{pilot.pinned.MODEL_ID}@{pilot.pinned.MODEL_REVISION}",
        "model_snapshot": str(MODEL_DIR),
        "query_only_retrieval": True,
        "source_ingestion_token_limit": MAX_SOURCE_INGESTION_TOKENS,
        "oracle_paths_passed_to_retriever": False,
        "episode_count": len(rows),
        "baseline_input_token_ids": baseline,
        "wrench_prepared_input_token_ids": prepared,
        "input_token_reduction_fraction": reduction,
        "oracle_quotes_total": quote_total,
        "oracle_quotes_visible_after_retrieval": quote_visible,
        "retrieval_misses_total": sum(
            row["retrieval_miss_count"] or 0 for row in rows
            if row["retrieval_miss_count"] is not None
        ),
        "retrieval_miss_counts_complete": all(
            row["retrieval_miss_count"] is not None for row in rows
        ),
        "omitted_evidence_total": sum(
            row["omitted_evidence_count"] or 0 for row in rows
            if row["omitted_evidence_count"] is not None
        ),
        "preparation_failure_count": sum(
            row["preparation_status"] != "ready" for row in rows
        ),
        "per_episode": rows,
        "storage_admission": admission,
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(payload) > 2_000_000 or APPROVED_ROOT.resolve() not in OUTPUT.resolve().parents:
        raise RuntimeError("receipt_path_or_size_invalid")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)
    print(json.dumps({
        "receipt": str(OUTPUT),
        "receipt_sha256": sha256_bytes(payload),
        "episode_count": len(rows),
        "baseline_input_token_ids": baseline,
        "wrench_prepared_input_token_ids": prepared,
        "input_token_reduction_fraction": reduction,
        "oracle_quotes": f"{quote_visible}/{quote_total}",
        "retrieval_misses": receipt["retrieval_misses_total"],
        "model_weights_loaded": False,
        "goal_hash_matches_heartbeat": receipt["goal_hash_matches_heartbeat"],
    }, indent=2))


if __name__ == "__main__":
    main()
