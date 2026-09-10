"""Build V16 training-only corrections for Chinese invalid-range handling.

V16 keeps the V15 candidate as the parent and puts 4,800 fresh examples at
the front of the training stream. Most are invalid-range abstentions with the
duplicated, explicit wording seen in the remaining external failures. The
other prefix rows preserve a small routine mix. Development and evaluation
are copied byte-for-byte from V15.
"""

from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import public_record  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402
from wrench.release_data import make_release_task  # noqa: E402


PARENT = ROOT / "data/pilots/release-generalization-v15"
OUTPUT = ROOT / "data/pilots/release-generalization-v16"


PROMPTS = {
    "invalid_range": {
        "en": "This line range is invalid. Do not read any file and do not call read_file. Return ROUTER_FALLBACK. Target path: {path}. Requested bounds: {start} through {end}. The target path is {path}; the requested bounds are {start} through {end}. Return ROUTER_FALLBACK and do not call a tool.",
        "zh": "这个行范围无效。不要读取任何文件，也不要调用 read_file。请返回 ROUTER_FALLBACK。目标路径：{path}。请求范围：第 {start} 到第 {end} 行。目标路径是 {path}，请求范围为第 {start} 到第 {end} 行。请返回 ROUTER_FALLBACK，不要调用工具。",
    },
    "lines": {
        "en": "Return exactly one JSON read_file call using the selected path and inclusive bounds {start} through {end}.",
        "zh": "请只返回一个 JSON read_file 调用，使用选定路径和包含首尾的第 {start} 到第 {end} 行。",
    },
    "git_log": {
        "en": "Return exactly one JSON call to git log -1 --format=%s for the newest commit subject.",
        "zh": "请只返回一个 JSON git log -1 --format=%s 调用来读取最新提交主题。",
    },
    "config": {
        "en": "Return exactly one JSON read_file call for the selected configuration path to inspect region.",
        "zh": "请只返回一个 JSON read_file 调用，读取选定配置路径来检查 region。",
    },
    "search": {
        "en": "Return exactly one JSON fixed-string rg command using the selected directory and marker.",
        "zh": "请只返回一个 JSON 固定字符串 rg 命令，使用上下文选定的目录和标记。",
    },
    "health": {
        "en": "Return exactly one JSON curl health command using the selected URL and allowlisted flags.",
        "zh": "请只返回一个 JSON curl 健康检查命令，使用选定地址和允许的参数。",
    },
    "git_status": {
        "en": "Return exactly one JSON call to git status --short for this read-only request.",
        "zh": "请只返回一个 JSON git status --short 调用，这是只读请求。",
    },
}


def vary_context(row: dict, instance: int) -> dict:
    row = copy.deepcopy(row)
    if instance % 4 == 1:
        row["context"]["tools"].reverse()
    if instance % 4 == 2:
        row["context"]["resources"].reverse()
    if instance % 4 == 3:
        prior = row["context"].get("prior_results", {})
        row["context"]["prior_results"] = dict(reversed(list(prior.items())))
    return row


def generated_bounds(kind: str, template: int, instance: int) -> tuple[int, int]:
    digest = hashlib.sha256(
        f"release-generalization-v16-train-{kind}-{template}-{instance}".encode()
    ).hexdigest()
    rng = random.Random(digest)
    start = rng.randint(1, 180)
    end = start + rng.randint(0, 15)
    if kind == "invalid_range":
        start, end = (0, end) if instance % 2 else (end + 5, start)
    return start, end


def make_row(kind: str, language: str, family: int, instance: int) -> dict:
    template = 0 if language == "en" else 2
    seed_instance = family * 256 + instance
    row = make_release_task(kind, template, seed_instance, "train", "release-generalization-v16")
    row = vary_context(row, instance)
    row["language"] = language
    row["id"] = f"release-generalization-v16-{kind}-{language}-{family}-{instance:03d}"
    row["seed_id"] = row["id"]
    row["family_id"] = f"release-generalization-v16-{kind}-{language}-{family}"
    row["source"] = "fresh_authored_v16_external_failure_correction_training"
    start, end = generated_bounds(kind, template, seed_instance)
    values = {
        "path": row["args"].get("path", row["context"]["resources"][0]["config"]),
        "start": row["args"].get("start_line", start),
        "end": row["args"].get("end_line", end),
    }
    row["prompt"] = PROMPTS[kind][language].format(**values)
    if kind == "search":
        parts = row["args"]["cmd"].split("'")
        row["prompt"] += f" Marker: {parts[1]}. Directory: {parts[3]}."
    elif kind == "health":
        row["prompt"] += f" URL: {row['context']['prior_results'].get('health_url', '')}."
    return row


def key(row: dict) -> str:
    return canonical_json(public_record(row))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=False)
    parent_train = [json.loads(line) for line in (PARENT / "train.jsonl").read_text(encoding="utf-8").splitlines()]
    specs = {
        "invalid_range": (128, 32),
        "lines": (8, 32),
        "git_log": (8, 32),
        "config": (2, 32),
        "search": (2, 32),
        "health": (1, 32),
        "git_status": (1, 32),
    }
    additions = []
    for kind, (families, rows_per_family) in specs.items():
        for family in range(families):
            language = "en" if family % 2 == 0 else "zh"
            additions.extend(make_row(kind, language, family, instance) for instance in range(rows_per_family))
    if len(additions) != 4800:
        raise ValueError(f"expected 4800 correction rows, got {len(additions)}")

    all_train = additions + parent_train
    seen = defaultdict(set)
    labels = defaultdict(set)
    for row in all_train:
        seen[key(row)].add(row["id"])
        labels[key(row)].add(canonical_json({"tool": row["tool"], "args": row["args"]}))
    if any(len(values) > 1 for values in labels.values()):
        raise ValueError("label conflict")

    for split in ("train", "development", "evaluation"):
        destination = OUTPUT / f"{split}.jsonl"
        rows = all_train if split == "train" else [
            json.loads(line) for line in (PARENT / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        destination.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    if (OUTPUT / "development.jsonl").read_bytes() != (PARENT / "development.jsonl").read_bytes():
        raise ValueError("development changed")
    if (OUTPUT / "evaluation.jsonl").read_bytes() != (PARENT / "evaluation.jsonl").read_bytes():
        raise ValueError("evaluation changed")

    split_rows = {
        split: [json.loads(line) for line in (OUTPUT / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]
        for split in ("train", "development", "evaluation")
    }
    split_keys = {split: {key(row) for row in rows} for split, rows in split_rows.items()}
    split_families = {split: {row["family_id"] for row in rows} for split, rows in split_rows.items()}
    for left in split_keys:
        for right in split_keys:
            if left != right and split_keys[left] & split_keys[right]:
                raise ValueError("cross-split exact input overlap")
            if left != right and split_families[left] & split_families[right]:
                raise ValueError("cross-split family overlap")

    manifest = {
        "version": "release-generalization-v16",
        "source": "V15 train plus 4,800 fresh ordered invalid-range corrections; no scored rows imported.",
        "parent_train_sha256": hashlib.sha256((PARENT / "train.jsonl").read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "new_training_rows": len(additions),
        "ordered_correction_prefix_rows": len(additions),
        "development_unchanged": True,
        "evaluation_unchanged": True,
        "cross_split_families": 0,
        "cross_split_exact_inputs": 0,
        "target_balance": dict(Counter(row["kind"] for row in additions)),
        "splits": {},
    }
    for split, rows in split_rows.items():
        path = OUTPUT / f"{split}.jsonl"
        manifest["splits"][split] = {
            "tasks": len(rows),
            "families": len({row["family_id"] for row in rows}),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kinds": dict(Counter(row["kind"] for row in rows)),
            "languages": dict(Counter(row["language"] for row in rows)),
        }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
