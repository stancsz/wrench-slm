"""Build V12 data for the remaining Chinese Git-status generalization gap."""

from collections import Counter
import copy
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


ZH_GIT_PROMPTS = [
    '请列出当前工作区中已修改和新增的路径。',
    '查看本地仓库有哪些尚未提交的文件变动。',
    '当前检出目录的工作树状态有哪些变化？',
    '请返回版本库里待处理的修改项和新文件。',
    '工作树是否干净？列出修改过或未跟踪的路径。',
    '检查这个仓库的未提交变更并显示文件名。',
    '请查看当前分支工作区的变动清单。',
    '列出索引之外以及尚未跟踪的文件路径。',
    '仓库当前有哪些脏状态项目？只返回变动路径。',
    '查看本地版本控制状态，报告修改和新增文件。',
    '请检查检出中的待处理变更，不要读取任何单个文件。',
    '把工作区的改动和未跟踪项列出来。',
    '当前仓库有哪些文件与索引不同，或还没有被跟踪？',
    '检查工作树状态并返回所有待提交路径。',
    '请显示本地仓库的简短状态和变动文件。',
    '不要打开选中文件，列出版本库中修改和新建的路径。',
]

EN_GIT_PROMPTS = [
    'List changed and untracked paths in the current working tree.',
    'Check this checkout for files with pending uncommitted changes.',
    'Report the repository working-tree status and its changed paths.',
    'Show files that differ from the index or are not tracked yet.',
    'Inspect version-control state and return modified and new files.',
    'List pending paths from the local repository status, not file contents.',
    'Which paths are dirty in this checkout? Return the short status.',
    'Do not open the selected file; report the working tree changes.',
]

CONFIG_PROMPTS = {
    'en': [
        'Read the selected service configuration file and return its region value.',
        'Open the config associated with the service selected in context; report region.',
        'Inspect the selected service config itself, not a filename search, for region.',
        'Use the selected service entry and read its matching configuration file.',
    ],
    'zh': [
        '请读取上下文中选中服务的配置文件并返回 region。',
        '打开当前选中服务对应的 config 文件，报告其中的 region。',
        '请直接读取选中服务配置，不要搜索文件名，然后返回区域。',
        '根据选中服务信息打开匹配配置文件并查看 region 字段。',
    ],
}


def vary_context(row, instance):
    row = copy.deepcopy(row)
    old_path = row['args'].get('path') or row['context']['prior_results'].get('selected_file')
    digest = hashlib.sha256(f"{row['id']}:v12-path".encode()).hexdigest()[:10]
    new_path = [
        f'configs/current-{digest}.json',
        f'project files/current {digest}.json',
        f"developer's notes/current-{digest}.txt",
        f'配置/当前服务-{digest}.txt',
    ][instance % 4]
    if old_path:
        row = replace_path(row, old_path, new_path)
    variant = instance % 8
    if variant in (1, 5):
        row['context']['tools'].reverse()
    if variant in (2, 6):
        row['context']['resources'].reverse()
    if variant in (3, 7):
        row['context']['prior_results'] = dict(reversed(list(row['context']['prior_results'].items())))
    return row


def replace_path(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace_path(item, old, new) for item in value]
    if isinstance(value, dict):
        return {replace_path(key, old, new): replace_path(item, old, new) for key, item in value.items()}
    return value


def make_row(kind, language, family, instance, prompt):
    template = 0 if language == 'en' else 2
    row = make_release_task(kind, template, family * 64 + instance, 'train', 'generalization-v12')
    row = vary_context(row, instance)
    row['language'] = language
    row['id'] = f'generalization-v12-{kind}-{language}-{family}-{instance:03d}'
    row['seed_id'] = row['id']
    row['family_id'] = f'generalization-v12-{kind}-{language}-{family}'
    row['source'] = 'fresh_authored_v12_cross_language_tool_selection_training'
    row['prompt'] = prompt
    return row


def build_additions():
    rows = []
    # The remaining failure is Chinese Git status, so it receives 16 fresh
    # families. Smaller balanced slices protect the already-correct config
    # behavior and English status behavior.
    for family in range(16):
        for instance in range(64):
            rows.append(make_row('git_status', 'zh', family, instance, ZH_GIT_PROMPTS[family]))
    for family in range(8):
        for instance in range(64):
            rows.append(make_row('git_status', 'en', family, instance, EN_GIT_PROMPTS[family]))
    for language in ('en', 'zh'):
        for family in range(4):
            for instance in range(64):
                rows.append(make_row('config', language, family, instance, CONFIG_PROMPTS[language][family]))
    return rows


def main():
    parent = ROOT / 'artifacts/archive/data/pilots/release-generalization-v11'
    parent_train = parent / 'train.jsonl'
    parent_rows = [json.loads(line) for line in parent_train.read_text(encoding='utf-8').splitlines()]
    additions = build_additions()
    if len(additions) != 2048:
        raise ValueError(f'Expected 2048 additions, got {len(additions)}')
    combined = parent_rows + additions
    random.Random('release-generalization-v12').shuffle(combined)

    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError(f'Conflicting labels for {row["id"]}')
        if key not in seen:
            seen[key] = label
            unique.append(row)

    output = ROOT / 'artifacts/archive/data/pilots/release-generalization-v12'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in unique), encoding='utf-8')
    for split in ('development', 'evaluation'):
        (output / f'{split}.jsonl').write_bytes((parent / f'{split}.jsonl').read_bytes())

    inputs, families, splits = {}, {}, {}
    for split in ('train', 'development', 'evaluation'):
        path = output / f'{split}.jsonl'
        records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        inputs[split] = {canonical_json(public_record(record)) for record in records}
        families[split] = {record['family_id'] for record in records}
        splits[split] = {
            'tasks': len(records),
            'families': len(families[split]),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'kinds': dict(Counter(record['kind'] for record in records)),
            'languages': dict(Counter(record['language'] for record in records)),
        }
    for left in inputs:
        for right in inputs:
            if left != right and (inputs[left] & inputs[right] or families[left] & families[right]):
                raise ValueError('Cross-split overlap')

    manifest = {
        'version': 'release-generalization-v12',
        'source': 'Fresh natural-language Git-status correction after V11; no scored rows imported.',
        'parent_train_sha256': hashlib.sha256(parent_train.read_bytes()).hexdigest(),
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'new_training_rows': len(additions),
        'dropped_identical_duplicates': len(combined) - len(unique),
        'label_conflicts': 0,
        'development_unchanged': (output / 'development.jsonl').read_bytes() == (parent / 'development.jsonl').read_bytes(),
        'evaluation_unchanged': (output / 'evaluation.jsonl').read_bytes() == (parent / 'evaluation.jsonl').read_bytes(),
        'cross_split_families': 0,
        'cross_split_exact_inputs': 0,
        'target_balance': {
            'new_rows': {'zh_git_status': 1024, 'en_git_status': 512, 'en_config': 256, 'zh_config': 256},
            'zh_git_status_families': 16,
            'en_git_status_families': 8,
            'config_families_per_language': 4,
            'instances_per_family': 64,
        },
        'splits': splits,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
