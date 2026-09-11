"""Audit available V2 evaluation overlap against retained training ancestry."""

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def public_record(row):
    if isinstance(row, dict) and isinstance(row.get('prompt'), str) and isinstance(row.get('context'), dict):
        return {'prompt': row['prompt'], 'context': row['context']}
    return None


def rows(path):
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.strip():
            yield json.loads(line)


def canonical(record):
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def normalize_prompt(prompt):
    value = prompt.lower()
    value = re.sub(r'https?://127\.0\.0\.1:\d+', 'http://127.0.0.1:<port>', value)
    value = re.sub(r'[a-f0-9]{6,}', '<id>', value)
    value = re.sub(r'(?<!\w)(?:[a-z]:)?[\\/][\w./\\-]+', '<path>', value)
    value = re.sub(r'\b\d+\b', '<num>', value)
    return ' '.join(value.split())


def resolve_declared_train(path):
    declared = Path(path)
    candidates = [ROOT / declared]
    text = str(declared).replace('data/pilots', 'data/releases').replace('data\\pilots', 'data\\releases')
    candidates.append(ROOT / text)
    candidates.append(ROOT / 'data' / declared.name)
    return next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)


def lineage_runs(training_root):
    output = []
    for run_path in sorted(training_root.glob('pro-training-*/run.json')):
        try:
            receipt = json.loads(run_path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        declared = receipt.get('arguments', {}).get('train')
        resolved = resolve_declared_train(declared) if declared else None
        output.append({
            'run': run_path.parent.name,
            'status': receipt.get('status'),
            'declared_train': declared,
            'resolved_train': str(resolved) if resolved else None,
            'train_sha256': digest(resolved) if resolved else None,
            'source_available': resolved is not None,
            'initial_adapter': receipt.get('arguments', {}).get('initialize_adapter'),
        })
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evaluation', required=True)
    parser.add_argument('--data-root', default='data')
    parser.add_argument('--training-root', default='artifacts/model-release')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    evaluation = Path(args.evaluation).resolve()
    data_root = Path(args.data_root).resolve()
    training_root = Path(args.training_root).resolve()
    output = Path(args.output).resolve()
    target_records = [public_record(row) for row in rows(evaluation)]
    target_records = [record for record in target_records if record]
    exact_targets = {canonical(record) for record in target_records}
    normalized_targets = {normalize_prompt(record['prompt']) for record in target_records}
    files = []
    for path in sorted(data_root.rglob('*.jsonl')):
        if path.resolve() != evaluation:
            files.append(path)
    files.extend(path for path in sorted(training_root.rglob('*.jsonl')) if path not in files)
    overlap = []
    seen = set()
    for path in files:
        path = path.resolve()
        if path in seen:
            continue
        seen.add(path)
        exact = 0
        normalized = 0
        count = 0
        try:
            for row in rows(path):
                record = public_record(row)
                if not record:
                    continue
                count += 1
                exact += canonical(record) in exact_targets
                normalized += normalize_prompt(record['prompt']) in normalized_targets
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if count:
            overlap.append({
                'path': str(path), 'rows_with_public_record': count,
                'exact_public_input_overlap': exact,
                'heuristic_normalized_prompt_overlap': normalized,
                'sha256': digest(path),
            })
    runs = lineage_runs(training_root)
    result = {
        'status': 'PARTIAL_COVERAGE_NO_INDEPENDENCE_PROOF',
        'evaluation': {'path': str(evaluation), 'sha256': digest(evaluation), 'rows': len(target_records), 'families': len({row.get('family_id') for row in rows(evaluation)})},
        'training_runs': runs,
        'training_runs_with_missing_declared_source': sum(not item['source_available'] for item in runs),
        'available_jsonl_overlap': overlap,
        'claims': {
            'independent_authorship_verified': False,
            'complete_ancestor_coverage_verified': not any(not item['source_available'] for item in runs),
            'exact_public_input_overlap_scope': 'All readable JSONL under data and artifacts/model-release, excluding the target evaluation file',
            'normalized_prompt_scope': 'Heuristic lowercase and placeholder normalization only; not a semantic similarity proof',
        },
        'limitations': [
            'Authorship records and author separation are not present in the retained artifacts.',
            'Missing declared source files prevent complete ancestor coverage.',
            'Exact and normalized prompt overlap do not prove semantic independence or non-independence.',
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
