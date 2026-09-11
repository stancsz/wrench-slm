"""Audit the V2 data contract and independently execute its gold actions."""

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
from wrench.pilot_tasks_v2 import (
    FALLBACK_KINDS,
    KINDS,
    ROUTINE_KINDS,
    public_record,
)
from wrench.protocol import ROUTER_FALLBACK
from wrench.release_eval import outcome_matches

PRIVATE_FIELDS = {'fixture', 'tool', 'args', 'expected_answer'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_split(data, split, manifest):
    path = data / f'{split}.jsonl'
    if digest(path) != manifest['splits'][split]['sha256']:
        raise ValueError(f'{split} checksum mismatch')
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != manifest['splits'][split]['tasks'] or len({row['id'] for row in rows}) != len(rows):
        raise ValueError(f'{split} count or ID mismatch')
    return rows


def public_json(row):
    return json.dumps(public_record(row), ensure_ascii=False, sort_keys=True)


def nested_keys(value):
    if isinstance(value, dict):
        return set(value) | {key for child in value.values() for key in nested_keys(child)}
    if isinstance(value, list):
        return {key for child in value for key in nested_keys(child)}
    return set()


def audit_public_records(rows):
    failures = []
    for row in rows:
        leaked = sorted(PRIVATE_FIELDS & nested_keys(public_record(row)))
        if leaked:
            failures.append({'id': row.get('id'), 'fields': leaked, 'reason': 'private_field_in_public_record'})
    return failures


def historical_public_inputs(root):
    values = set()
    if not root.exists():
        return values
    for path in root.rglob('*.jsonl'):
        try:
            for line in path.read_text(encoding='utf-8').splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if isinstance(row, dict) and isinstance(row.get('prompt'), str) and isinstance(row.get('context'), dict):
                    values.add(json.dumps({'prompt': row['prompt'], 'context': row['context']}, ensure_ascii=False, sort_keys=True))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    return values


def audit_labels(rows):
    checked = 0
    failures = []
    with tempfile.TemporaryDirectory(prefix='wrench-v2-gold-') as temporary:
        for row in rows:
            if not set(row) >= {'id', 'family_id', 'kind', 'language', 'prompt', 'context', 'fixture', 'tool', 'args', 'expected_answer'}:
                failures.append({'id': row['id'], 'reason': 'missing_row_field'})
                continue
            env = PilotEnvironment(row, Path(temporary) / row['id'])
            try:
                task = env.task
                if task['kind'] in FALLBACK_KINDS:
                    correct = outcome_matches(task, ROUTER_FALLBACK, None)
                else:
                    receipt = env.execute({'tool': task['tool'], 'args': task['args']})
                    correct = outcome_matches(task, json.dumps({'tool': task['tool'], 'args': task['args']}), receipt)
                if not correct:
                    failures.append({'id': row['id'], 'reason': 'gold_outcome_mismatch'})
                checked += 1
            finally:
                env.close()
    return checked, failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--historical-root', action='append', default=[])
    args = parser.parse_args()
    data = Path(args.data).resolve()
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version') != 'usefulness-pilot-v2':
        raise ValueError('Wrong dataset version')
    splits = {split: read_split(data, split, manifest) for split in manifest['splits']}
    all_rows = [row for rows in splits.values() for row in rows]
    family_sets = {split: {row['family_id'] for row in rows} for split, rows in splits.items()}
    public_sets = {split: {public_json(row) for row in rows} for split, rows in splits.items()}
    if family_sets['development'] & family_sets['evaluation'] or public_sets['development'] & public_sets['evaluation']:
        raise ValueError('Cross-split overlap')
    if any(row['language'] not in {'en', 'zh'} or row['kind'] not in KINDS for row in all_rows):
        raise ValueError('Unsupported language or kind')
    if any(set(row['context']) - {'os', 'shell', 'workdir', 'tools', 'resources', 'prior_results'} for row in all_rows):
        raise ValueError('Unexpected context field')
    historical = set()
    for root in args.historical_root:
        historical |= historical_public_inputs(Path(root).resolve())
    exact_historical_overlap = len(public_sets['evaluation'] & historical)
    public_failures = audit_public_records(all_rows)
    checked, failures = audit_labels(all_rows)
    invalid_categories = Counter()
    for row in splits['evaluation']:
        if row['kind'] != 'invalid_range':
            continue
        start, end = row['args']['start_line'], row['args']['end_line']
        if start <= 0 or end <= 0:
            invalid_categories['zero_or_negative'] += 1
        elif end < start:
            invalid_categories['reversed'] += 1
        else:
            invalid_categories['beyond_eof'] += 1
    result = {
        'status': 'passed' if not public_failures and not failures and exact_historical_overlap == 0 else 'failed',
        'manifest_sha256': digest(data / 'manifest.json'),
        'splits': {split: {'tasks': len(rows), 'families': len(family_sets[split]), 'languages': dict(Counter(r['language'] for r in rows)), 'kinds': dict(Counter(r['kind'] for r in rows))} for split, rows in splits.items()},
        'public_private_field_audit': 'passed' if not public_failures else 'failed',
        'public_private_field_failures': public_failures,
        'cross_split_family_overlap': len(family_sets['development'] & family_sets['evaluation']),
        'cross_split_public_input_overlap': len(public_sets['development'] & public_sets['evaluation']),
        'historical_exact_public_input_overlap': exact_historical_overlap,
        'gold_rows_checked': checked,
        'gold_failures': failures,
        'invalid_range_categories': dict(invalid_categories),
        'routine_kinds': sorted(ROUTINE_KINDS),
        'fallback_kinds': sorted(FALLBACK_KINDS),
        'limitations': [
            'Exact-input overlap checks do not prove semantic independence.',
            'Generated labels are executable fixture labels, not recovered production outcomes.',
        ],
    }
    output = data / 'preflight.json'
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
