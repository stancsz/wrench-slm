"""Build the bounded V11 cross-language tool-selection correction set.

V10 passed the authored development set but confused English config requests
with literal searches and Chinese Git-status requests with file reads on fresh
contexts. This generator adds training-only contrast rows while copying the
V10 development and evaluation files byte-for-byte. It never imports scored
evaluation rows into training.
"""

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


CONFIG_PROMPTS = {
    'en': [
        'Open the configuration belonging to the selected service and read its region.',
        'Read the selected service config file and report the region value.',
        'The selected service needs a region check. Open its configuration with the file reader.',
        'Use the selected service entry in context, then read that config file for region.',
        'Find the selected service configuration and read the region field; do not search filenames.',
        'Which region is stored in the selected service configuration? Read the matching file.',
        'Inspect the config file for the service selected in prior results and return its region.',
        'Please open the selected service config itself, rather than running a text search, and get region.',
    ],
    'zh': [
        '请打开上下文中选中服务的配置文件，读取其中的 region。',
        '读取当前选中服务的配置文件并返回 region 值。',
        '选中的服务需要检查部署区域，请用文件读取工具打开它的配置。',
        '根据上下文里的选中服务读取对应配置文件，然后返回 region。',
        '请读取选中服务的配置文件中的 region，不要搜索文件名。',
        '选中服务的配置记录了哪个 region？请打开匹配的文件。',
        '查看之前结果选中的服务配置文件，并返回其中的 region 字段。',
        '请直接打开选中服务的配置文件读取 region，不要执行文本搜索。',
    ],
}

GIT_STATUS_PROMPTS = {
    'en': [
        'Use Git status to show modified and untracked files in this working tree.',
        'Run the short Git status for this checkout and list its pending files.',
        'Which paths are changed or untracked? Use exactly the Git status operation.',
        'Inspect repository status, not file contents, and return modified and new files.',
        'Show the working tree changes with short Git status.',
        'Report the files Git considers modified or untracked in this repository.',
        'Check the checkout for pending changes with `git status --short`.',
        'List the dirty and untracked paths from Git; do not open the selected file.',
    ],
    'zh': [
        '请用 Git status 列出工作区中已修改和未跟踪的文件。',
        '运行当前检出的简短 Git 状态，并列出待处理文件。',
        '哪些路径已修改或未跟踪？请使用 Git 状态操作。',
        '检查仓库状态而不是文件内容，返回修改和新增文件。',
        '用简短 Git status 显示工作树的变动。',
        '返回 Git 认为已修改或未跟踪的文件。',
        '检查当前检出中的待处理变更，使用 `git status --short`。',
        '列出 Git 工作区中的脏文件和未跟踪路径，不要打开选中文件。',
    ],
}

MISSING_CONFIG_PROMPTS = {
    'en': [
        'I need a service region, but no service is selected. Ask for clarification before reading a config.',
        'There is no selected service for this region request. Return fallback instead of guessing a file.',
    ],
    'zh': [
        '我需要服务的 region，但当前没有选中服务。读取配置前请先请求澄清。',
        '这个区域请求没有选中服务。不要猜文件，请返回 fallback。',
    ],
}


def replace_path(value, old, new):
    """Replace a generated path throughout a task before rendering its prompt."""
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace_path(item, old, new) for item in value]
    if isinstance(value, dict):
        return {replace_path(key, old, new): replace_path(item, old, new) for key, item in value.items()}
    return value


def vary_context(row, instance):
    """Vary ordering and path spelling without changing the target label."""
    row = copy.deepcopy(row)
    old_path = row['args'].get('path')
    if not old_path:
        old_path = row['context']['prior_results'].get('selected_file')
    digest = hashlib.sha256(f"{row['id']}:path".encode()).hexdigest()[:10]
    path_forms = [
        f'configs/selected-{digest}.json',
        f'project files/selected {digest}.json',
        f"developer's notes/selected-{digest}.txt",
        f'配置/选中服务-{digest}.txt',
    ]
    new_path = path_forms[instance % len(path_forms)]
    if old_path:
        row = replace_path(row, old_path, new_path)
    context = row['context']
    variant = instance % 8
    if variant in (1, 5):
        context['tools'].reverse()
    if variant in (2, 6):
        context['resources'].reverse()
    if variant in (3, 7):
        context['prior_results'] = dict(reversed(list(context['prior_results'].items())))
    return row


def selected_config(language, family, instance):
    row = make_release_task('config', 0 if language == 'en' else 2,
                            family * 64 + instance, 'train', 'generalization-v11')
    row = vary_context(row, instance)
    row['language'] = language
    row['family_id'] = f'generalization-v11-config-{language}-selected-{family}'
    row['id'] = f'generalization-v11-config-{language}-selected-{family}-{instance:03d}'
    row['seed_id'] = row['id']
    row['source'] = 'fresh_authored_cross_language_tool_selection_training'
    row['prompt'] = CONFIG_PROMPTS[language][family].format(
        path=row['args']['path'],
        service=row['context']['prior_results']['selected_service'],
    )
    return row


def missing_config(language, family, instance):
    row = make_release_task('config', 0 if language == 'en' else 2,
                            512 + family * 64 + instance, 'train', 'generalization-v11')
    row = vary_context(row, instance)
    row['context']['resources'] = []
    request_id = hashlib.sha256(row['id'].encode()).hexdigest()[:10]
    row['context']['prior_results'] = {'request_id': request_id}
    row['tool'] = 'fallback'
    row['args'] = {}
    row['expected_answer'] = 'NEEDS_CLARIFICATION'
    row['language'] = language
    row['family_id'] = f'generalization-v11-config-{language}-missing-{family}'
    row['id'] = f'generalization-v11-config-{language}-missing-{family}-{instance:03d}'
    row['seed_id'] = row['id']
    row['source'] = 'fresh_authored_cross_language_tool_selection_training'
    row['prompt'] = f'{MISSING_CONFIG_PROMPTS[language][family]} Request reference: {request_id}.'
    return row


def git_status(language, family, instance):
    row = make_release_task('git_status', 0 if language == 'en' else 2,
                            1024 + family * 64 + instance, 'train', 'generalization-v11')
    row = vary_context(row, instance)
    row['language'] = language
    row['family_id'] = f'generalization-v11-git-status-{language}-{family}'
    row['id'] = f'generalization-v11-git-status-{language}-{family}-{instance:03d}'
    row['seed_id'] = row['id']
    row['source'] = 'fresh_authored_cross_language_tool_selection_training'
    row['prompt'] = GIT_STATUS_PROMPTS[language][family]
    return row


def build_additions():
    rows = []
    # Eight families per language and target kind, 64 instances per family.
    # Config families 0-5 are selected-service positives; 6-7 are explicit
    # missing-selection fallback contrasts.
    for language in ('en', 'zh'):
        for family in range(8):
            for instance in range(64):
                if family < 6:
                    rows.append(selected_config(language, family, instance))
                else:
                    missing_family = (family - 6) % len(MISSING_CONFIG_PROMPTS[language])
                    rows.append(missing_config(language, missing_family, instance))
                rows.append(git_status(language, family, instance))
    return rows


def main():
    parent = ROOT / 'data/pilots/release-generalization-v10'
    parent_train = parent / 'train.jsonl'
    parent_rows = [json.loads(line) for line in parent_train.read_text(encoding='utf-8').splitlines()]
    additions = build_additions()
    if len(additions) != 2048:
        raise ValueError(f'Expected 2048 additions, got {len(additions)}')
    combined = parent_rows + additions
    random.Random('release-generalization-v11').shuffle(combined)

    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError(f'Conflicting labels for {row["id"]}')
        if key not in seen:
            seen[key] = label
            unique.append(row)

    output = ROOT / 'data/pilots/release-generalization-v11'
    output.mkdir(parents=True, exist_ok=False)
    train_path = output / 'train.jsonl'
    train_path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in unique), encoding='utf-8')
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
        'version': 'release-generalization-v11',
        'source': 'Fresh balanced cross-language tool-selection correction after V10 external failures; no scored rows imported.',
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
            'languages': ['en', 'zh'],
            'kinds': ['config', 'git_status'],
            'families_per_language_kind': 8,
            'instances_per_family': 64,
            'config_selected_families_per_language': 6,
            'config_missing_selection_families_per_language': 2,
        },
        'splits': splits,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
