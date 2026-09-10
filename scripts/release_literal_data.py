"""Training-only literal-copy and boundary corrections. Sealed inputs stay fixed."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release_context_data import change_range, clone  # noqa: E402
from wrench.pilot_tasks import public_record  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402


STYLES = [
    'Make a write proposal for {path} using the complete decoded string {payload}.',
    'The entire proposed file content is {payload}, encoded as JSON. Draft its write to {path}.',
    'Generate a draft that puts all characters of the string {payload} at {path}. Interpret JSON escapes.',
    'File write for review only: {path}. Full body (JSON string): {payload}.',
    'Treat {payload} as one JSON string and use its decoded value as the complete write draft for {path}.',
    'Propose storing the complete text denoted by the JSON string {payload} in {path}, without applying it.',
    '为 {path} 准备完整文件写入草稿，正文取 JSON 字符串 {payload} 解码后的全部字符。',
    '正文的 JSON 编码是 {payload}。请拟定写入 {path} 的提案，不要执行。',
    '只生成写入建议：目标 {path}，完整内容为 {payload} 的 JSON 解码值。',
    '请把 JSON 字符串 {payload} 对应的全文作为 {path} 的待审写入内容。',
    '使用 {payload} 解码后的整个字符串，给 {path} 生成文件写入草稿。',
    '拟定 {path} 的写入提案，包含 JSON 编码 {payload} 表示的所有内容，保留换行和引号。',
]


def additions(rows):
    result = []
    drafts = [r for r in rows if r['kind'] == 'draft']
    for style, wording in enumerate(STYLES):
        for index in range(64):
            row = clone(drafts[(style * 64 + index) % len(drafts)], f'literal-{style}-{index}')
            nonce = hashlib.sha256(row['id'].encode()).hexdigest()[:12]
            name = ['alpha', 'beta', 'delta', 'omega'][index % 4]
            content = [f"name='{name}'\nkey={nonce}", f'mode="{name}"\nid={nonce}\n',
                       f"name='{name}'\nline two\ncode={nonce}", f'标题="{name}"\n键={nonce}\n',
                       f'{{"mode":"{name}","key":"{nonce}"}}', f'tab\t{name}\nbackslash=\\{nonce}'][index % 6]
            row['args']['content'] = content
            row.update(prompt=wording.format(path=row['args']['path'], payload=json.dumps(content, ensure_ascii=False)),
                       family_id=f'literal-training-v3-style-{style}', language='en' if style < 6 else 'zh',
                       source='new_authored_literal_copy_training_variation')
            result.append(row)
    by_language = {language: [r for r in rows if r['kind'] == 'lines' and r['language'] == language] for language in ['en', 'zh']}
    for index in range(128):
        language = 'en' if index % 2 == 0 else 'zh'
        parent = by_language[language][index % len(by_language[language])]
        end = 1 + (index // 2) % 16
        for start in [0, 1]:
            row = clone(parent, f'low-boundary-{index}-{start}')
            change_range(row, start, end)
            if start == 0:
                row.update(kind='invalid_range', tool='fallback', args={}, expected_answer='NEEDS_CLARIFICATION')
            else:
                row['args'].update(start_line=1, end_line=end)
                row['expected_answer'] = row['fixture']['files'][row['args']['path']].splitlines()[:end]
            result.append(row)
    for parent in rows:
        path = parent.get('args', {}).get('path')
        if parent['tool'] != 'fallback' and path and path in parent['prompt']:
            row = clone(parent, 'stale-selection')
            row['context']['prior_results'] = {'selected_file': 'unrelated/stale.txt', 'selected_service': 'unrelated-old'}
            result.append(row)
    return result


def main():
    source = ROOT / 'data/pilots/release-context-v2'
    rows = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    combined = rows + additions(rows)
    random.Random('release-literal-v3').shuffle(combined)
    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError('Conflicting training labels')
        if key not in seen:
            unique.append(row)
            seen[key] = label
    output = ROOT / 'data/pilots/release-literal-v3'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in unique), encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {'version': 'release-literal-v3', 'source': 'Training-only literal and numeric-boundary variations; no challenge or evaluation examples imported.',
                'parent_train_sha256': hashlib.sha256((source / 'train.jsonl').read_bytes()).hexdigest(),
                'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'dropped_identical_duplicates': len(combined) - len(unique), 'evaluation_unchanged': True,
                'label_conflicts': 0, 'splits': {}}
    inputs, families = {}, {}
    for split in ['train', 'development', 'evaluation']:
        path = output / f'{split}.jsonl'
        records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        inputs[split] = {canonical_json(public_record(r)) for r in records}
        families[split] = {r['family_id'] for r in records}
        manifest['splits'][split] = {'tasks': len(records), 'families': len(families[split]),
                                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                     'kinds': dict(Counter(r['kind'] for r in records))}
    for a in inputs:
        for b in inputs:
            if a != b and (inputs[a] & inputs[b] or families[a] & families[b]):
                raise ValueError('Cross-split overlap')
    manifest.update(cross_split_families=0, cross_split_exact_inputs=0)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
