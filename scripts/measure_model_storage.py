"""Measure the explicitly retained model and checkpoint paths."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    'artifacts/model-release/base-dependency-v1',
    'artifacts/model-release/package-selected-v20',
    'artifacts/model-release/package-selected-v21',
    'artifacts/model-release/pro-training-v21/step-000100',
    'artifacts/model-release/pro-training-v21/step-000200',
    'artifacts/model-release/pro-training-v21/checkpoint',
    'artifacts/model-release/pro-training-v22/step-000100',
    'artifacts/model-release/pro-training-v22/step-000200',
    'artifacts/model-release/pro-training-v22/checkpoint',
)


def measure(budget):
    rows = []
    for relative in TARGETS:
        path = ROOT / relative
        files = list(path.rglob('*')) if path.is_dir() else []
        files = [item for item in files if item.is_file()]
        rows.append({'path': relative, 'exists': path.is_dir(), 'files': len(files), 'bytes': sum(item.stat().st_size for item in files)})
    total = sum(row['bytes'] for row in rows)
    return {
        'budget_bytes': budget,
        'total_bytes': total,
        'remaining_bytes': budget - total,
        'within_budget': total <= budget,
        'targets': rows,
        'scope': 'Explicit retained base, packages, and V21/V22 trainer snapshots; no deletion performed',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--budget-bytes', type=int, default=5_000_000_000)
    parser.add_argument('--output')
    args = parser.parse_args()
    result = measure(args.budget_bytes)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['within_budget']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
