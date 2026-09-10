"""Build V20 with Chinese ``至`` line-range wording in training replay.

The V19 holdout showed nine Chinese line-range misses on wording that used
``至`` while training mostly used ``到``. V20 adds that phrasing to the clean,
line-weighted stream. The V19 holdout remains diagnostic and is not imported.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import release_clean_v19_data as v19  # noqa: E402


base = v19.base
base.VERSION = "release-generalization-v20"
base.OUTPUT = base.ROOT / "artifacts/model-release/generated" / base.VERSION
base.PROMPTS = deepcopy(base.PROMPTS)
base.PROMPTS["train"]["lines"]["zh"] = (
    "请读取选中文件 {path} 的第 {start} 到第 {end} 行，包括首尾。",
    "请读取选中文件 {path} 的第 {start} 至第 {end} 行，包括首尾。",
    "请返回一个 JSON read_file 调用，path 为 {path}，start_line 为 {start}，end_line 为 {end}。",
    "选中文件有 {line_count} 行。请使用 read_file，path 为 {path}，start_line 为 {start}，end_line 为 {end}。",
)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New directory under artifacts/")
    args = parser.parse_args()
    if args.output:
        target = args.output.resolve()
        if not target.is_relative_to(ROOT / "artifacts") or target == ROOT / "artifacts":
            parser.error("Output must be a new subdirectory of artifacts/")
        base.OUTPUT = target
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        base.main()
    manifest_path = base.OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest["training_stream"] += "; Chinese line wording includes 到 and 至 variants"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (base.OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
