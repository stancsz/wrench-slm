"""Build V18 from the clean V17 generator with explicit range-call replay.

V17 exposed a repeatable development weakness: three Chinese line-range cases
returned the file length as ``end_line``. V18 keeps the clean data contract and
adds varied explicit JSON argument wording to the training stream. Its new
development and evaluation splits are distinct versioned artifacts.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import release_clean_v17_data as base


base.VERSION = "release-generalization-v18"
base.OUTPUT = base.ROOT / "artifacts/archive/data/pilots" / base.VERSION
base.PROMPTS = deepcopy(base.PROMPTS)
base.PROMPTS["train"]["lines"] = {
    "en": (
        "Retrieve inclusive lines {start} through {end} from the selected file {path}.",
        "Show the selected file {path} from line {start} to line {end}, including both ends.",
        "Return one JSON read_file call with path {path}, start_line {start}, and end_line {end}.",
        "The selected file has {line_count} lines. Use read_file with path {path}, start_line {start}, and end_line {end}.",
    ),
    "zh": (
        "请读取选中文件 {path} 的第 {start} 到第 {end} 行，包括首尾。",
        "显示选中文件 {path} 中从第 {start} 行到第 {end} 行的内容。",
        "请返回一个 JSON read_file 调用，path 为 {path}，start_line 为 {start}，end_line 为 {end}。",
        "选中文件有 {line_count} 行。请使用 read_file，path 为 {path}，start_line 为 {start}，end_line 为 {end}。",
    ),
}


if __name__ == "__main__":
    base.main()
    manifest_path = base.OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (base.OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())
