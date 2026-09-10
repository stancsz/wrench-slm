"""Add a final ordinary-wording ambiguity correction after V9."""

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
    'The region request names no service. Ask which service to use before reading a configuration.',
    'I need the region from the appropriate config, but no service has been selected. Abstain.',
    'Several service resources are available and none is selected. Do not choose one; return fallback.',
    'Which service should supply the region? Do not open a config until that is clarified.',
    '这个 region 请求没有指定服务。请先询问服务，不要读取配置。',
    '我需要适当配置中的 region，但没有选中服务，请明确放弃。',
    '有多个服务资源却没有选择对象，不要猜测配置，请返回 fallback。',
    '请先确认应该使用哪个服务，再读取配置；当前请求必须澄清。',
]


def clone(template, instance):
    language = 'en' if template < 4 else 'zh'
    row = make_release_task('ambiguous', 0 if language == 'en' else 2, template * 256 + instance,
                            'train', 'generalization-v10')
    row['id'] = f'generalization-v10-ambiguous-{language}-{template}-{instance}'
    row['seed_id'] = row['id']
    row['family_id'] = f'generalization-v10-ambiguous-ordinary-{template}'
    row['source'] = 'fresh_authored_ordinary_abstention_training'
    row['context']['prior_results'] = {}
    row['prompt'] = PROMPTS[template]
    return row


def main():
    source = ROOT / 'data/pilots/release-generalization-v9'
    parent = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    additions = [clone(template, instance) for template in range(8) for instance in range(256)]
    combined = parent + additions
    random.Random('release-ambiguity-v10').shuffle(combined)
    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError(f'Conflicting labels for {row["id"]}')
        if key not in seen:
            seen[key] = label
            unique.append(row)
    output = ROOT / 'data/pilots/release-generalization-v10'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in unique),
                                        encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {
        'version': 'release-generalization-v10',
        'source': 'Fresh ordinary-wording ambiguity correction after V9; no scored rows imported.',
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
