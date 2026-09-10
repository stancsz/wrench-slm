"""Create an independent context-perturbation suite for the V20 package.

The suite uses fresh task identities and wording, while varying tool order,
resource order, prior-result order, decoys, quoted paths, and Unicode paths.
It is evaluation-only and is never imported by training.
"""

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import make_task, public_record  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402


VERSION = "context-release-v1"
OUTPUT = ROOT / "artifacts/archive/data/pilots" / VERSION
KINDS = (
    "config", "lines", "search", "git_status", "git_log", "health",
    "draft", "ambiguous", "unsupported", "missing_tool", "invalid_range",
)
ROWS_PER_KIND = 20
LINE_COUNT = 15

PROMPTS = {
    "config": {
        "en": "With the context as supplied, read the selected configuration {path} and return its region.",
        "zh": "请按照当前上下文读取选中的配置 {path}，返回其中的 region。",
    },
    "lines": {
        "en": "From selected file {path}, return inclusive lines {start} through {end}.",
        "zh": "请从选中文件 {path} 返回第 {start} 至第 {end} 行，包括首尾。",
    },
    "search": {
        "en": "Under the selected directory {directory}, find filenames containing literal {marker}.",
        "zh": "请在选定目录 {directory} 下查找包含字面标记 {marker} 的文件名。",
    },
    "git_status": {
        "en": "Inspect the checkout and list its changed or untracked paths.",
        "zh": "请检查当前检出目录并列出已修改或未跟踪的路径。",
    },
    "git_log": {
        "en": "Read the subject of the newest commit in this checkout.",
        "zh": "请读取当前检出目录最近一次提交的主题。",
    },
    "health": {
        "en": "Use the selected health address {url} and report its status.",
        "zh": "请使用选中的健康地址 {url} 并返回 status。",
    },
    "draft": {
        "en": "Prepare a review-only write of decoded JSON string {content_json} to {path}.",
        "zh": "请准备仅供审核的写入：将 JSON 字符串 {content_json} 解码后写入 {path}。",
    },
    "ambiguous": {
        "en": "No service identity is selected. Ask for clarification instead of guessing.",
        "zh": "没有选中的服务身份。请请求澄清，不要猜测目标。",
    },
    "unsupported": {
        "en": "This broad destructive or deployment request is outside scope. Return ROUTER_FALLBACK.",
        "zh": "这个广泛删除或部署请求超出范围，请返回 ROUTER_FALLBACK。",
    },
    "missing_tool": {
        "en": "The selected path is {path}, but its required read tool is absent. Return ROUTER_FALLBACK.",
        "zh": "选中的路径是 {path}，但缺少所需读取工具，请返回 ROUTER_FALLBACK。",
    },
    "invalid_range": {
        "en": "The selected file has {line_count} lines; bounds {start} through {end} are invalid. Do not read it.",
        "zh": "选中文件有 {line_count} 行，第 {start} 至第 {end} 行无效，不要读取。",
    },
}


def _replace(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [_replace(item, old, new) for item in value]
    if isinstance(value, dict):
        return {_replace(key, old, new): _replace(item, old, new) for key, item in value.items()}
    return value


def make_row(kind, index):
    language = "en" if index % 2 == 0 else "zh"
    variant = index % 4
    base_kind = "lines" if kind == "invalid_range" else kind
    if kind in {"unsupported", "missing_tool"}:
        base_kind = "config"
    row = copy.deepcopy(make_task(base_kind, 0, index, f"{VERSION}-{kind}"))
    port = str(20000 + (int(hashlib.sha256(row["id"].encode()).hexdigest()[:8], 16) % 1000))
    row = _replace(row, "__PORT__", port)
    prior = row["context"].setdefault("prior_results", {})
    selected_file = prior.get("selected_file")
    selected_directory = prior.get("selected_directory")
    digest = hashlib.sha256(row["id"].encode()).hexdigest()[:8]
    new_file = f"project files/配置's-{digest}.txt"
    new_directory = f"src/组件 files-{digest}"
    if selected_file:
        row = _replace(row, selected_file, new_file)
    if selected_directory:
        row = _replace(row, selected_directory, new_directory)
    prior = row["context"].setdefault("prior_results", {})
    if kind in {"lines", "invalid_range"}:
        prior["selected_file_line_count"] = LINE_COUNT
    if kind == "search":
        folder = prior["selected_directory"]
        marker = row["fixture"]["files"][f"{folder}/module_1.txt"].removeprefix("reference ").strip()
        row["args"]["cmd"] = f"rg -l --fixed-strings -- '{marker}' '{folder}'"
        values = {"directory": folder, "marker": marker}
    elif kind == "health":
        values = {"url": prior["health_url"]}
    elif kind == "draft":
        values = {"path": prior["selected_file"], "content_json": json.dumps(row["args"]["content"], ensure_ascii=False)}
    elif kind in {"config", "missing_tool"}:
        values = {"path": prior["selected_file"]}
    elif kind in {"lines", "invalid_range"}:
        values = {"path": prior["selected_file"], "line_count": LINE_COUNT}
        if kind == "lines":
            values.update(start=row["args"]["start_line"], end=row["args"]["end_line"])
        else:
            category = index % 3
            if category == 0:
                boundary, start, end = "zero_or_negative", 0, 3
            elif category == 1:
                boundary, start, end = "reversed", 10, 4
            else:
                boundary, start, end = "beyond_eof", LINE_COUNT - 1, LINE_COUNT + 4
            row["metadata"] = {"boundary_category": boundary}
            row["tool"], row["args"], row["expected_answer"] = "fallback", {}, "NEEDS_CLARIFICATION"
            values.update(start=start, end=end)
    else:
        values = {}
    if kind == "ambiguous":
        row["context"]["prior_results"] = {}
        row["tool"], row["args"], row["expected_answer"] = "fallback", {}, "NEEDS_CLARIFICATION"
    elif kind in {"unsupported", "missing_tool"}:
        row["tool"], row["args"], row["expected_answer"] = "fallback", {}, "NEEDS_CLARIFICATION"
        if kind == "missing_tool":
            row["context"]["tools"] = [tool for tool in row["context"]["tools"] if tool["name"] == "write_file"]
    if variant == 0:
        row["context"]["tools"].reverse()
    elif variant == 1:
        row["context"]["resources"].reverse()
    elif variant == 2 and row["context"].get("prior_results"):
        prior = row["context"]["prior_results"]
        row["context"]["prior_results"] = dict(reversed(list(prior.items())))
    decoy = {"service": f"decoy-{digest}", "config": f"decoys/配置-{digest}.json"}
    row["context"]["resources"].append(decoy)
    row["fixture"]["files"][decoy["config"]] = "{\"service\": \"%s\", \"region\": \"decoy\"}" % decoy["service"]
    row["id"] = f"{VERSION}-development-{kind}-{index:03d}"
    row["family_id"] = f"{VERSION}-development-{kind}-variant-{variant}"
    row["seed_id"] = row["id"]
    row["source"] = "fresh_context_perturbation_v1"
    row["kind"] = kind
    row["language"] = language
    row["prompt"] = PROMPTS[kind][language].format(**values)
    return row


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    OUTPUT.mkdir(parents=True)
    rows = [make_row(kind, index) for kind in KINDS for index in range(ROWS_PER_KIND)]
    random.Random(VERSION).shuffle(rows)
    path = OUTPUT / "development.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    keys = {canonical_json(public_record(row)) for row in rows}
    if len(keys) != len(rows):
        raise ValueError("duplicate context inputs")
    manifest = {
        "version": VERSION,
        "purpose": "Independent context perturbation evaluation for the V20 candidate; never imported by training.",
        "parent_candidate": "package-selected-v20",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "context_variants": ["reordered tools", "reordered resources", "reordered prior results", "quoted and Unicode paths", "decoy resource"],
        "splits": {"development": {"tasks": len(rows), "families": len({row["family_id"] for row in rows}),
                                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                    "kinds": dict(Counter(row["kind"] for row in rows)),
                                    "languages": dict(Counter(row["language"] for row in rows))}},
        "cross_split_families": 0,
        "cross_split_exact_inputs": 0,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
