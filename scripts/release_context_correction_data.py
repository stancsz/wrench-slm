"""Add training-only context grounding variations without importing probes."""

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


SUPPORTED = {'config', 'lines', 'search', 'git_status', 'git_log', 'health', 'draft'}
FOCUS = {'search', 'git_status', 'health', 'config', 'lines', 'git_log', 'draft'}

EN_SUFFIXES = [
    'Use the matching tool schema that is present in the available context.',
    'The listed tools are the complete interface for this request; choose from them exactly.',
    'Use the available inspection tool and preserve every argument from the request.',
    'Do not substitute a file read for an available command tool.',
    'The context may omit unrelated resources; resolve this from the tools and request.',
    'Use the tool by its schema name even when the tool list is reordered.',
]
ZH_SUFFIXES = [
    '请严格使用当前上下文中提供的对应工具模式。',
    '列出的工具就是本请求的完整接口，请从中准确选择。',
    '请使用可用的检查工具，并保留请求中的全部参数。',
    '不要把可用的命令工具替换成文件读取。',
    '上下文可能省略无关资源，请根据工具和请求完成判断。',
    '即使工具列表顺序改变，也请按模式名称选择工具。',
]


def clone(row, label):
    result = json.loads(json.dumps(row))
    result['id'] = f"{row['id']}-context-v5-{label}"
    result['source'] = 'authored_context_grounding_training_variation'
    return result


def add_variant(row, variant, index):
    result = clone(row, f'{variant}-{index}')
    language = row['language']
    suffixes = EN_SUFFIXES if language == 'en' else ZH_SUFFIXES
    result['prompt'] = f"{row['prompt']} {suffixes[index % len(suffixes)]}"
    tools = result['context']['tools']
    if variant == 'rotate_tools':
        shift = (index % max(1, len(tools)))
        result['context']['tools'] = tools[shift:] + tools[:shift]
    elif variant == 'reverse_tools':
        result['context']['tools'] = list(reversed(tools))
    elif variant == 'sole_tool' and row['tool'] != 'fallback':
        result['context']['tools'] = [tool for tool in tools if tool['name'] == row['tool']]
    elif variant == 'minimal_context':
        result['context'] = {key: value for key, value in result['context'].items()
                             if key in {'tools', 'prior_results'}}
    elif variant == 'stale_selection':
        prior = result['context'].setdefault('prior_results', {})
        if 'selected_file' in prior:
            prior['selected_file'] = 'unrelated/stale-selection.txt'
        if 'selected_service' in prior:
            prior['selected_service'] = 'unrelated-old-service'
    if row['kind'] in {'search', 'git_status', 'health'}:
        result['context']['resources'] = []
        result['context'].pop('os', None)
        result['context'].pop('shell', None)
        result['context'].pop('workdir', None)
    return result


def additions(rows):
    selected = [row for row in rows if row['kind'] in FOCUS]
    variants = ['rotate_tools', 'reverse_tools', 'minimal_context', 'stale_selection']
    result = []
    for index, row in enumerate(selected):
        for variant_index, variant in enumerate(variants):
            result.append(add_variant(row, variant, index + variant_index))
    # Give the three context-sensitive command kinds extra examples with only
    # their available schema. These are new prompts and new public contexts.
    for index, row in enumerate(rows):
        if row['kind'] in {'search', 'git_status', 'health'}:
            result.append(add_variant(row, 'sole_tool', index))
    return result


def main():
    source = ROOT / 'data/pilots/release-boundary-v4'
    rows = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    combined = rows + additions(rows)
    random.Random('release-context-correction-v5').shuffle(combined)
    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError(f'Conflicting training labels for {row["id"]}')
        if key not in seen:
            seen[key] = label
            unique.append(row)
    output = ROOT / 'data/pilots/release-context-correction-v5'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in unique), encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {
        'version': 'release-context-correction-v5',
        'source': 'Training-only context-grounding variations derived from V4 train; no prior context probes imported.',
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
            'tasks': len(records), 'families': len(families[split]),
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
