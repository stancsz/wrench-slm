#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrench-SLM Production Log Ingestion Pipeline
=============================================
Reads real production logs from LeanRouter (READ-ONLY) and transforms them into
standardized, high-quality, verified training, validation, and held-out evaluation
datasets for Wrench-SLM.

Data sources parsed:
  - c:\\Users\\stanc\\github\\lean-router\\logs\\tool_calls.log*
  - c:\\Users\\stanc\\github\\lean-router\\logs\\events\\*.jsonl
  - c:\\Users\\stanc\\github\\lean-router\\logs\\router.log*

Outputs written strictly into:
  - c:\\Users\\stanc\\github\\portfolio\\wrench-slm\\data\\train.jsonl
  - c:\\Users\\stanc\\github\\portfolio\\wrench-slm\\data\\val.jsonl
  - c:\\Users\\stanc\\github\\portfolio\\wrench-slm\\data\\held_out.jsonl
  - c:\\Users\\stanc\\github\\portfolio\\wrench-slm\\data\\manifest.json
"""

from __future__ import annotations

import glob
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


LEAN_ROUTER_LOGS_DIR = Path(r"c:\Users\stanc\github\lean-router\logs")
OUTPUT_DATA_DIR = Path(r"c:\Users\stanc\github\portfolio\wrench-slm\data")


# Regex patterns for high-precision log extraction
TOOL_COMPLETED_RE = re.compile(
    r"\[(?P<timestamp>[\d\-]+ [\d:]+)\]\s+\[INFO\]\s+\[(?P<req_id>\w+)\]\s+Completed:\s+(?P<tool>[\w\-:]+)\s+\((?P<call_id>call_[\w\-]+)\)\s+args:\s+(?P<raw_args>\{.*\})"
)

SEMANTIC_ROUTER_RE = re.compile(
    r"\[(?P<req_id>\w+)\]\s+\[Semantic Router\]\s+tier=(?P<tier>\w+)\s+complexity=(?P<complexity>[\d\.]+)\s+cat=(?P<cat>\w+)"
)


@dataclass
class ToolCallRecord:
    id: str
    req_id: str
    timestamp: str
    tool: str
    call_id: str
    args: Dict[str, Any]
    canonical_call: str
    prompt: str
    served_model: str = "minimax/minimax-m3"
    complexity: float = 0.1
    category: str = "routine"
    priority: str = "P4"
    source: str = "lean_router_production_log"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_natural_prompt(tool: str, args: Dict[str, Any]) -> str:
    """
    Synthesize a clean, natural language user instruction from the concrete tool call.
    Ground-truth is the exact arguments executed in the production log.
    """
    if tool == "exec_command":
        cmd = str(args.get("cmd", "")).strip()
        workdir = args.get("workdir")
        wd_str = f" in directory {workdir}" if workdir else ""
        # Distinguish python, powershell, git, etc.
        if cmd.startswith("py ") or cmd.startswith("python"):
            return f"Run the following Python script/command{wd_str}:\n{cmd}"
        elif cmd.startswith("git "):
            return f"Execute git command{wd_str}: {cmd}"
        elif cmd.startswith("Get-Content") or cmd.startswith("cat "):
            return f"Inspect file contents using command{wd_str}: {cmd}"
        else:
            return f"Execute shell command{wd_str}: {cmd}"

    elif tool == "write_stdin":
        text = str(args.get("text", "")).strip()
        return f"Send input to active process: {text[:200]}"

    elif tool == "send_input":
        input_data = str(args.get("input", "")).strip()
        task_id = args.get("task_id", "")
        return f"Send input to task {task_id}: {input_data[:200]}"

    elif tool == "get_goal":
        goal_id = args.get("goal_id") or args.get("id", "")
        return f"Get status and details for goal {goal_id}"

    elif tool == "create_goal":
        obj = args.get("objective") or args.get("title") or args.get("goal", "")
        return f"Create a new goal with objective: {obj}"

    elif tool == "update_goal":
        goal_id = args.get("goal_id") or args.get("id", "")
        status = args.get("status", "")
        return f"Update goal {goal_id} to status: {status}"

    elif tool == "multi_agent_v1":
        agents = args.get("agents", [])
        names = [a.get("name", "agent") for a in agents if isinstance(a, dict)]
        return f"Launch multi-agent workflow with agents: {', '.join(names)}"

    elif tool == "spawn_agent":
        name = args.get("name") or args.get("role", "")
        prompt = str(args.get("prompt", ""))[:150]
        return f"Spawn agent '{name}' with task: {prompt}"

    elif tool == "view_image":
        path = args.get("path") or args.get("file", "")
        return f"Inspect and view image at: {path}"

    elif tool == "write_file":
        path = args.get("path") or args.get("file", "")
        return f"Write content to file: {path}"

    elif tool == "apply_patch":
        path = args.get("path") or args.get("file", "")
        return f"Apply code patch to file: {path}"

    elif tool == "tabs":
        action = args.get("action", "list")
        return f"Browser tab management: {action}"

    else:
        # Generic tool
        arg_keys = ", ".join(args.keys())
        return f"Execute tool '{tool}' with parameters for {arg_keys}"


def extract_events_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Parse events/*.jsonl to collect request-level metadata:
    model, priority, complexity, tier.
    """
    events_dir = LEAN_ROUTER_LOGS_DIR / "events"
    metadata_by_req: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    if not events_dir.is_dir():
        return metadata_by_req

    for jsonl_file in sorted(events_dir.glob("*.jsonl")):
        try:
            with open(jsonl_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        req_id = record.get("req_id")
                        if not req_id:
                            continue
                        meta = metadata_by_req[req_id]
                        if "model" in record:
                            meta["served_model"] = record["model"]
                        if "priority_tier" in record:
                            meta["priority"] = record["priority_tier"]
                        if "priority" in record:
                            meta["priority"] = record["priority"]
                        if "route" in record:
                            meta["tier"] = record["route"]
                    except Exception:
                        continue
        except Exception as e:
            print(f"Warning: error reading {jsonl_file}: {e}")

    return metadata_by_req


def parse_tool_calls(events_meta: Dict[str, Dict[str, Any]]) -> List[ToolCallRecord]:
    """
    Scan tool_calls.log and rotated tool_calls.log.* files to extract verified tool executions.
    """
    records: List[ToolCallRecord] = []
    seen_call_ids = set()

    tool_files = sorted(glob.glob(str(LEAN_ROUTER_LOGS_DIR / "tool_calls.log*")))
    print(f"Discovered {len(tool_files)} tool_calls log file(s): {[Path(p).name for p in tool_files]}")

    for file_path in tool_files:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "Completed:" not in line:
                    continue
                m = TOOL_COMPLETED_RE.search(line)
                if not m:
                    continue
                
                req_id = m.group("req_id")
                tool_name = m.group("tool")
                call_id = m.group("call_id")
                raw_args = m.group("raw_args")
                timestamp = m.group("timestamp")

                if call_id in seen_call_ids:
                    continue
                seen_call_ids.add(call_id)

                # Validate JSON args
                try:
                    args_dict = json.loads(raw_args)
                    if not isinstance(args_dict, dict):
                        continue
                except Exception:
                    # Skip malformed raw args
                    continue

                canonical = json.dumps(
                    {"tool": tool_name, "args": args_dict},
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":")
                )

                prompt = generate_natural_prompt(tool_name, args_dict)
                req_meta = events_meta.get(req_id, {})

                # Deterministic stable record ID
                rec_id = f"wrench_prod_{hashlib.sha256(call_id.encode('utf-8')).hexdigest()[:12]}"

                record = ToolCallRecord(
                    id=rec_id,
                    req_id=req_id,
                    timestamp=timestamp,
                    tool=tool_name,
                    call_id=call_id,
                    args=args_dict,
                    canonical_call=canonical,
                    prompt=prompt,
                    served_model=req_meta.get("served_model", "minimax/minimax-m3"),
                    complexity=req_meta.get("complexity", 0.1),
                    category=req_meta.get("category", "routine"),
                    priority=req_meta.get("priority", "P4"),
                    source="lean_router_production_log"
                )
                records.append(record)

    return records


def partition_and_write(records: List[ToolCallRecord], out_dir: Path) -> Dict[str, Any]:
    """
    Split records deterministically (70% train, 15% val, 15% held-out) and write out clean jsonl files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Sort deterministically by call_id hash
    records_sorted = sorted(records, key=lambda r: r.id)
    n = len(records_sorted)
    
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    
    train_set = records_sorted[:n_train]
    val_set = records_sorted[n_train:n_train + n_val]
    held_out_set = records_sorted[n_train + n_val:]

    def write_jsonl(path: Path, items: List[ToolCallRecord]):
        with open(path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    train_path = out_dir / "train.jsonl"
    val_path = out_dir / "val.jsonl"
    held_out_path = out_dir / "held_out.jsonl"
    manifest_path = out_dir / "manifest.json"

    write_jsonl(train_path, train_set)
    write_jsonl(val_path, val_set)
    write_jsonl(held_out_path, held_out_set)

    tool_counts = Counter(r.tool for r in records_sorted)
    model_counts = Counter(r.served_model for r in records_sorted)

    manifest = {
        "dataset_name": "Wrench-SLM Production Ingestion Dataset",
        "created_at": datetime.now().isoformat(),
        "total_records": n,
        "splits": {
            "train": len(train_set),
            "val": len(val_set),
            "held_out": len(held_out_set),
        },
        "files": {
            "train": str(train_path),
            "val": str(val_path),
            "held_out": str(held_out_path),
        },
        "tool_distribution": dict(tool_counts.most_common()),
        "model_provenance": dict(model_counts.most_common()),
        "source_repository": "c:\\Users\\stanc\\github\\lean-router\\logs",
        "zero_mutation_guarantee": "lean-router logs were accessed strictly in read-only mode"
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def main():
    print("=" * 70)
    print(" Wrench-SLM: Production Log Ingestion & Dataset Standardization")
    print("=" * 70)

    if not LEAN_ROUTER_LOGS_DIR.is_dir():
        print(f"Error: Log directory not found at {LEAN_ROUTER_LOGS_DIR}")
        sys.exit(1)

    print(f"[1/4] Scanning events metadata from {LEAN_ROUTER_LOGS_DIR / 'events'}...")
    events_meta = extract_events_metadata()
    print(f"      Loaded metadata for {len(events_meta)} unique requests.")

    print("[2/4] Parsing verified completed tool calls from tool_calls.log*...")
    records = parse_tool_calls(events_meta)
    print(f"      Extracted {len(records)} verified production tool calls.")

    print("[3/4] Partitioning into Train (70%), Val (15%), Held-Out (15%)...")
    manifest = partition_and_write(records, OUTPUT_DATA_DIR)

    print(f"[4/4] Output generated successfully in {OUTPUT_DATA_DIR}:")
    print(f"      - train.jsonl:    {manifest['splits']['train']} records")
    print(f"      - val.jsonl:      {manifest['splits']['val']} records")
    print(f"      - held_out.jsonl:  {manifest['splits']['held_out']} records")
    print(f"      - manifest.json:  {manifest_path_display(OUTPUT_DATA_DIR)}")

    print("\nTop 10 Tool Distribution:")
    for tool, count in list(manifest["tool_distribution"].items())[:10]:
        print(f"  * {tool:<28} : {count:>5} calls")

    print("\n" + "=" * 70)
    print(" Log Ingestion Completed. LeanRouter source code untouched.")
    print("=" * 70)


def manifest_path_display(d: Path) -> str:
    return str(d / "manifest.json")


if __name__ == "__main__":
    main()
