#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrench-SLM Cross-Platform Dataset Transpiler & Augmentor
=========================================================
Bridges the gap between Windows production logs and Linux / macOS environments.

1. Identifies Windows/PowerShell records and explicitly tags them:
     platform: "windows"
     prompt: "Execute shell command (powershell on Windows): ..."
2. Generates equivalent POSIX Bash records for Linux & macOS:
     platform: "posix"
     prompt: "Execute shell command (bash on Linux/macOS): ..."
3. Tags API / Agent tools as:
     platform: "cross_platform"
4. Updates train.jsonl, val.jsonl, held_out.jsonl, and manifest.json.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


DATA_DIR = Path(__file__).resolve().parents[1] / "artifacts/legacy-work/data"


_POSIX_VERIFY_CACHE: Dict[str, bool] = {}


def verify_posix_syntax(cmd: str) -> bool:
    """Verifies that cmd is valid POSIX bash syntax."""
    if not cmd or not cmd.strip():
        return False
    if cmd in _POSIX_VERIFY_CACHE:
        return _POSIX_VERIFY_CACHE[cmd]

    # Exclude powershell specific markers that cannot run in bash
    ps_markers = [
        "[System.", "[System.IO", "[System.Text", "New-Object", "Where-Object",
        "Select-Object", "Format-Table", "Get-Process", "Get-Service", "Test-Path",
        "2>$null", "$_.FullName", "$_.Name", "$ErrorActionPreference",
        "Out-String", "Out-Null", "@{"
    ]
    for m in ps_markers:
        if m in cmd:
            _POSIX_VERIFY_CACHE[cmd] = False
            return False

    # Check for basic quote balancing
    double_quotes = cmd.count('"') - cmd.count(r'\"')
    single_quotes = cmd.count("'") - cmd.count(r"\'")
    if double_quotes % 2 != 0 or single_quotes % 2 != 0:
        _POSIX_VERIFY_CACHE[cmd] = False
        return False

    if cmd.endswith("|") or cmd.endswith("&&") or cmd.endswith("||"):
        _POSIX_VERIFY_CACHE[cmd] = False
        return False

    try:
        # High-speed tokenization check
        shlex.split(cmd)
        is_ok = True
    except ValueError:
        is_ok = False

    _POSIX_VERIFY_CACHE[cmd] = is_ok
    return is_ok


def powershell_to_posix(cmd: str) -> str:
    """
    Translates Windows PowerShell commands into standard POSIX Bash commands
    for macOS and Linux.
    """
    c = cmd.strip()

    # Normalize Windows drive and user home paths
    c = re.sub(r'[A-Za-z]:[\\\/]Users[\\\/][^\\\/]+[\\\/]', '~/', c)
    c = re.sub(r'[A-Za-z]:[\\\/]Users[\\\/][^\\\/]+', '~', c)
    
    # Python launcher executable (avoid matching .py extension)
    c = re.sub(r'(?<![.\w])py\s+-3\s+-X\s+utf8\b', 'python3', c)
    c = re.sub(r'(?<![.\w])py\s+-3\b', 'python3', c)
    c = re.sub(r'(?<![.\w])py\s+(?=[^-\n])', 'python3 ', c)

    # Redirections and pipes
    c = re.sub(r'2>\$null', '2>/dev/null', c)
    c = re.sub(r'>\$null', '>/dev/null', c)
    c = re.sub(r'\|\s*Out-Null', '>/dev/null 2>&1', c)
    c = re.sub(r'\|\s*Out-String', '', c)
    c = re.sub(r'-ErrorAction\s+(?:SilentlyContinue|Stop|Ignore)', '', c)

    # Get-Content variations
    c = re.sub(r'\bGet-Content\s+([^\s\|]+)\s+-TotalCount\s+(\d+)', r'head -n \2 \1', c)
    c = re.sub(r'\bGet-Content\s+([^\s\|]+)\s*\|\s*Measure-Object\s+-Line[^\n\|;]*', r'wc -l \1', c)
    c = re.sub(r'\bGet-Content\s+([^\s\|]+)\s*\|\s*Select-Object\s+-First\s+(\d+)', r'head -n \2 \1', c)
    c = re.sub(r'\bGet-Content\s+', 'cat ', c)

    # File and directory cmdlets
    c = re.sub(r'\bGet-ChildItem\s+-Path\s+', 'ls ', c)
    c = re.sub(r'\bGet-ChildItem\b', 'ls', c)
    c = re.sub(r'\bSet-Location\b', 'cd', c)
    c = re.sub(r'\bRemove-Item\s+-Force\b', 'rm -f', c)
    c = re.sub(r'\bRemove-Item\b', 'rm -f', c)
    c = re.sub(r'\bWrite-Host\b', 'echo', c)
    c = re.sub(r'\bWrite-Output\b', 'echo', c)
    c = re.sub(r'\|\s*Select-Object\s+-First\s+(\d+)', r'| head -n \1', c)
    c = re.sub(r'\|\s*Select-Object\s+-Last\s+(\d+)', r'| tail -n \1', c)

    # Replace Windows backslashes in relative file paths
    for _ in range(3):
        c = re.sub(r'(\b[\w\.-]+)\\([\w\.-]+\b)', r'\1/\2', c)

    return c


def process_file(file_path: Path) -> Tuple[List[Dict[str, Any]], Counter]:
    """
    Reads a jsonl split and outputs an augmented list of records with explicit platform conditioning.
    """
    augmented_records: List[Dict[str, Any]] = []
    platform_counter = Counter()

    if not file_path.is_file():
        return augmented_records, platform_counter

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            tool = rec.get("tool")
            args = rec.get("args", {})

            if tool != "exec_command":
                # Pure cross-platform API/Agent tool
                rec["platform"] = "cross_platform"
                augmented_records.append(rec)
                platform_counter["cross_platform"] += 1
                continue

            # It's an exec_command
            orig_cmd = args.get("cmd", "")
            if not isinstance(orig_cmd, str):
                orig_cmd = json.dumps(orig_cmd, ensure_ascii=False) if isinstance(orig_cmd, (dict, list)) else str(orig_cmd)
            
            # 1. Update original record with explicit Windows / PowerShell conditioning
            rec["platform"] = "windows"
            rec["prompt"] = f"Execute shell command (powershell on Windows): {orig_cmd}"
            augmented_records.append(rec)
            platform_counter["windows"] += 1

            # 2. Synthesize equivalent POSIX Bash record for Linux & macOS ONLY if valid
            posix_cmd = powershell_to_posix(orig_cmd)
            if verify_posix_syntax(posix_cmd):
                # Create paired POSIX record
                posix_args = dict(args)
                posix_args["cmd"] = posix_cmd
                
                # Normalize workdir if present
                if "workdir" in posix_args and posix_args["workdir"]:
                    posix_args["workdir"] = re.sub(r'^[A-Za-z]:[\\\/]Users[\\\/][^\\\/]+', '~', posix_args["workdir"]).replace('\\', '/')

                posix_canonical = json.dumps(
                    {"args": posix_args, "tool": "exec_command"},
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":")
                )

                posix_id = f"wrench_posix_{hashlib.sha256(posix_canonical.encode('utf-8')).hexdigest()[:12]}"
                posix_rec = dict(rec)
                posix_rec["id"] = posix_id
                posix_rec["platform"] = "posix"  # Linux & macOS compatible
                posix_rec["args"] = posix_args
                posix_rec["canonical_call"] = posix_canonical
                posix_rec["prompt"] = f"Execute shell command (bash on Linux/macOS): {posix_cmd}"
                
                augmented_records.append(posix_rec)
                platform_counter["posix"] += 1

    return augmented_records, platform_counter


def main():
    print("=" * 70)
    print(" Wrench-SLM: Cross-Platform Dataset Transpilation (Windows -> Mac/Linux)")
    print("=" * 70)

    total_platform_counts = Counter()
    split_counts = {}

    for split in ["train", "val", "held_out"]:
        file_path = DATA_DIR / f"{split}.jsonl"
        print(f"Processing {file_path.name}...")
        records, counts = process_file(file_path)
        
        # Write back augmented records
        with open(file_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        
        split_counts[split] = len(records)
        total_platform_counts.update(counts)
        print(f"  -> Augmented {split}.jsonl: {len(records)} total records (Windows: {counts['windows']}, POSIX: {counts['posix']}, CrossPlatform: {counts['cross_platform']})")

    # Update manifest.json
    manifest_path = DATA_DIR / "manifest.json"
    manifest_data = {}
    if manifest_path.is_file():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

    manifest_data["cross_platform_coverage"] = {
        "supported_os": ["Windows", "Linux", "macOS"],
        "platform_distribution": dict(total_platform_counts),
        "augmentation_method": "Deterministic PowerShell-to-POSIX transpiler + explicit OS conditioning tags",
        "total_augmented_records": sum(split_counts.values())
    }
    manifest_data["splits"] = split_counts
    manifest_data["total_records"] = sum(split_counts.values())

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(" Cross-Platform Augmentation Complete!")
    print(f" Total records across all splits: {manifest_data['total_records']}")
    print(f" Platform distribution: {dict(total_platform_counts)}")
    print(f" Manifest updated at: {manifest_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
