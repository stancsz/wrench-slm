"""Generate a fresh, synthetic-only Wrench gateway LoRA diagnostic corpus.

This emits train/dev/held-out JSONL and a hash manifest. It never reads a
repository, prior fixture, model, teacher, endpoint, credential, or network.
It refuses to overwrite any existing output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


SCHEMA = "wrench.gateway_lora_screen_01.synthetic.v1"
SEED = 20260927
ROWS_PER_SPLIT = {"train": 256, "dev": 64, "heldout": 128}
FAMILIES = ("evidence_select", "retrieve_stop", "compaction_policy", "route")
MAX_FILE_BYTES = 10 * 1024 * 1024

SYSTEM = (
    "You are a proposal-only Wrench gateway. Choose only a bounded route and "
    "operation, and only source IDs shown in the input. Never invent evidence, "
    "execute a tool, modify a file, or grant permission. Return exactly one "
    "JSON object with route, operation, selected_evidence_ids, retrieve_more, "
    "and reason_code."
)

LEXICON = {
    "train": {
        "symbols": ("CacheKey", "RouteStamp", "LineFence", "PatchLedger"),
        "files": ("src/cache.py", "src/router.py", "tests/test_lines.py", "docs/patch.md"),
        "near": ("CacheKeys", "RouteStampOld", "LineFenceTest", "PatchLedgerNotes"),
    },
    "dev": {
        "symbols": ("TracePivot", "LeaseToken", "DeltaMarker", "ScopeFence"),
        "files": ("lib/trace.ts", "lib/lease.ts", "spec/delta.yaml", "notes/scope.txt"),
        "near": ("TracePivots", "LeaseTokenV0", "DeltaMarkers", "ScopeFences"),
    },
    "heldout": {
        "symbols": ("ShardAnchor", "ReplayCursor", "ProofTag", "BudgetLatch"),
        "files": ("engine/shard.go", "engine/replay.go", "qa/proof.json", "ops/budget.toml"),
        "near": ("ShardAnchors", "ReplayCursors", "ProofTags", "BudgetLatches"),
    },
}

WORDING = {
    "train": {
        "evidence_select": "Find the exact definition of {symbol}. Select evidence, then retrieve it. Do not choose a near-match.",
        "retrieve_stop": "Required evidence is {symbol}. Decide whether to retrieve more or stop using only the supplied records.",
        "compaction_policy": "The context is over budget. Preserve the user's instruction, active diff, and failure; cold history can be fetched again by ID.",
        "route": "Choose the bounded route for this request: {request}",
    },
    "dev": {
        "evidence_select": "Return the source ID that proves the exact symbol {symbol}; the similarly named record is not equivalent.",
        "retrieve_stop": "Check whether the supplied evidence for {symbol} is current and sufficient. Request another read when it is stale.",
        "compaction_policy": "Reduce cold context while keeping the explicit instruction, working diff and current test failure intact and retrievable.",
        "route": "Classify this request for Wrench's proposal-only gateway: {request}",
    },
    "heldout": {
        "evidence_select": "Which known evidence ID contains the exact requested symbol {symbol}? Ignore the near-match and cite the ID.",
        "retrieve_stop": "For {symbol}, choose ENOUGH only if the exact current record is present; otherwise retrieve the current record or abstain.",
        "compaction_policy": "Apply a bounded context policy: keep hot user/diff/failure material exactly, and refer to recoverable cold history by source ID.",
        "route": "Select one allowed route and reason code for this user request: {request}",
    },
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ids(split: str, n: int) -> tuple[str, str, str, str]:
    prefix = {"train": "TR", "dev": "DV", "heldout": "HO"}[split]
    return tuple(f"{prefix}-{n:04d}-{slot}" for slot in ("A", "B", "C", "D"))  # type: ignore[return-value]


def _scenario(split: str, family: str, n: int, rng: random.Random) -> tuple[str, dict[str, Any]]:
    words = LEXICON[split]
    symbol_index = (n + rng.randrange(len(words["symbols"]))) % len(words["symbols"])
    symbol = words["symbols"][symbol_index]
    near = words["near"][symbol_index]
    path = words["files"][symbol_index]
    ids = _ids(split, n)
    marker = f"rev-{split}-{(n * 17 + symbol_index) % 997:03d}"

    if family == "evidence_select":
        evidence = [
            {"id": ids[0], "path": path, "symbol": near, "revision": marker, "state": "current"},
            {"id": ids[1], "path": path, "symbol": symbol, "revision": marker, "state": "current"},
            {"id": ids[2], "path": path, "symbol": symbol, "revision": "stale", "state": "stale"},
        ]
        rng.shuffle(evidence)
        prompt = f"{WORDING[split][family].format(symbol=symbol)}\nSnapshot: {marker}\nRecords: {json.dumps(evidence, sort_keys=True)}"
        gold = {"route": "LOCAL_MECHANICAL", "operation": "EXACT_RETRIEVE", "selected_evidence_ids": [ids[1]], "retrieve_more": False, "reason_code": "EXACT_CURRENT_MATCH"}
    elif family == "retrieve_stop":
        mode = n % 4
        if mode == 0:
            records = [{"id": ids[0], "symbol": symbol, "revision": marker, "state": "current"}]
            gold = {"route": "LOCAL_MECHANICAL", "operation": "NOOP", "selected_evidence_ids": [ids[0]], "retrieve_more": False, "reason_code": "ENOUGH_CURRENT_EVIDENCE"}
        elif mode in (1, 2):
            records = [{"id": ids[0], "symbol": symbol, "revision": "old", "state": "stale"}, {"id": ids[1], "symbol": symbol, "revision": marker, "state": "available"}]
            gold = {"route": "LOCAL_MECHANICAL", "operation": "EXACT_RETRIEVE", "selected_evidence_ids": [ids[1]], "retrieve_more": True, "reason_code": "REFRESH_STALE_EVIDENCE"}
        else:
            records = [{"id": ids[0], "symbol": near, "revision": marker, "state": "current"}]
            gold = {"route": "ABSTAIN", "operation": "NOOP", "selected_evidence_ids": [], "retrieve_more": True, "reason_code": "EXACT_EVIDENCE_MISSING"}
        rng.shuffle(records)
        prompt = f"{WORDING[split][family].format(symbol=symbol)}\nSnapshot: {marker}\nRecords: {json.dumps(records, sort_keys=True)}"
    elif family == "compaction_policy":
        records = [
            {"id": ids[0], "kind": "user_instruction", "temperature": "hot", "recoverable": True},
            {"id": ids[1], "kind": "active_diff", "temperature": "hot", "recoverable": True},
            {"id": ids[2], "kind": "current_failure", "temperature": "hot", "recoverable": True},
            {"id": ids[3], "kind": "old_history", "temperature": "cold", "recoverable": True},
        ]
        rng.shuffle(records)
        prompt = f"{WORDING[split][family]}\nBudget: {128 + (n % 5) * 16} tokens\nRecords: {json.dumps(records, sort_keys=True)}"
        gold = {"route": "LOCAL_COMPACTION", "operation": "COMPACT", "selected_evidence_ids": sorted(ids[:3]), "retrieve_more": False, "reason_code": "PRESERVE_HOT_RETRIEVE_COLD"}
    else:
        cases = (
            ("Return the exact lines containing the literal {symbol} from the current source.", {"route": "LOCAL_MECHANICAL", "operation": "EXACT_RETRIEVE", "selected_evidence_ids": [ids[0]], "retrieve_more": False, "reason_code": "BOUNDED_EXACT_OPERATION"}),
            ("Diagnose why the failing test occurs and propose a multi-file semantic fix for {symbol}.", {"route": "FRONTIER", "operation": "NOOP", "selected_evidence_ids": [ids[0], ids[1]], "retrieve_more": False, "reason_code": "OPEN_ENDED_ENGINEERING"}),
            ("Fix it. No task details or current failure evidence are available.", {"route": "ABSTAIN", "operation": "NOOP", "selected_evidence_ids": [], "retrieve_more": True, "reason_code": "REQUIREMENTS_OR_EVIDENCE_MISSING"}),
            ("Compute the current line count for {symbol} in the provided exact source range.", {"route": "LOCAL_MECHANICAL", "operation": "EXACT_RETRIEVE", "selected_evidence_ids": [ids[2]], "retrieve_more": False, "reason_code": "BOUNDED_EXACT_OPERATION"}),
        )
        request_template, gold_template = cases[n % len(cases)]
        request = request_template.format(symbol=symbol)
        records = [
            {"id": ids[0], "kind": "current_source", "path": path, "symbol": symbol, "revision": marker, "available": True},
            {"id": ids[1], "kind": "failure_log", "path": "logs/current-test.log", "symbol": symbol, "revision": marker, "available": True},
            {"id": ids[2], "kind": "source_range", "path": path, "symbol": symbol, "revision": marker, "available": True},
        ]
        prompt = f"{WORDING[split][family].format(request=request)}\nSnapshot: {marker}\nRecords: {json.dumps(records, sort_keys=True)}"
        gold = dict(gold_template)

    return prompt, gold


def build_split(split: str, count: int) -> list[dict[str, Any]]:
    rng = random.Random(SEED + {"train": 0, "dev": 100_000, "heldout": 200_000}[split])
    per_family = count // len(FAMILIES)
    rows: list[dict[str, Any]] = []
    for family_index, family in enumerate(FAMILIES):
        for i in range(per_family):
            ordinal = family_index * per_family + i
            prompt, gold = _scenario(split, family, ordinal, rng)
            rows.append({
                "schema": SCHEMA,
                "example_id": f"{split}-{family}-{ordinal:04d}",
                "split": split,
                "family": family,
                "template_group": f"{split}:{family}:template-v1",
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": json.dumps(gold, ensure_ascii=False, sort_keys=True)},
                ],
                "gold": gold,
            })
    rng.shuffle(rows)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_root.resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output: {root}")
    root.mkdir(parents=True, exist_ok=True)

    files: dict[str, dict[str, Any]] = {}
    for split, count in ROWS_PER_SPLIT.items():
        path = root / f"{split}.jsonl"
        rows = build_split(split, count)
        payload = b"".join(_json_bytes(row) for row in rows)
        if len(payload) > MAX_FILE_BYTES:
            raise SystemExit(f"split exceeds byte cap: {split}")
        with path.open("xb") as stream:
            stream.write(payload)
        files[split] = {"path": path.name, "count": len(rows), "size_bytes": len(payload), "sha256": _digest(path)}

    manifest = {
        "schema": "wrench.gateway_lora_screen_01.manifest.v1",
        "synthetic_only": True,
        "seed": SEED,
        "generator_sha256": _digest(Path(__file__).resolve()),
        "families": list(FAMILIES),
        "split_method": "disjoint wording, symbol, path, revision-marker and scenario-seed groups per split",
        "files": files,
        "limitations": [
            "synthetic rule labels are not real workflow outcomes",
            "template-family holdout does not prove repository or user generalization",
            "heldout must not be read or used for tuning until training is complete",
        ],
    }
    manifest_path = root / "manifest.json"
    with manifest_path.open("xb") as stream:
        stream.write(_json_bytes(manifest))
    print(json.dumps({"status": "GENERATED", "root": str(root), "manifest_sha256": _digest(manifest_path), "files": files}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
