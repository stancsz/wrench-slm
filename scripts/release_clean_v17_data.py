"""Build a semantically audited, mixed-stream V17 release dataset.

V17 is intentionally generated from resettable fixtures rather than inheriting
the V16 training file. The training stream is balanced and interleaved so each
selectable checkpoint sees every task kind and both languages. Development and
evaluation use separate wording and family identifiers and are written before
training starts.
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

from wrench.pilot_tasks import make_task  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402
from wrench.pilot_tasks import public_record  # noqa: E402


VERSION = "release-generalization-v17"
OUTPUT = ROOT / "artifacts/archive/data/pilots" / VERSION
KINDS = (
    "config", "lines", "search", "git_status", "git_log", "health",
    "draft", "ambiguous", "unsupported", "missing_tool", "invalid_range",
)
TRAIN_ROWS_PER_KIND = 512
DEVELOPMENT_ROWS_PER_KIND = 16
EVALUATION_ROWS_PER_KIND = 40
LINE_COUNT = 15


PROMPTS = {
    "train": {
        "config": {
            "en": (
                "Read the selected configuration at {path} and return its region.",
                "Which deployment region is recorded in the selected file {path}?",
            ),
            "zh": (
                "请读取选中的配置文件 {path}，返回其中的 region。",
                "选中的文件 {path} 记录了哪个部署 region？",
            ),
        },
        "lines": {
            "en": (
                "Retrieve inclusive lines {start} through {end} from the selected file {path}.",
                "Show the selected file {path} from line {start} to line {end}, including both ends.",
            ),
            "zh": (
                "请读取选中文件 {path} 的第 {start} 到第 {end} 行，包括首尾。",
                "显示选中文件 {path} 中从第 {start} 行到第 {end} 行的内容。",
            ),
        },
        "search": {
            "en": (
                "Find files under {directory} containing the literal marker {marker}.",
                "Search {directory} for the exact text {marker} and return matching filenames.",
            ),
            "zh": (
                "请在 {directory} 下查找包含字面标记 {marker} 的文件。",
                "在 {directory} 中搜索原样文本 {marker}，返回匹配的文件名。",
            ),
        },
        "git_status": {
            "en": (
                "Inspect this checkout and list changed or untracked paths.",
                "Show the read-only short Git status for this working tree.",
            ),
            "zh": (
                "请检查当前检出目录并列出已修改或未跟踪的路径。",
                "请以只读方式显示当前工作树的简短 Git 状态。",
            ),
        },
        "git_log": {
            "en": (
                "Read the subject of the newest commit in this checkout.",
                "Return the latest Git commit subject from local history.",
            ),
            "zh": (
                "请读取当前检出目录最近一次提交的主题。",
                "返回本地历史中最新 Git 提交的主题行。",
            ),
        },
        "health": {
            "en": (
                "Query the selected health endpoint {url} and report its status.",
                "Use the service health URL {url} to retrieve the status field.",
            ),
            "zh": (
                "请访问选中的健康检查地址 {url} 并返回 status。",
                "使用服务健康地址 {url} 获取 status 字段。",
            ),
        },
        "draft": {
            "en": (
                "Prepare a review-only write proposal for {path}; the exact JSON string content is {content_json}.",
                "Draft, without executing, a write of JSON string {content_json} decoded into {path}.",
            ),
            "zh": (
                "请为 {path} 准备仅供审核的写入草稿，精确内容是 JSON 字符串 {content_json}。",
                "不要执行写入，请把 JSON 字符串 {content_json} 解码后拟写入 {path}。",
            ),
        },
        "ambiguous": {
            "en": (
                "I have not selected a service. Ask for clarification instead of choosing a configuration.",
                "No service is selected yet. Do not guess a target; request clarification.",
            ),
            "zh": (
                "我还没有选定服务。请请求澄清，不要自行选择配置。",
                "当前没有选中的服务。不要猜测目标，请先请求澄清。",
            ),
        },
        "unsupported": {
            "en": (
                "This request would delete or deploy broadly and is outside the read-only contract. Use ROUTER_FALLBACK.",
                "The requested system-wide change is unsupported here. Return ROUTER_FALLBACK without a tool call.",
            ),
            "zh": (
                "这个请求会进行广泛删除或部署，超出只读范围。请返回 ROUTER_FALLBACK。",
                "所请求的系统级变更不受支持。不要调用工具，请返回 ROUTER_FALLBACK。",
            ),
        },
        "missing_tool": {
            "en": (
                "The selected file is {path}, but the required read tool is unavailable. Use ROUTER_FALLBACK.",
                "Reading {path} needs a tool that is not provided. Return ROUTER_FALLBACK.",
            ),
            "zh": (
                "选中文件是 {path}，但缺少读取所需的工具。请返回 ROUTER_FALLBACK。",
                "读取 {path} 需要的工具没有提供。请返回 ROUTER_FALLBACK。",
            ),
        },
        "invalid_range": {
            "en": (
                "The selected file has {line_count} lines and the requested inclusive bounds are {start} through {end}. The range is invalid. Return ROUTER_FALLBACK without calling read_file.",
                "The file length is {line_count}; bounds {start} through {end} cannot be served. Do not call read_file. Return ROUTER_FALLBACK.",
            ),
            "zh": (
                "选中文件有 {line_count} 行，请求的包含首尾范围是第 {start} 到第 {end} 行，范围无效。不要调用 read_file，请返回 ROUTER_FALLBACK。",
                "文件长度为 {line_count} 行，第 {start} 到第 {end} 行无法读取。不要调用 read_file，请返回 ROUTER_FALLBACK。",
            ),
        },
    },
    "development": {
        "config": {
            "en": ("For the chosen service, inspect {path} and report the configured region.",),
            "zh": ("请检查所选服务的 {path}，返回配置的 region。",),
        },
        "lines": {
            "en": ("Give the inclusive excerpt {start} to {end} from {path}.",),
            "zh": ("请返回 {path} 中第 {start} 到第 {end} 行的包含首尾片段。",),
        },
        "search": {
            "en": ("Which files below {directory} contain the exact marker {marker}?",),
            "zh": ("{directory} 下哪些文件包含精确标记 {marker}？",),
        },
        "git_status": {
            "en": ("What paths does the short status report as changed or untracked?",),
            "zh": ("简短状态报告了哪些已修改或未跟踪路径？",),
        },
        "git_log": {
            "en": ("What subject is recorded on the tip commit?",),
            "zh": ("最新提交记录的主题是什么？",),
        },
        "health": {
            "en": ("What status does the selected endpoint {url} report?",),
            "zh": ("选中的端点 {url} 报告了什么 status？",),
        },
        "draft": {
            "en": ("For review, propose writing {content_json} as decoded text to {path}; do not apply it.",),
            "zh": ("请审核拟案：将 {content_json} 解码后写入 {path}，不要实际执行。",),
        },
        "ambiguous": {
            "en": ("The service identity is missing. Ask for clarification before reading configuration.",),
            "zh": ("缺少服务身份信息。读取配置前请先请求澄清。",),
        },
        "unsupported": {
            "en": ("A broad destructive or deployment action is outside this worker's scope. Fall back.",),
            "zh": ("广泛删除或部署不在此工作器范围内，请执行回退。",),
        },
        "missing_tool": {
            "en": ("The path is {path}, but no file-reading tool is available. Fall back.",),
            "zh": ("目标路径是 {path}，但没有文件读取工具，请回退。",),
        },
        "invalid_range": {
            "en": ("The file has {line_count} lines, but {start} through {end} is invalid. Abstain without reading.",),
            "zh": ("文件有 {line_count} 行，但第 {start} 到第 {end} 行无效。不要读取，请回退。",),
        },
    },
    "evaluation": {
        "config": {
            "en": ("Look up the region value in the selected configuration file {path}.",),
            "zh": ("请从选定配置文件 {path} 中查找 region 值。",),
        },
        "lines": {
            "en": ("Return only the selected interval of {path}, from line {start} through {end}.",),
            "zh": ("请只返回选定文件 {path} 的第 {start} 至第 {end} 行。",),
        },
        "search": {
            "en": ("Locate every filename under {directory} that contains literal text {marker}.",),
            "zh": ("请找出 {directory} 下包含字面文本 {marker} 的所有文件名。",),
        },
        "git_status": {
            "en": ("List the paths that are dirty in this checkout.",),
            "zh": ("请列出当前检出目录中处于脏状态的路径。",),
        },
        "git_log": {
            "en": ("Return the title of the most recent local commit.",),
            "zh": ("请返回本地最近一次提交的标题。",),
        },
        "health": {
            "en": ("Read the status field served at {url}.",),
            "zh": ("请读取 {url} 提供的 status 字段。",),
        },
        "draft": {
            "en": ("Create a write proposal for {path} whose exact decoded body is {content_json}; leave the filesystem unchanged.",),
            "zh": ("请为 {path} 创建写入提案，精确解码正文为 {content_json}，不要改变文件系统。",),
        },
        "ambiguous": {
            "en": ("There is no selected service identity. Do not infer one; ask for clarification.",),
            "zh": ("没有选中的服务身份。不要推断目标，请请求澄清。",),
        },
        "unsupported": {
            "en": ("The request requires an unsupported broad system action. Return the fallback response.",),
            "zh": ("该请求需要不受支持的广泛系统操作，请返回回退响应。",),
        },
        "missing_tool": {
            "en": ("The requested file is {path}, but its reading capability is absent. Return the fallback response.",),
            "zh": ("请求文件是 {path}，但缺少读取能力，请返回回退响应。",),
        },
        "invalid_range": {
            "en": ("The disclosed file length is {line_count}; the inclusive request {start} through {end} is invalid. Return the fallback response.",),
            "zh": ("已披露文件长度为 {line_count} 行，第 {start} 到第 {end} 行的请求无效，请返回回退响应。",),
        },
    },
}


def _replace(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [_replace(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: _replace(item, old, new) for key, item in value.items()}
    return value


def _base_kind(kind):
    if kind in {"lines", "invalid_range"}:
        return "lines"
    if kind == "draft":
        return "draft"
    if kind in {"config", "missing_tool", "unsupported"}:
        return "config"
    return kind


def _invalid_bounds(instance):
    category = instance % 3
    if category == 0:
        return "zero_or_negative", 0, 3
    if category == 1:
        return "reversed", 10, 4
    return "beyond_eof", LINE_COUNT - 1, LINE_COUNT + 4


def make_row(kind, split, instance, language, family):
    seed = f"{VERSION}-{split}-{kind}-{instance}"
    base = make_task(_base_kind(kind), 0, instance, seed)
    row = copy.deepcopy(base)
    port = str(19000 + (int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % 1000))
    row = _replace(row, "__PORT__", port)
    context = row["context"]
    prior = context.setdefault("prior_results", {})
    path = prior.get("selected_file")
    directory = prior.get("selected_directory")
    if kind in {"lines", "invalid_range"}:
        prior["selected_file_line_count"] = LINE_COUNT
    values = {"path": path, "directory": directory}
    if kind in {"lines", "invalid_range"}:
        values.update({"start": row["args"].get("start_line"), "end": row["args"].get("end_line"), "line_count": LINE_COUNT})
    if kind == "draft":
        values["content_json"] = json.dumps(row["args"]["content"], ensure_ascii=False)
    if kind == "health":
        values["url"] = prior["health_url"]
    if kind == "search":
        folder = prior["selected_directory"]
        module = f"{folder}/module_1.txt"
        marker = row["fixture"]["files"][module].removeprefix("reference ").strip()
        row["args"]["cmd"] = f"rg -l --fixed-strings -- '{marker}' '{folder}'"
        values["marker"] = marker
    if kind == "invalid_range":
        category, start, end = _invalid_bounds(instance)
        values.update(start=start, end=end)
        row["metadata"] = {"boundary_category": category}
        row["tool"] = "fallback"
        row["args"] = {}
        row["expected_answer"] = "NEEDS_CLARIFICATION"
    elif kind in {"ambiguous", "unsupported", "missing_tool"}:
        row["tool"] = "fallback"
        row["args"] = {}
        row["expected_answer"] = "NEEDS_CLARIFICATION"
        if kind == "ambiguous":
            context["prior_results"] = {}
        elif kind == "missing_tool":
            context["tools"] = [tool for tool in context["tools"] if tool["name"] == "write_file"]
    row["id"] = f"{VERSION}-{split}-{kind}-{instance:04d}"
    row["family_id"] = f"{VERSION}-{split}-{kind}-family-{family:03d}"
    row["seed_id"] = row["id"]
    row["source"] = f"clean_authored_{VERSION}"
    row["kind"] = kind
    row["language"] = language
    template = PROMPTS[split][kind][language][instance % len(PROMPTS[split][kind][language])]
    row["prompt"] = template.format(**values)
    return row


def _make_split(split, rows_per_kind):
    rows = []
    for kind in KINDS:
        for instance in range(rows_per_kind):
            language = "en" if instance % 2 == 0 else "zh"
            family = instance // 32 if split == "train" else 0
            rows.append(make_row(kind, split, instance, language, family))
    if split == "train":
        buckets = {kind: [row for row in rows if row["kind"] == kind] for kind in KINDS}
        rows = []
        for index in range(rows_per_kind):
            for kind in KINDS:
                rows.append(buckets[kind][index])
    else:
        random.Random(f"{VERSION}-{split}-order").shuffle(rows)
    return rows


def _manifest_for(rows_by_split):
    keys = {split: {canonical_json(public_record(row)) for row in rows} for split, rows in rows_by_split.items()}
    families = {split: {row["family_id"] for row in rows} for split, rows in rows_by_split.items()}
    for left in rows_by_split:
        for right in rows_by_split:
            if left == right:
                continue
            if keys[left] & keys[right]:
                raise ValueError(f"cross-split public input overlap: {left} {right}")
            if families[left] & families[right]:
                raise ValueError(f"cross-split family overlap: {left} {right}")
    manifest = {
        "version": VERSION,
        "source": "Fresh resettable fixtures with public-input semantic checks; no historical scored rows imported.",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "line_count_public": LINE_COUNT,
        "training_stream": "kind-round-robin, deterministic, language-alternating within each kind",
        "cross_split_families": 0,
        "cross_split_exact_inputs": 0,
        "splits": {},
    }
    for split, rows in rows_by_split.items():
        path = OUTPUT / f"{split}.jsonl"
        manifest["splits"][split] = {
            "tasks": len(rows),
            "families": len({row["family_id"] for row in rows}),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kinds": dict(Counter(row["kind"] for row in rows)),
            "languages": dict(Counter(row["language"] for row in rows)),
        }
    return manifest


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    OUTPUT.mkdir(parents=True)
    rows_by_split = {
        "train": _make_split("train", TRAIN_ROWS_PER_KIND),
        "development": _make_split("development", DEVELOPMENT_ROWS_PER_KIND),
        "evaluation": _make_split("evaluation", EVALUATION_ROWS_PER_KIND),
    }
    for split, rows in rows_by_split.items():
        (OUTPUT / f"{split}.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
        )
    manifest = _manifest_for(rows_by_split)
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
