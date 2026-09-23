"""Complete SWE-Explore task metadata from its pinned official source datasets."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).parent
DATA = ROOT / "data"
BENCH = DATA / "bench.final.public.jsonl"
ISSUE_MAP = DATA / "issue_map_and_commits.json"
UNMATCHED = DATA / "unmatched-ids.json"
MULTILINGUAL = (
    DATA
    / "source-snapshots"
    / "SWE-bench__SWE-bench_Multilingual"
    / "data"
    / "test-00000-of-00001.parquet"
)


def main() -> None:
    rows = [json.loads(line) for line in BENCH.read_text(encoding="utf-8").splitlines()]
    issue_map = json.loads(ISSUE_MAP.read_text(encoding="utf-8"))
    multi = pq.read_table(MULTILINGUAL).to_pylist()
    by_id = {row["instance_id"]: row for row in multi}

    added = 0
    for bench_row in rows:
        iid = bench_row["instance_id"]
        if iid in issue_map:
            continue
        source = by_id.get(iid)
        if source is None:
            continue
        issue_map[iid] = {
            "instance_id": iid,
            "repo": source["repo"],
            "base_commit": source["base_commit"],
            "problem_statement": source["problem_statement"],
            "source": "SWE-bench/SWE-bench_Multilingual@7566cd247075886ef34453ff5582908c0255f5e6",
        }
        added += 1

    missing = sorted({row["instance_id"] for row in rows} - issue_map.keys())
    if len(issue_map) != len(set(issue_map)):
        raise ValueError("duplicate source map ids")
    ISSUE_MAP.write_text(
        json.dumps(issue_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    UNMATCHED.write_text(json.dumps(missing, indent=2) + "\n", encoding="utf-8")

    manifest_path = DATA / "issue-source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"].append(
        "SWE-bench/SWE-bench_Multilingual@7566cd247075886ef34453ff5582908c0255f5e6"
    )
    manifest.update(
        {
            "bench_rows": len(rows),
            "matched_rows": len(set(row["instance_id"] for row in rows) & issue_map.keys()),
            "unmatched_rows": len(missing),
            "multilingual_rows_added": added,
            "repo_count": len({issue_map[row["instance_id"]]["repo"] for row in rows if row["instance_id"] in issue_map}),
            "base_commit_count": len({issue_map[row["instance_id"]]["base_commit"] for row in rows if row["instance_id"] in issue_map}),
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"multilingual_rows": len(multi), "added": added, **{k: manifest[k] for k in ("bench_rows", "matched_rows", "unmatched_rows", "repo_count", "base_commit_count")}}, indent=2))


if __name__ == "__main__":
    main()
