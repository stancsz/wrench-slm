"""Prepare training-only contrast pairs for demonstrated context/range failures.

Every derivative remains in its parent's training wording family. The original
sealed evaluation file is copied unchanged, never used to construct examples.
"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import public_record  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402


def clone(row, variant):
    result = json.loads(json.dumps(row))
    result['id'] += '-' + variant
    result['seed_id'] = row['seed_id']
    result['source'] = 'training_contrast_derivative_of_' + row['id']
    return result


def change_range(row, start, end):
    # Replace just the two requested bounds, not digits within paths.
    pattern = re.compile(r'(?<![A-Za-z0-9_/])\d+(?![A-Za-z0-9_])')
    matches = list(pattern.finditer(row['prompt']))
    if len(matches) != 2:
        raise ValueError('Unexpected range wording: ' + row['id'])
    values = iter([str(start), str(end)])
    row['prompt'] = pattern.sub(lambda _: next(values), row['prompt'])


def derive(row):
    results = [row]
    variant = clone(row, 'context')
    variant['context']['tools'].reverse()
    if row['tool'] != 'fallback':
        variant['context']['tools'] = [t for t in variant['context']['tools'] if t['name'] == row['tool']]
    explicit_path = row.get('args', {}).get('path', '')
    if row['kind'] != 'config' or (explicit_path and explicit_path in row['prompt']):
        variant['context']['resources'] = []
    variant['context'].pop('os', None)
    variant['context'].pop('shell', None)
    variant['context'].pop('workdir', None)
    if explicit_path and explicit_path in row['prompt']:
        variant['context']['prior_results'] = {}
    results.append(variant)
    if row['kind'] in {'lines', 'invalid_range'}:
        twin = clone(row, 'bounds-contrast')
        path = row['context']['resources'][0]['config']
        seed = int(hashlib.sha256(row['id'].encode()).hexdigest()[:8], 16)
        if row['kind'] == 'lines':
            end = row['args']['end_line']
            start = 0 if seed % 2 else end + 5
            twin.update(kind='invalid_range', tool='fallback', args={}, expected_answer='NEEDS_CLARIFICATION')
        else:
            start = 1 + seed % 160
            end = start + seed % 12
            twin.update(kind='lines', tool='read_file', args={'path': path, 'start_line': start, 'end_line': end},
                        expected_answer=row['fixture']['files'][path].splitlines()[start - 1:end])
        change_range(twin, start, end)
        results.append(twin)
    template = int(row['family_id'].rsplit('-', 1)[1])
    if row['kind'] == 'config' and template in (1, 3):
        twin = clone(row, 'missing-selection')
        twin['context']['prior_results'] = {}
        twin.update(kind='ambiguous', tool='fallback', args={}, expected_answer='NEEDS_CLARIFICATION')
        results.append(twin)
    if row['kind'] == 'ambiguous' and template in (1, 3):
        twin = clone(row, 'available-selection')
        seed = int(hashlib.sha256(row['id'].encode()).hexdigest()[:8], 16)
        selected = twin['context']['resources'][seed % 2]
        twin['context']['prior_results'] = {'selected_service': selected['service']}
        twin['context']['resources'].reverse()
        twin.update(kind='config', tool='read_file', args={'path': selected['config']},
                    expected_answer=json.loads(twin['fixture']['files'][selected['config']])['region'])
        results.append(twin)
    return results


def main():
    source = ROOT / 'data/pilots/release-authoring-v1'
    output = ROOT / 'data/pilots/release-context-v2'
    original = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    train = [derived for row in original for derived in derive(row)]
    random.Random('release-context-v2').shuffle(train)
    seen = {}
    unique = []
    for row in train:
        key = canonical_json(public_record(row))
        target = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != target:
            raise ValueError('Conflicting labels for the same model input')
        if key not in seen:
            unique.append(row)
            seen[key] = target
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in unique), encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {'version': 'release-context-v2', 'source': 'Training-only context and range contrasts derived from release-authoring-v1 train.',
                'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'dropped_exact_training_duplicates': len(train) - len(unique),
                'parent_train_sha256': hashlib.sha256((source / 'train.jsonl').read_bytes()).hexdigest(),
                'evaluation_unchanged': True, 'splits': {},
                'limitations': ['Authored cases, not production data.', 'Contrast pairs share parent families and are not independent samples.']}
    input_sets, families = {}, {}
    for split in ['train', 'development', 'evaluation']:
        path = output / f'{split}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        input_sets[split] = {canonical_json(public_record(r)) for r in rows}
        families[split] = {r['family_id'] for r in rows}
        manifest['splits'][split] = {'tasks': len(rows), 'families': len(families[split]),
                                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                     'kinds': dict(Counter(r['kind'] for r in rows))}
    for a in input_sets:
        for b in input_sets:
            if a != b and (input_sets[a] & input_sets[b] or families[a] & families[b]):
                raise ValueError('Cross-split overlap')
    manifest.update(cross_split_families=0, cross_split_exact_inputs=0)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
