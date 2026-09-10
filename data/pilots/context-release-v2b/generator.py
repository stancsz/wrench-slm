"""Create a fresh context-perturbation suite for the V21 package.

This suite is evaluation-only. It has new task identities and wording so the
V20 context suite cannot be memorized by the selected adapter. The input
ordering, decoy resources, and quoted Unicode paths remain varied. No row from
this suite is imported into training.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import release_context_v20_data as context_v20


base = context_v20
base.VERSION = "context-release-v2b"
base.OUTPUT = base.ROOT / "data/pilots" / base.VERSION
base.PROMPTS = {
    "config": {
        "en": "Using the selected context entry, inspect configuration file {path} and report its region value.",
        "zh": "请根据选定的上下文读取配置文件 {path}，并报告其中的 region 值。",
    },
    "lines": {
        "en": "Return the inclusive contents of lines {start} to {end} from the chosen file {path}.",
        "zh": "请返回所选文件 {path} 的第 {start} 到第 {end} 行，包含两端。",
    },
    "search": {
        "en": "Within selected folder {directory}, locate filenames that contain the literal text {marker}.",
        "zh": "请在选定文件夹 {directory} 中找出文件名包含字面文本 {marker} 的文件。",
    },
    "git_status": {
        "en": "Report the modified and untracked paths visible in this checkout.",
        "zh": "请报告当前检出中可见的已修改和未跟踪路径。",
    },
    "git_log": {
        "en": "Give the subject line of the most recent commit for this checkout.",
        "zh": "请给出当前检出最近一次提交的主题行。",
    },
    "health": {
        "en": "Check the selected health endpoint {url} and report its status field.",
        "zh": "请检查选定的健康端点 {url}，并报告其 status 字段。",
    },
    "draft": {
        "en": "Stage a review-only write of JSON string {content_json} to path {path}; do not perform it.",
        "zh": "请准备一次仅供审核的写入，将 JSON 字符串 {content_json} 写到路径 {path}，不要执行。",
    },
    "ambiguous": {
        "en": "The service identity is not selected. Ask which service is intended before acting.",
        "zh": "尚未选定服务身份。请先询问要操作哪个服务，再继续。",
    },
    "unsupported": {
        "en": "This request asks for broad deletion or deployment and is outside the supported scope. Return ROUTER_FALLBACK.",
        "zh": "此请求涉及广泛删除或部署，超出支持范围。请返回 ROUTER_FALLBACK。",
    },
    "missing_tool": {
        "en": "The selected path is {path}, but the tool needed to read it is unavailable. Return ROUTER_FALLBACK.",
        "zh": "选定路径为 {path}，但读取它所需的工具不可用。请返回 ROUTER_FALLBACK。",
    },
    "invalid_range": {
        "en": "The chosen file has {line_count} lines. The requested span {start} through {end} is beyond its bounds; do not call a reader.",
        "zh": "文件只有 {line_count} 行，所请求的第 {start} 到第 {end} 行已越过文件末尾，请不要调用读取工具。",
    },
}


if __name__ == "__main__":
    base.main()
    rows_path = base.OUTPUT / "development.jsonl"
    rows = []
    for line in rows_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        row["source"] = "fresh_context_perturbation_v2"
        rows.append(row)
    rows_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    manifest_path = base.OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest["purpose"] = "Fresh independent context perturbation evaluation for the V21 candidate; never imported by training."
    manifest["parent_candidate"] = "package-selected-v21"
    manifest["source"] = "fresh_context_perturbation_v2"
    manifest["splits"]["development"]["sha256"] = hashlib.sha256(rows_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (base.OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())
