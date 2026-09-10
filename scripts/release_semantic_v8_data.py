"""Add a final bounded semantic-disambiguation set after V7 held-out scores."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import TOOLS, public_record  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402
from wrench.release_data import make_release_task  # noqa: E402


TEMPLATES = {
    'config': [
        'The selected service needs a region check. Open its matching configuration file.',
        'Use the service resource in context to read its configuration and find the region field.',
        'A region lookup means read the service config, not repository status. Inspect the matching file.',
        'Which deployment region is stored in the selected service configuration?',
        '当前选中的服务需要核对 region，请打开对应配置文件。',
        '请根据上下文资源读取服务配置，查找 region 字段。',
        'region 查询要读取服务配置，不是查看仓库状态。请检查匹配文件。',
        '选中服务的配置记录了哪个部署区域？',
    ],
    'git_status': [
        'What files are currently modified or untracked in this checkout?',
        'List the pending changes in the repository working tree.',
        'Show the short status of this local Git repository.',
        'Inspect this checkout for changed files and new files.',
        '当前工作区有哪些已修改或未跟踪的文件？',
        '列出仓库工作树里待处理的变更和新增文件。',
        '查看本地 Git 仓库的简短状态。',
        '检查这个检出目录中被修改和新建的文件。',
    ],
    'git_log': [
        'What subject is recorded on the tip commit?',
        'Read the newest local commit subject from HEAD.',
        'Return the latest commit title from this repository history.',
        'Find the subject line attached to the most recent commit.',
        '请读取本地 HEAD 最新提交的主题。',
        '返回仓库最近一次提交的标题。',
        '查看最新提交对应的 subject 行。',
        '从本地历史取出末尾提交的主题文本。',
    ],
    'missing_tool': [
        'The file-reading interface is unavailable. Return the fallback instead of inventing read_file.',
        'Only the listed tools may be used, and none can read the complete file. Abstain explicitly.',
        'Do not emit a call when the required file tool is missing; use the fallback response.',
        'The requested operation cannot be performed with the available tools, so return fallback.',
        '上下文没有文件读取接口，不要虚构 read_file，请返回 fallback。',
        '只能使用列出的工具，无法读取完整文件时必须明确放弃。',
        '缺少完成该读取所需的工具，不要生成调用，请使用 fallback。',
        '当前工具不能完成请求，请返回 fallback。',
    ],
}


def clone(kind, template, instance):
    language = 'en' if template < 4 else 'zh'
    row = make_release_task(kind, 0 if language == 'en' else 2, template * 128 + instance,
                            'train', 'generalization-v8')
    row['id'] = f'generalization-v8-{kind}-{language}-{template}-{instance}'
    row['seed_id'] = row['id']
    row['family_id'] = f'generalization-v8-{kind}-contrast-{template}'
    row['source'] = 'fresh_authored_semantic_disambiguation_training'
    if kind in {'config', 'git_status', 'git_log'}:
        path = row.get('args', {}).get('path') or row['context'].get('prior_results', {}).get('selected_file',
                                                                                              'selected/config.txt')
        row['context']['tools'] = json.loads(json.dumps(TOOLS))
        row['context']['resources'] = [
            {'service': 'selected-service', 'config': path},
            {'service': 'archived-service', 'config': 'archive/old-config.json'},
        ]
        row['context']['prior_results'] = {}
    else:
        row['context']['prior_results'] = {}
        row['context']['tools'] = [tool for tool in row['context']['tools'] if tool['name'] == 'write_file']
    row['prompt'] = TEMPLATES[kind][template]
    return row


def main():
    source = ROOT / 'data/pilots/release-generalization-v7'
    parent = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    additions = [clone(kind, template, instance)
                 for kind in TEMPLATES
                 for template in range(8)
                 for instance in range(128)]
    combined = parent + additions
    random.Random('release-semantic-v8').shuffle(combined)
    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError(f'Conflicting labels for {row["id"]}')
        if key not in seen:
            seen[key] = label
            unique.append(row)
    output = ROOT / 'data/pilots/release-generalization-v8'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in unique),
                                        encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {
        'version': 'release-generalization-v8',
        'source': 'Fresh semantic disambiguation after V7 held-out failures; no scored rows imported.',
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
