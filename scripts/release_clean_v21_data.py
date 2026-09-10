"""Build V21 with natural Chinese beyond-EOF abstention wording.

The V20 context suite found three Chinese beyond-EOF cases where the model
called ``read_file`` after being told only that the range was invalid. V21
adds training variants that state the public file length and prohibit reading
without repeating the fallback token.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import release_clean_v20_data as v20  # noqa: E402


base = v20.base
base.VERSION = "release-generalization-v21"
base.OUTPUT = base.ROOT / "data/pilots" / base.VERSION
base.PROMPTS = deepcopy(base.PROMPTS)
base.PROMPTS["train"]["invalid_range"]["zh"] = (
    "选中文件有 {line_count} 行，请求的第 {start} 到第 {end} 行超出文件范围。不要读取该文件。",
    "选中文件有 {line_count} 行，第 {start} 至第 {end} 行不可用。请不要调用任何工具，直接回退。",
    "请返回一个 JSON fallback，因为第 {start} 到第 {end} 行不在 {line_count} 行文件内，不要调用 read_file。",
    "文件长度为 {line_count} 行。请求的第 {start} 至第 {end} 行无效，请停止读取并回退。",
)


if __name__ == "__main__":
    base.main()
    manifest_path = base.OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest["training_stream"] += "; natural Chinese invalid-range abstention variants"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (base.OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())
