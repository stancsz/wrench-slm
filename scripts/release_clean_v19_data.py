"""Build V19 with a deliberate extra line-range replay fraction.

V18 improved the Chinese line slice but still missed two of sixteen
development cases at every checkpoint. V19 keeps the audited contract and
places two line-range examples around each example from the other task kinds
in the first 6,144 training rows. This gives the planned 300-step run a
substantive, measured correction without changing the public holdout contract.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import release_clean_v18_data as v18  # noqa: E402


base = v18.base
base.VERSION = "release-generalization-v19"
base.OUTPUT = base.ROOT / "data/pilots" / base.VERSION
base.PROMPTS = deepcopy(base.PROMPTS)


def _mixed_train(rows_per_kind):
    counts = {kind: 512 for kind in base.KINDS}
    counts["lines"] = 1024
    buckets = {}
    for kind in base.KINDS:
        bucket = []
        for instance in range(counts[kind]):
            language = "en" if instance % 2 == 0 else "zh"
            family = instance // 32
            bucket.append(base.make_row(kind, "train", instance, language, family))
        buckets[kind] = bucket
    non_lines = [kind for kind in base.KINDS if kind != "lines"]
    rows = []
    for index in range(512):
        rows.extend(buckets[kind][index] for kind in non_lines)
        rows.extend(buckets["lines"][2 * index:2 * index + 2])
    return rows


_original_make_split = base._make_split


def _make_split(split, rows_per_kind):
    if split == "train":
        return _mixed_train(rows_per_kind)
    return _original_make_split(split, rows_per_kind)


base._make_split = _make_split


if __name__ == "__main__":
    base.main()
    manifest_path = base.OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest["training_stream"] = "one row per non-line kind followed by two line rows, language-alternating"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (base.OUTPUT / "generator.py").write_bytes(Path(__file__).read_bytes())
