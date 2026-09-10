#!/usr/bin/env python3
"""Fetch real Wrench data into data/raw and data/build without replacing data/*.jsonl."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "artifacts/acquisition"
RAW = DATA / "raw"
BUILD = DATA / "build"
LEGACY = DATA / "legacy"
LOGS = ROOT / "artifacts/legacy-work/gateway-logs"
BFCL_REPO = "gorilla-llm/Berkeley-Function-Calling-Leaderboard"
BFCL_FILES = (
    "BFCL_v3_exec_simple.json",
    "BFCL_v3_exec_multiple.json",
    "BFCL_v3_exec_parallel.json",
    "BFCL_v3_exec_parallel_multiple.json",
)
COMPLETED_RE = re.compile(r"Completed:\s+(?P<tool>[^\s(]+)\s+\((?P<call_id>call_[^)]+)\)\s+args:\s+(?P<args>\{.*)$")
HEADER_RE = re.compile(r"^\[(?P<timestamp>[^]]+)\].*?\[(?P<req_id>[0-9a-f]+)\]")
WINDOWS_PREFIXES = ("Get-", "Set-", "New-", "Remove-", "Test-", "Invoke-", "Select-", "Write-", "Start-", "Stop-", "Where-Object", "ForEach-Object")
POSIX_PREFIXES = ("bash ", "sh ", "cat ", "git ", "curl ", "ls ", "pwd", "grep ", "find ", "sed ", "awk ", "pytest", "python ", "python3 ")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                yield value


def download(url: str, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {"url": url, "path": str(destination)}
    try:
        request = Request(url, headers={"User-Agent": "wrench-slm-data-fetch/1.0"})
        with urlopen(request, timeout=180) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        receipt.update(status="downloaded", http_status=response.status, bytes=destination.stat().st_size)
    except HTTPError as exc:
        receipt.update(status="blocked", http_status=exc.code, error=str(exc.reason))
    except (OSError, URLError) as exc:
        receipt.update(status="error", error=str(exc))
    return receipt


def fetch_public_data() -> list[dict[str, Any]]:
    receipts = []
    for filename in BFCL_FILES:
        url = f"https://huggingface.co/datasets/{BFCL_REPO}/resolve/main/{filename}"
        receipts.append(download(url, RAW / "bfcl" / filename))
    gated = {
        "intercode/intercode-bash": "HTTP 401 without an accepted gated-data license and HF token",
        "Salesforce/xlam-function-calling-60k": "HTTP 401 without an accepted gated-data license and HF token",
        "bigcode/the-stack": "gated and too large for unbounded download; shell subset requires accepted license",
    }
    receipt = {"fetched_at": utc_now(), "downloaded": receipts, "blocked_sources": gated}
    (RAW / "hf_acquisition_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipts


def infer_platform(command: str) -> str:
    if command.startswith(WINDOWS_PREFIXES) or " | Select-Object" in command or "Get-ChildItem" in command:
        return "windows"
    if command.startswith(POSIX_PREFIXES):
        return "posix"
    return "cross_platform"


def parse_completed_line(line: str, source: Path, line_number: int) -> dict[str, Any] | None:
    match = COMPLETED_RE.search(line)
    if not match:
        return None
    try:
        args, _ = json.JSONDecoder().raw_decode(match.group("args").lstrip())
    except json.JSONDecodeError:
        return None
    if not isinstance(args, dict):
        return None
    header = HEADER_RE.search(line)
    tool = match.group("tool")
    command = str(args.get("cmd", ""))
    call = {"tool": tool, "args": args}
    return {
        "id": stable_id("wrench_observed", {"call_id": match.group("call_id"), "source": source.name}),
        "tool": tool,
        "args": args,
        "canonical_call": json.dumps(call, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        "prompt": f"Observed production tool call: {tool} {command}".strip(),
        "platform": infer_platform(command),
        "category": "observed_replay_trace",
        "source": "lean_router_production_log",
        "provenance": {
            "source_file": str(source),
            "line_number": line_number,
            "timestamp": header.group("timestamp") if header else None,
            "req_id": header.group("req_id") if header else None,
            "call_id": match.group("call_id"),
        },
        "execution_evidence": "gateway_completed_log_only",
    }


def extract_logs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    records = []
    events = []
    scan = []
    for path in sorted(LOGS.glob("tool_calls.log*")):
        parsed = 0
        lines = 0
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for lines, line in enumerate(handle, 1):
                record = parse_completed_line(line, path, lines)
                if record:
                    records.append(record)
                    parsed += 1
        scan.append({"path": str(path), "bytes": path.stat().st_size, "lines": lines, "completed_records": parsed})
    for path in sorted((LOGS / "events").glob("*.jsonl")):
        count = 0
        for count, event in enumerate(read_jsonl(path), 1):
            event["_provenance"] = {"source_file": str(path), "source_record": count}
            events.append(event)
        scan.append({"path": str(path), "bytes": path.stat().st_size, "event_records": count})
    records.sort(key=lambda row: row["id"])
    return records, events, scan


def distill_one(seed: dict[str, Any], gateway: str, model: str) -> dict[str, Any]:
    command = str(seed.get("args", {}).get("cmd", ""))
    body = {
        "model": model,
        "temperature": 0.4,
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": "Generate exactly 5 concise natural-language user prompts that mean this same tool call. Return JSON only as {\"variants\":[\"...\"]}. Do not alter the command. Tool call:\n" + command,
        }],
    }
    request = Request(gateway.rstrip("/") + "/chat/completions", data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            value = json.loads(content)
            variants = value.get("variants", []) if isinstance(value, dict) else []
        except json.JSONDecodeError:
            variants = []
        return {
            "seed_id": seed["id"],
            "model_requested": model,
            "model_returned": payload.get("model"),
            "variants": [item for item in variants if isinstance(item, str)][:5],
            "usage": payload.get("usage"),
            "status": "ok",
        }
    except Exception as exc:
        return {"seed_id": seed["id"], "model_requested": model, "status": "error", "error": str(exc)}


def distill(records: list[dict[str, Any]], gateway: str, model: str, limit: int) -> list[dict[str, Any]]:
    seeds = [row for row in records if row.get("tool") == "exec_command" and row.get("args", {}).get("cmd")][:limit]
    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(distill_one, seed, gateway, model) for seed in seeds]
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda row: row["seed_id"])


def load_legacy() -> list[dict[str, Any]]:
    rows = []
    for name in ("train.jsonl", "val.jsonl", "held_out.jsonl"):
        path = LEGACY / name
        if path.exists():
            rows.extend(read_jsonl(path))
    return rows


def record_key(row: dict[str, Any]) -> str:
    payload = {"tool": row.get("tool"), "args": row.get("args", {}), "prompt": str(row.get("prompt", "")).strip().lower()}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# legacy records are backed up but excluded from the new evidence build
def build(observed: list[dict[str, Any]], distilled: list[dict[str, Any]]) -> dict[str, Any]:
    """Compose deterministic splits from observed gateway traces and teacher-distilled variants.

    Legacy records live in data/legacy and are intentionally excluded from this build so that
    the evidence boundary stays explicit. Each row carries an execution_evidence tag.
    """
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in observed:
        key = record_key(row)
        if key in seen or not row.get("tool") or not isinstance(row.get("args"), dict):
            continue
        seen.add(key)
        rows.append(row)
    seeds = {row["id"]: row for row in observed}
    for result in distilled:
        seed = seeds.get(result.get("seed_id"))
        if not seed:
            continue
        for index, prompt in enumerate(result.get("variants", [])):
            row = dict(seed)
            row["id"] = stable_id("wrench_distilled", {"seed": seed["id"], "prompt": prompt})
            row["prompt"] = prompt
            row["source"] = "lean_router_gateway_distillation"
            row["category"] = "distilled_observed_trace"
            row["execution_evidence"] = "teacher_generated_prompt_variant"
            row["provenance"] = {"seed_id": seed["id"], "teacher_model": result.get("model_returned"), "variant_index": index}
            key = record_key(row)
            if key not in seen:
                seen.add(key)
                rows.append(row)
    rows.sort(key=lambda row: row["id"])
    splits = {"train": [], "val": [], "held_out": []}
    for row in rows:
        bucket = int(hashlib.md5(row["id"].encode("utf-8")).hexdigest()[:8], 16) % 100
        split = "train" if bucket < 70 else "val" if bucket < 85 else "held_out"
        splits[split].append(row)
    for split, values in splits.items():
        write_jsonl(BUILD / f"{split}.jsonl", values)
    manifest = {
        "dataset_name": "Wrench-SLM Real Data Aggregated Build",
        "version": "3.0.0-real-aggregated",
        "built_at": utc_now(),
        "total_records": len(rows),
        "splits": {key: len(value) for key, value in splits.items()},
        "sources": dict(Counter(row.get("source", "unknown") for row in rows)),
        "categories": dict(Counter(row.get("category", "unknown") for row in rows)),
        "evidence_boundary": {
            "observed_trace": "gateway_completed_log_only",
            "teacher_distillation": "teacher_generated_prompt_variants_only",
            "legacy": "pre-existing local records copied to data/legacy and excluded from this build",
            "public_bfcl": "raw public evaluation reference, not merged into training splits",
        },
        "legacy_split_untouched": True,
    }
    (BUILD / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "README.md").write_text(
        "# Wrench real-data build\n\nThis build is separate from data/archive/baseline/train.jsonl, data/archive/baseline/val.jsonl, and data/archive/baseline/held_out.jsonl. Log-derived rows are observed gateway traces, not independently re-executed commands. Raw BFCL files are public evaluation references kept outside training splits.\n",
        encoding="utf-8",
    )
    return manifest


def backup_legacy() -> None:
    """Create a non-destructive backup once before any acquisition work."""
    LEGACY.mkdir(parents=True, exist_ok=True)
    for name in ("train.jsonl", "val.jsonl", "held_out.jsonl", "manifest.json"):
        source = DATA / name
        destination = LEGACY / name
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", default="http://127.0.0.1:4000/v1")
    parser.add_argument("--teacher-model", default="minimax/minimax-m3")
    parser.add_argument("--distill-limit", type=int, default=100)
    parser.add_argument("--skip-distill", action="store_true")
    args = parser.parse_args()
    for directory in (RAW, BUILD, LEGACY):
        directory.mkdir(parents=True, exist_ok=True)
    backup_legacy()
    print("[1/5] Downloading public BFCL execution files", flush=True)
    downloads = fetch_public_data()
    print("[2/5] Extracting LeanRouter logs read-only", flush=True)
    observed, events, scan = extract_logs()
    write_jsonl(RAW / "lean_router" / "tool_calls.jsonl", observed)
    write_jsonl(RAW / "lean_router" / "events.jsonl", events)
    (RAW / "lean_router" / "scan_receipt.json").write_text(json.dumps({"scanned_at": utc_now(), "files": scan}, indent=2), encoding="utf-8")
    print(f"      observed={len(observed)} events={len(events)}", flush=True)
    print("[3/5] Distilling prompt variants through local gateway", flush=True)
    distilled = [] if args.skip_distill else distill(observed, args.gateway, args.teacher_model, args.distill_limit)
    write_jsonl(RAW / "distillation.jsonl", distilled)
    print(f"      responses={len(distilled)} successful={sum(row.get('status') == 'ok' for row in distilled)} variants={sum(len(row.get('variants', [])) for row in distilled)}", flush=True)
    print("[4/5] Building deduplicated deterministic splits", flush=True)
    manifest = build(observed, distilled)
    receipt = {
        "completed_at": utc_now(),
        "downloads": downloads,
        "observed_calls": len(observed),
        "events": len(events),
        "distillation": {"responses": len(distilled), "successful": sum(row.get("status") == "ok" for row in distilled), "variants": sum(len(row.get("variants", [])) for row in distilled)},
        "build": manifest,
        "legacy_untouched": True,
    }
    (DATA / "acquisition_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[5/5] Receipt written", flush=True)
    print(json.dumps({"total": manifest["total_records"], "splits": manifest["splits"], "legacy_untouched": True}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
