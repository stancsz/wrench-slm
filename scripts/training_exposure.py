"""Audit the sequential example stream consumed by each planned checkpoint."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def audit(path, steps, batch_size, accumulation, required_kinds, required_languages):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows or min([batch_size, accumulation, *steps]) < 1:
        raise ValueError('Dataset and positive batch, accumulation, and step values are required')
    identifiers = [row['id'] for row in rows]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Duplicate row IDs')
    # The iterable loader emits a partial last batch, then cycles the file.
    checkpoints = []
    for step in sorted(set(steps)):
        remaining_batches = step * accumulation
        seen = []
        while remaining_batches:
            for offset in range(0, len(rows), batch_size):
                seen.extend(rows[offset:offset + batch_size])
                remaining_batches -= 1
                if not remaining_batches:
                    break
        kinds = Counter(row['kind'] for row in seen)
        languages = Counter(row['language'] for row in seen)
        missing_kinds = sorted(set(required_kinds) - kinds.keys())
        missing_languages = sorted(set(required_languages) - languages.keys())
        unique = len({row['id'] for row in seen})
        checkpoints.append({
            'step': step, 'presentations': len(seen), 'unique_rows': unique,
            'repeated_presentations': len(seen) - unique,
            'corpus_fraction_seen': unique / len(rows),
            'kinds': dict(kinds), 'languages': dict(languages),
            'kind_language': dict(Counter(f"{row['kind']}:{row['language']}" for row in seen)),
            'families': dict(Counter(row['family_id'] for row in seen)),
            'ordered_ids_sha256': hashlib.sha256(json.dumps([row['id'] for row in seen]).encode()).hexdigest(),
            'missing_kinds': missing_kinds, 'missing_languages': missing_languages,
            'coverage_passed': not missing_kinds and not missing_languages,
        })
    return {'dataset_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'corpus_rows': len(rows), 'batch_size': batch_size, 'accumulation': accumulation,
            'scope': 'Sequential loader exposure from step zero; presence checks do not prove balanced proportions or semantic correctness.',
            'checkpoints': checkpoints,
            'passed': all(item['coverage_passed'] for item in checkpoints)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train', required=True)
    parser.add_argument('--steps', type=int, nargs='+', required=True)
    parser.add_argument('--batch-size', type=int, required=True)
    parser.add_argument('--accumulation', type=int, required=True)
    parser.add_argument('--require-kind', nargs='+', required=True)
    parser.add_argument('--require-language', nargs='+', default=['en', 'zh'])
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = audit(args.train, args.steps, args.batch_size, args.accumulation,
                   args.require_kind, args.require_language)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(json.dumps({'passed': result['passed'], 'output': str(output)}))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
