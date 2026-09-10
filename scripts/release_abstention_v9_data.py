"""Add a small explicit-abstention correction after V8's dev miss."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import public_record  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402
from wrench.release_data import make_release_task  # noqa: E402


PROMPTS = [
    'The service is not selected. Ask for clarification instead of opening any configuration.',
    'No service was identified, so return the fallback rather than choosing a resource.',
    'Which service should be inspected? Do not guess from the available configs.',
    'There is no selected file or service. Abstain explicitly.',
    '服务尚未选定，请先澄清，不要打开任何配置文件。',
    '没有指定服务，不能从资源中猜测；请返回 fallback。',
    '我还没有选中具体服务，请明确放弃，不要读取配置。',
    '当前没有选中的文件或服务，请请求澄清。',
]


def clone(template, instance):
    language = 'en' if template < 4 else 'zh'
    row = make_release_task('ambiguous', 0 if language == 'en' else 2, template * 128 + instance,
                            'train', 'generalization-v9')
    row['id'] = f'generalization-v9-ambiguous-{language}-{template}-{instance}'
    row['seed_id'] = row['id']
    row['family_id'] = f'generalization-v9-ambiguous-abstention-{template}'
    row['source'] = 'fresh_authored_abstention_training'
    row['context']['prior_results'] = {}
    row['prompt'] = PROMPTS[template]
    return row


def main():
    source = ROOT / 'data/pilots/release-generalization-v8'
    parent = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    additions = [clone(template, instance) for template in range(8) for instance in range(128)]
    combined = parent + additions
    random.Random('release-abstention-v9').shuffle(combined)
    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError(f'Conflicting labels for {row["id"]}')
        if key not in seen:
            seen[key] = label
            unique.append(row)
    output = ROOT / 'data/pilots/release-generalization-v9'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in unique),
                                        encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {
        'version': 'release-generalization-v9',
        'source': 'Fresh explicit-abstention correction after V8 development failure; no scored rows imported.',
        'parent_train_sha256': hashlib.sha256((source / 'train.jsonl').read_bytes()).hexdigest(),
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'dropped_identical_duplicates': len(combined) - len(unique),
        'label_conflicts': 0,
        'evaluation_unchanged': True,
        'splits': {},
    }
    inputs, families = {}, {}
    for split in ['train', 'development', 'evaluation']:
        path = output / f'{split}.jsonl'
        records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        inputs[split] = {canonical_json(public_record(record)) for record in records}
        families[split] = {record['family_id'] for record in records}
        manifest['splits'][split] = {
            'tasks': len(records),
            'families': len(families[split]),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'kinds': dict(Counter(record['kind'] for record in records)),
        }
    for left in inputs:
        for right in inputs:
            if left != right and (inputs[left] & inputs[right] or families[left] & families[right]):
                raise ValueError('Cross-split overlap')
    manifest.update(cross_split_families=0, cross_split_exact_inputs=0)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
