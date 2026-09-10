"""Build V13 training-only boundary data from the V12 training split.

V13 targets invalid-range abstention, missing-context abstention, and literal
search discrimination. It never imports scored external rows and preserves the
V12 development and evaluation files byte-for-byte.
"""

from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import TOOLS, public_record
from wrench.protocol import canonical_json


PARENT = ROOT / 'data/pilots/release-generalization-v12'
OUTPUT = ROOT / 'data/pilots/release-generalization-v13'

PROMPTS = {
    'invalid_range': {
        'en': [
            'The requested interval {start} through {end} is invalid for {path}; abstain explicitly.',
            'Do not read {path}: the line request starts at {start} and ends at {end}, which is invalid.',
            'This range is out of bounds for {path} ({start} to {end}). Return the fallback token.',
            'Handle the invalid line bounds {start}-{end} for {path} with an explicit abstention.',
            'The file is selected, but lines {start} through {end} cannot be requested. Abstain.',
            'For {path}, reject the reversed or out-of-range interval {start} to {end}.',
            'Invalid range detected: {path}, start {start}, end {end}. Do not call a tool.',
            'Return ROUTER_FALLBACK for the unusable range {start} through {end} in {path}.',
        ],
        'zh': [
            '{path} 的第 {start} 到第 {end} 行范围无效，请明确放弃。',
            '不要读取 {path}，请求的起止行是 {start} 和 {end}，范围不合法。',
            '{path} 的 {start} 至 {end} 超出有效范围，请返回回退标记。',
            '请对 {path} 的无效行边界 {start}-{end} 进行明确拒绝。',
            '文件已选中，但第 {start} 到第 {end} 行不能请求，请放弃调用。',
            '拒绝 {path} 中反向或越界的 {start} 至 {end} 行区间。',
            '发现无效范围：{path}，起始 {start}，结束 {end}，不要调用工具。',
            '对 {path} 的不可用范围 {start} 到 {end} 返回 ROUTER_FALLBACK。',
        ],
    },
    'ambiguous': {
        'en': [
            'No service is selected. Do not guess a configuration target; abstain.',
            'The service choice is missing, so return the explicit fallback token.',
            'Which region should be read when there is no selected service? Do not infer one.',
            'There is no target object in context. Decline this configuration request.',
            'Without a selected service, the correct action is an explicit abstention.',
            'The request names no file or service. Do not choose a resource yourself.',
            'Selection is absent from prior results. Return ROUTER_FALLBACK.',
            'Resolve this only if a service is selected; otherwise abstain now.',
        ],
        'zh': [
            '当前没有选中的服务，不要猜配置目标，请明确放弃。',
            '服务选择缺失，请返回明确的回退标记。',
            '没有选中服务时应该读取哪个区域？不要自行推断。',
            '上下文没有目标对象，请拒绝这个配置请求。',
            '未选定服务时，正确动作是明确放弃调用。',
            '请求没有文件或服务目标，不要自行选择资源。',
            '之前结果里没有选择，请返回 ROUTER_FALLBACK。',
            '只有选中服务才能处理，否则现在就放弃。',
        ],
    },
    'unsupported': {
        'en': [
            'This asks for deletion and production deployment, outside the read-only contract. Abstain.',
            'Do not execute this database migration or restart request; return the fallback token.',
            'Erasing repository history is unsupported here. Use an explicit abstention.',
            'The requested infrastructure rollout is outside the available tools. Decline it.',
            'Do not destroy or publish anything. This unsupported operation must fall back.',
            'Credential rotation and production changes are not allowed in this contract.',
            'This destructive request has no supported tool. Return ROUTER_FALLBACK.',
            'Reject the requested migration because only bounded inspection is supported.',
        ],
        'zh': [
            '这是删除和生产部署请求，超出只读契约，请明确放弃。',
            '不要执行数据库迁移或重启请求，请返回回退标记。',
            '清除仓库历史不受支持，请明确放弃。',
            '整体基础设施发布超出可用工具范围，请拒绝。',
            '不要销毁或上线任何内容，这个操作必须回退。',
            '凭据轮换和生产修改不在当前契约内。',
            '该破坏性请求没有支持的工具，请返回 ROUTER_FALLBACK。',
            '只支持有限检查，因此拒绝这个迁移请求。',
        ],
    },
    'missing_tool': {
        'en': [
            'Read {path}, but the file-reading tool is unavailable. Abstain explicitly.',
            'The selected file cannot be opened because read_file is not listed. Return fallback.',
            'Do not invent a tool for the complete contents of {path}; use explicit abstention.',
            'Only write_file is available, so a file read must return the fallback token.',
            'The request needs read_file, which is missing from context. Decline it.',
            'There is no supported reader for {path}. Do not call another tool.',
            'File contents cannot be retrieved with the listed tools. Return ROUTER_FALLBACK.',
            'Handle the unavailable file-reading capability by abstaining.',
        ],
        'zh': [
            '要读取 {path}，但文件读取工具不可用，请明确放弃。',
            '工具列表没有 read_file，不能打开选中文件，请回退。',
            '不要为读取 {path} 虚构工具，返回明确放弃。',
            '当前只有 write_file，因此读取文件必须返回回退标记。',
            '请求需要 read_file，但上下文中缺少它，请拒绝。',
            '没有支持 {path} 的读取工具，不要调用其他工具。',
            '列出的工具无法获取文件内容，请返回 ROUTER_FALLBACK。',
            '文件读取能力不可用时应明确放弃。',
        ],
    },
    'search': {
        'en': [
            'Use a literal fixed-string search for {marker_json} under {folder_json}; list matching paths.',
            'Search {folder_json} for the unchanged text {marker_json}, not a regex.',
            'Return files below {folder_json} containing exact marker {marker_json}.',
            'Run the allowlisted fixed-string filename search in {folder_json} for {marker_json}.',
            'Which paths contain {marker_json} beneath {folder_json}? Treat the marker literally.',
            'Inspect {folder_json} and report every file containing {marker_json}.',
            'Find the literal marker {marker_json} in the selected directory {folder_json}.',
            'List matching filenames for the fixed text {marker_json} in {folder_json}.',
        ],
        'zh': [
            '请在 {folder_json} 下对 {marker_json} 做固定字符串搜索并列出路径。',
            '在 {folder_json} 中查找未改变的原文 {marker_json}，不要使用正则。',
            '返回 {folder_json} 下正文包含确切标记 {marker_json} 的文件。',
            '运行允许的字面搜索，检查 {folder_json} 中的 {marker_json}。',
            '哪些路径在 {folder_json} 下包含 {marker_json}？按原文处理。',
            '检查选定目录 {folder_json}，报告包含 {marker_json} 的每个文件。',
            '在 {folder_json} 中查找字面标记 {marker_json}。',
            '列出 {folder_json} 内固定文本 {marker_json} 的匹配文件名。',
        ],
    },
}


def digest(*parts):
    return hashlib.sha256('|'.join(map(str, parts)).encode('utf-8')).hexdigest()


def shell_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


def new_row(kind, language, family, index):
    token = digest('release-generalization-v13', kind, language, family, index)
    service = 'svc-v13-' + token[:8]
    if language == 'zh':
        path = f'配置 v13/{service} 记录 {token[8:14]}.json'
        folder = f'检索区 v13/{token[14:20]}'
    else:
        path = f'project files v13/{service} note {token[8:14]}.json'
        folder = f'search area v13/{token[14:20]}'
    start = 1 + int(token[20:22], 16) % 5
    end = start + 1 + int(token[22:24], 16) % 4
    invalid_mode = index % 4
    if invalid_mode == 0:
        start, end = 0, end
    elif invalid_mode == 1:
        start, end = end, start
    elif invalid_mode == 2:
        start, end = 999, 1004
    else:
        start, end = 12, 4
    marker = ['BUILD-V13=' + token[24:32], 'retry?window=' + token[24:30], '状态码=v13-' + token[24:30]][index % 3]
    tools = copy.deepcopy(TOOLS)
    resources = [
        {'service': service, 'config': path},
        {'service': 'svc-v13-decoy-' + token[32:37], 'config': f'archive-v13/{token[37:43]}.json'},
    ]
    if int(token[43], 16) % 2:
        tools.reverse()
    if int(token[44], 16) % 2:
        resources.reverse()
    context = {
        'os': 'Windows',
        'shell': 'PowerShell',
        'workdir': '.',
        'tools': tools,
        'resources': resources,
        'prior_results': {
            'selected_service': service,
            'selected_file': path,
            'selected_directory': folder,
        },
    }
    fixture = {
        'files': {
            path: json.dumps({'service': service, 'region': 'region-v13-' + token[45:53]}),
            resources[1]['config']: json.dumps({'service': resources[1]['service'], 'region': 'decoy-v13-' + token[53:61]}),
        },
        'git': False,
        'health': None,
    }
    values = {
        'path': path,
        'folder_json': json.dumps(folder, ensure_ascii=False),
        'marker_json': json.dumps(marker, ensure_ascii=False),
        'start': start,
        'end': end,
    }
    prompt = PROMPTS[kind][language][index % len(PROMPTS[kind][language])].format(**values)
    if kind == 'invalid_range':
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'ambiguous':
        context['prior_results'] = {}
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'unsupported':
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'missing_tool':
        context['tools'] = [tool for tool in context['tools'] if tool['name'] == 'write_file']
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    else:
        fixture['files'] = {
            f'{folder}/match-one.txt': marker + '\n',
            f'{folder}/unrelated.txt': 'different v13 body\n',
            f'{folder}/match-two.txt': 'prefix\n' + marker + '\n',
        }
        call = {'tool': 'exec_command', 'args': {
            'cmd': f'rg -l --fixed-strings -- {shell_quote(marker)} {shell_quote(folder)}',
        }}
        expected = [f'{folder}/match-one.txt', f'{folder}/match-two.txt']
    return {
        'id': f'release-generalization-v13-{kind}-{language}-{family}-{index:03d}',
        'family_id': f'release-generalization-v13-{kind}-{language}-{family}',
        'seed_id': f'release-generalization-v13-{kind}-{language}-{family}-{index:03d}',
        'source': 'fresh_v13_boundary_training',
        'kind': kind,
        'language': language,
        'prompt': prompt,
        'context': context,
        **call,
        'fixture': fixture,
        'expected_answer': expected,
    }


def key(row):
    return canonical_json(public_record(row))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=False)
    parent_train = [json.loads(line) for line in (PARENT / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    additions = []
    specs = {
        'invalid_range': (16, 64),
        'ambiguous': (8, 64),
        'unsupported': (8, 64),
        'missing_tool': (8, 64),
        'search': (8, 64),
    }
    for kind, (families, rows_per_family) in specs.items():
        for family in range(families):
            language = 'en' if family % 2 == 0 else 'zh'
            additions.extend(new_row(kind, language, family, index) for index in range(rows_per_family))
    all_train = parent_train + additions
    if len({row['id'] for row in all_train}) != len(all_train):
        raise ValueError('duplicate training IDs')
    seen = defaultdict(set)
    labels = defaultdict(set)
    for row in all_train:
        seen[key(row)].add(row['id'])
        labels[key(row)].add(canonical_json({'tool': row['tool'], 'args': row['args']}))
    if any(len(values) > 1 for values in labels.values()):
        raise ValueError('label conflict')
    for split in ('train', 'development', 'evaluation'):
        source = PARENT / f'{split}.jsonl'
        destination = OUTPUT / f'{split}.jsonl'
        if split == 'train':
            random.Random('shuffle-release-generalization-v13').shuffle(all_train)
            rows = all_train
        else:
            rows = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
        destination.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    parent_dev = (PARENT / 'development.jsonl').read_bytes()
    parent_eval = (PARENT / 'evaluation.jsonl').read_bytes()
    if (OUTPUT / 'development.jsonl').read_bytes() != parent_dev or (OUTPUT / 'evaluation.jsonl').read_bytes() != parent_eval:
        raise ValueError('development or evaluation changed')
    split_rows = {split: [json.loads(line) for line in (OUTPUT / f'{split}.jsonl').read_text(encoding='utf-8').splitlines()] for split in ('train', 'development', 'evaluation')}
    split_keys = {split: {key(row) for row in rows} for split, rows in split_rows.items()}
    split_families = {split: {row['family_id'] for row in rows} for split, rows in split_rows.items()}
    for left in split_keys:
        for right in split_keys:
            if left != right and split_keys[left] & split_keys[right]:
                raise ValueError('cross-split exact input overlap')
            if left != right and split_families[left] & split_families[right]:
                raise ValueError('cross-split family overlap')
    manifest = {
        'version': 'release-generalization-v13',
        'source': 'V12 train plus fresh boundary data; no scored evaluation rows imported.',
        'parent_train_sha256': hashlib.sha256((PARENT / 'train.jsonl').read_bytes()).hexdigest(),
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'new_training_rows': len(additions),
        'dropped_identical_duplicates': 0,
        'label_conflicts': 0,
        'development_unchanged': True,
        'evaluation_unchanged': True,
        'cross_split_families': 0,
        'cross_split_exact_inputs': 0,
        'target_balance': dict(Counter(row['kind'] for row in additions)),
        'splits': {},
    }
    for split, rows in split_rows.items():
        path = OUTPUT / f'{split}.jsonl'
        manifest['splits'][split] = {
            'tasks': len(rows),
            'families': len({row['family_id'] for row in rows}),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'kinds': dict(Counter(row['kind'] for row in rows)),
            'languages': dict(Counter(row['language'] for row in rows)),
        }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    (OUTPUT / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
