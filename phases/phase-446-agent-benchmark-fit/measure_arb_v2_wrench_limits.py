"""Reproduce Wrench Qwen gate character and token-limit decisions on ARB V2 prompts."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_arb_v2_abstention_gate import DATA, load_cases, sha256_file, write_json


PHASE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    model_dir, head_path, output_dir = args.model_dir.resolve(), args.head.resolve(), args.output_dir.resolve()
    if not model_dir.is_dir() or not head_path.is_file() or output_dir.exists():
        parser.error("model, head must exist and output directory must not exist")

    import torch
    from transformers import AutoTokenizer

    head = json.loads(head_path.read_text(encoding="utf-8"))
    max_chars, max_tokens = head["max_chars"], head["max_tokens"]
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True, local_files_only=True)
    cases = load_cases(DATA)
    output_dir.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    path = output_dir / "input-limits.jsonl"
    with path.open("x", encoding="utf-8") as stream:
        for case in cases:
            chars = sum(len(message["content"]) for message in case["messages"])
            if chars > max_chars:
                token_count = None
                reason = "input_too_long_chars"
            else:
                text = tokenizer.apply_chat_template(
                    case["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=False
                )
                encoded = tokenizer(text, return_tensors="pt", add_special_tokens=False, truncation=False)
                token_count = int(encoded["input_ids"].shape[-1])
                reason = "input_too_long_tokens" if token_count > max_tokens else "within_limits"
            row = {
                "id": case["id"],
                "repo": case["repo"],
                "group": case["group"],
                "expected": case["expected"],
                "input_chars": chars,
                "input_tokens": token_count,
                "limit_reason": reason,
            }
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
            rows.append(row)
    summary = {
        "schema": "wrench.arb-v2-input-limit-audit.v1",
        "status": "COMPLETE",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": sha256_file(DATA),
        "head_sha256": sha256_file(head_path),
        "checkpoint_sha256": head["checkpoint_sha256"],
        "model_dir": str(model_dir),
        "tokenizer_implementation": "Transformers AutoTokenizer; QwenAbstainGate.encode_messages chat-template serialization",
        "max_chars": max_chars,
        "max_tokens": max_tokens,
        "cases": len(rows),
        "limit_counts": {
            reason: sum(row["limit_reason"] == reason for row in rows)
            for reason in ("within_limits", "input_too_long_chars", "input_too_long_tokens")
        },
        "input_limits_sha256": sha256_file(path),
        "resources": {
            "ram_available_bytes": __import__("psutil").virtual_memory().available,
            "vram_free_total_bytes": list(torch.cuda.mem_get_info()) if torch.cuda.is_available() else None,
        },
        "artifact": path.name,
    }
    write_json(output_dir / "summary.json", summary)
    print(json.dumps(summary, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
