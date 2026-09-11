"""Audit V22 repair data before any training or checkpoint selection."""

import argparse
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_environment import PilotEnvironment
from wrench.pilot_tasks_v22 import KINDS, public_record
from wrench.protocol import ROUTER_FALLBACK
from wrench.release_eval import outcome_matches

PRIVATE_FIELDS = {'fixture', 'tool', 'args', 'expected_answer'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def nested_keys(value):
    if isinstance(value, dict):
        return set(value) | {key for child in value.values() for key in nested_keys(child)}
    if isinstance(value, list):
        return {key for child in value for key in nested_keys(child)}
    return set()


def read_rows(data, manifest, split):
    path = data / f'{split}.jsonl'
    if digest(path) != manifest['splits'][split]['sha256']:
        raise ValueError(f'{split} checksum mismatch')
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != manifest['splits'][split]['tasks'] or len({row['id'] for row in rows}) != len(rows):
        raise ValueError(f'{split} count or ID mismatch')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    data = Path(args.data).resolve()
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version') != 'usefulness-pilot-v22-repair':
        raise ValueError('Wrong V22 data version')
    splits = {split: read_rows(data, manifest, split) for split in manifest['splits']}
    all_rows = [row for rows in splits.values() for row in rows]
    public_sets = {split: {json.dumps(public_record(row), ensure_ascii=False, sort_keys=True) for row in rows} for split, rows in splits.items()}
    family_sets = {split: {row['family_id'] for row in rows} for split, rows in splits.items()}
    public_leaks = [row['id'] for row in all_rows if PRIVATE_FIELDS & nested_keys(public_record(row))]
    failures = []
    checked = 0
    with tempfile.TemporaryDirectory(prefix='wrench-v22-gold-') as temporary:
        for row in all_rows:
            if public_leaks and row['id'] in public_leaks:
                continue
            env = PilotEnvironment(row, Path(temporary) / row['id'])
            try:
                task = env.task
                if task['tool'] == 'fallback':
                    correct = outcome_matches(task, ROUTER_FALLBACK, None)
                else:
                    call = {'tool': task['tool'], 'args': task['args']}
                    receipt = env.execute(call)
                    correct = outcome_matches(task, json.dumps(call), receipt)
                if not correct:
                    failures.append({'id': row['id'], 'reason': 'gold_outcome_mismatch'})
                checked += 1
            finally:
                env.close()
    overlaps = {
        f'{left}_vs_{right}': {
            'families': len(family_sets[left] & family_sets[right]),
            'public_inputs': len(public_sets[left] & public_sets[right]),
        }
        for left in splits
        for right in splits
        if left < right
    }
    result = {
        'status': 'passed' if not failures and not public_leaks and all(not value['families'] and not value['public_inputs'] for value in overlaps.values()) else 'failed',
        'manifest_sha256': digest(data / 'manifest.json'),
        'splits': {split: {'tasks': len(rows), 'families': len(family_sets[split]), 'languages': dict(Counter(row['language'] for row in rows)), 'kinds': dict(Counter(row['kind'] for row in rows))} for split, rows in splits.items()},
        'overlaps': overlaps,
        'public_private_field_leaks': public_leaks,
        'gold_rows_checked': checked,
        'gold_failures': failures,
        'kinds': list(KINDS),
        'limitations': ['Exact-input isolation does not prove semantic independence.', 'Executable labels are not recovered production outcomes.'],
    }
    (data / 'preflight.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
