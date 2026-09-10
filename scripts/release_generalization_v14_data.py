"""Build V14 training-only corrections from the V13 training split.

V14 concentrates on the remaining external failures: explicit invalid-range
abstention, JSON health-call formatting, literal search target selection, and
English and Chinese Git command choice. Development and evaluation files are
copied byte-for-byte from V13 and no scored rows are imported.
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


PARENT = ROOT / "data/pilots/release-generalization-v13"
OUTPUT = ROOT / "data/pilots/release-generalization-v14"

PROMPTS = {
    "invalid_range": {
        "en": [
            "The requested line interval is invalid. Do not call read_file; return ROUTER_FALLBACK.",
            "These bounds cannot be served. Abstain explicitly and emit the fallback token, with no tool call.",
            "Reject this out-of-range or reversed request. Never read the file; use the fallback action.",
            "The selected path is known, but the requested lines are invalid. Return ROUTER_FALLBACK only.",
        ],
        "zh": [
            "请求的行范围无效。不要调用 read_file，请返回 ROUTER_FALLBACK。",
            "这些起止行不能处理，请明确放弃，不要发出任何工具调用。",
            "拒绝这个越界或反向请求，不要读取文件，使用回退动作。",
            "目标路径已知，但行号无效，请只返回 ROUTER_FALLBACK。",
        ],
    },
    "health": {
        "en": [
            "Use the listed read-only curl health command exactly and return a JSON tool call, not prose.",
            "Inspect the health endpoint with curl --silent --show-error --max-time 3; emit the command as JSON.",
            "The correct action is the allowlisted curl command. Do not answer healthy or degraded in plain text.",
            "Call the health URL with the exact curl flags from the tool description, then let execution report status.",
        ],
        "zh": [
            "请严格使用工具描述中的只读 curl 健康检查命令，并返回 JSON 工具调用，不要输出散文。",
            "用 curl --silent --show-error --max-time 3 检查健康端点，把命令作为 JSON 返回。",
            "正确动作是允许的 curl 命令，不要直接用文字回答 healthy 或 degraded。",
            "按工具描述的精确 curl 参数调用健康 URL，让执行结果报告状态。",
        ],
    },
    "search": {
        "en": [
            "Search the selected directory for the literal marker. Use prior_results.selected_directory, never selected_file.",
            "Run the fixed-string rg filename search below the selected directory, not against a configuration path.",
            "The folder is the search target. Treat the marker literally and return the allowlisted rg command as JSON.",
            "Use the directory named in context for the search; do not substitute the selected service config file.",
        ],
        "zh": [
            "请在上下文选中的目录中搜索固定标记，使用 prior_results.selected_directory，不要使用 selected_file。",
            "对选中目录执行固定字符串 rg 文件名搜索，不要把配置路径当作搜索目录。",
            "搜索目标是文件夹，请按原文处理标记，并把允许的 rg 命令作为 JSON 返回。",
            "使用上下文中的选定目录进行搜索，不要替换成选中服务的配置文件。",
        ],
    },
    "git_status": {
        "en": [
            "Run git status --short to list modified and untracked paths. This is a read-only status request.",
            "Show the working-tree changes with the exact git status --short command; do not abstain.",
            "Inspect repository status and return the allowlisted git status command as JSON.",
            "List changed and new files from the checkout using git status --short.",
        ],
        "zh": [
            "请使用 git status --short 列出已修改和未跟踪路径，这是只读状态请求，不要回退。",
            "用精确的 git status --short 查看工作树变动，请返回 JSON 工具调用。",
            "检查仓库状态并返回允许的 git status 命令，不要明确放弃。",
            "使用 git status --short 列出当前检出目录的修改和新增文件。",
        ],
    },
    "git_log": {
        "en": [
            "Run git log -1 --format=%s to read the latest commit subject.",
            "Use the exact read-only git log command for the most recent commit title.",
            "Return a JSON call to git log -1 --format=%s; do not use git status.",
            "Read only the latest commit subject with the allowlisted git log command.",
        ],
        "zh": [
            "请运行 git log -1 --format=%s 读取最近提交主题，不要使用 git status。",
            "使用精确的只读 git log 命令获取最新提交标题。",
            "请返回 git log -1 --format=%s 的 JSON 调用，不要回退或改用状态命令。",
            "只用允许的 git log 命令读取最近一次提交主题。",
        ],
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


def make_row(kind: str, language: str, family: int, instance: int) -> dict:
    template = 0 if language == "en" else 2
    row = make_release_task(kind, template, family * 64 + instance, "train", "release-generalization-v14")
    row = vary_context(row, instance)
    row["language"] = language
    row["id"] = f"release-generalization-v14-{kind}-{language}-{family}-{instance:03d}"
    row["seed_id"] = row["id"]
    row["family_id"] = f"release-generalization-v14-{kind}-{language}-{family}"
    row["source"] = "fresh_authored_v14_external_failure_correction_training"
    row["prompt"] = PROMPTS[kind][language][family % len(PROMPTS[kind][language])]
    if kind == "invalid_range":
        base = make_release_task(kind, template, family * 64 + instance, "train", "release-generalization-v14")
        row["prompt"] += " " + base["prompt"]
    elif kind == "health":
        row["prompt"] += " " + row["context"]["prior_results"].get("health_url", "")
    elif kind == "search":
        base = make_release_task(kind, template, family * 64 + instance, "train", "release-generalization-v14")
        row["prompt"] += " " + base["prompt"]
    return row


def key(row: dict) -> str:
    return canonical_json(public_record(row))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=False)
    parent_train = [json.loads(line) for line in (PARENT / "train.jsonl").read_text(encoding="utf-8").splitlines()]
    additions = []
    specs = {
        "invalid_range": (32, 64),
        "health": (16, 64),
        "search": (16, 64),
        "git_status": (8, 64),
        "git_log": (8, 64),
    }
    for kind, (families, rows_per_family) in specs.items():
        for family in range(families):
            language = "en" if family % 2 == 0 else "zh"
            additions.extend(make_row(kind, language, family, instance) for instance in range(rows_per_family))

    all_train = parent_train + additions
    random.Random("shuffle-release-generalization-v14").shuffle(all_train)
    seen = defaultdict(set)
    labels = defaultdict(set)
    for row in all_train:
        seen[key(row)].add(row["id"])
        labels[key(row)].add(canonical_json({"tool": row["tool"], "args": row["args"]}))
    if any(len(values) > 1 for values in labels.values()):
        raise ValueError("label conflict")

    for split in ("train", "development", "evaluation"):
        destination = OUTPUT / f"{split}.jsonl"
        if split == "train":
            rows = all_train
        else:
            rows = [json.loads(line) for line in (PARENT / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]
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
        "version": "release-generalization-v14",
        "source": "V13 train plus fresh external-failure corrections; no scored rows imported.",
        "parent_train_sha256": hashlib.sha256((PARENT / "train.jsonl").read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "new_training_rows": len(additions),
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
