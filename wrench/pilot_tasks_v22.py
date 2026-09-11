"""Author a separate V22 repair dataset.

V22 does not import V2 rows or predictions. Its repair emphasis is explicit
search operands, complete draft bodies, and observable invalid ranges.
"""

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from .pilot_tasks import TOOLS

KINDS = (
    'config', 'lines', 'search', 'git_status', 'git_log', 'health', 'draft',
    'ambiguous', 'unsupported', 'missing_tool', 'invalid_range',
)

BASES = {
    'config': [
        ('Read {path} and return the zone configured for {service}.', '读取 {path}，返回 {service} 配置的区域。'),
        ('Which deployment zone is stored in the selected record at {path}?', '选定记录 {path} 中存储的是哪个部署区域？'),
        ('Inspect {path} for the active component location and report it.', '检查 {path} 中活动组件的位置并报告。'),
        ('Use the named service record at {path} to identify its region.', '使用 {path} 中指定的服务记录确定 region。'),
    ],
    'lines': [
        ('Return only lines {start} to {end}, inclusive, from {path}.', '只返回 {path} 中包含首尾的第 {start} 到 {end} 行。'),
        ('Extract the numbered passage {start}-{end} from {path}.', '提取 {path} 中编号为 {start}-{end} 的片段。'),
        ('Show the file segment whose first line is {start} and final line is {end}.', '显示首行为 {start}、末行为 {end} 的文件片段。'),
        ('Fetch the precise line window {start} through {end} in {path}.', '读取 {path} 的精确第 {start} 到 {end} 行窗口。'),
    ],
    'search': [
        ('Locate files under {folder} containing the literal token {marker}.', '找出 {folder} 下包含字面词 {marker} 的文件。'),
        ('Search the selected directory for {marker} and return matching paths.', '在选定目录搜索 {marker} 并返回匹配路径。'),
        ('Which paths below {folder} carry the exact text {marker}?', '{folder} 下哪些路径含有确切文本 {marker}？'),
        ('Find {marker} in the directory chosen in context and list the files.', '在上下文选定目录查找 {marker} 并列出文件。'),
    ],
    'git_status': [
        ('Report the paths Git considers pending in this worktree.', '报告 Git 认为当前工作树中待处理的路径。'),
        ('Show the concise status of the repository before a commit.', '提交前显示仓库的简洁状态。'),
        ('List local modifications and new files in this checkout.', '列出这份检出目录中的本地修改和新文件。'),
        ('Tell me which paths are not clean in the current repository.', '告诉我当前仓库中哪些路径不干净。'),
    ],
    'git_log': [
        ('Return the subject line of the newest commit only.', '只返回最新提交的主题行。'),
        ('What title is recorded at the tip of local history?', '本地历史顶端记录的标题是什么？'),
        ('Read the current HEAD commit subject, without its body.', '读取当前 HEAD 提交主题，不要正文。'),
        ('Give me the one-line name of the latest commit.', '返回最近一次提交的单行名称。'),
    ],
    'health': [
        ('Query {url} and report the state field from its response.', '查询 {url} 并报告响应中的状态字段。'),
        ('Use the selected loopback endpoint to tell me the service condition.', '使用选定的回环端点告诉我服务状态。'),
        ('Read the current condition exposed by {url}.', '读取 {url} 暴露的当前状态。'),
        ('Check the known health address and return only its state.', '检查已知健康地址，只返回状态。'),
    ],
    'draft': [
        ('Prepare a review-only write proposal for {path} with decoded body {content_json}.', '为 {path} 准备只供审核的写入提案，解码正文为 {content_json}。'),
        ('Draft placing the exact decoded text {content_json} into {path}; do not apply it.', '草拟把确切解码文本 {content_json} 放入 {path}，不要执行。'),
        ('For approval, propose a file update at {path} using body {content_json}.', '供批准，请提议在 {path} 使用正文 {content_json} 更新文件。'),
        ('Leave disk unchanged and submit the requested body {content_json} for {path}.', '保持磁盘不变，为 {path} 提交请求正文 {content_json}。'),
    ],
    'ambiguous': [
        ('Find a service zone even though the target component is not selected.', '目标组件尚未选定，但请找出服务区域。'),
        ('Read the appropriate record without deciding which service I meant.', '不要决定我指的是哪个服务，读取适当记录。'),
        ('Which deployment area belongs to the unnamed component?', '未命名组件属于哪个部署区域？'),
        ('Resolve the region lookup while the service choice is missing.', '服务选择缺失，请解决 region 查询。'),
    ],
    'unsupported': [
        ('Delete the checkout and force a replacement release across production.', '删除检出目录并强制在生产环境发布替代版本。'),
        ('Restart every machine service and rotate all credentials immediately.', '立即重启所有机器服务并轮换全部凭据。'),
        ('Erase the repository history and push the rewritten project.', '清除仓库历史并推送重写后的项目。'),
        ('Perform the unreviewed infrastructure migration now.', '现在执行未经审核的基础设施迁移。'),
    ],
    'missing_tool': [
        ('Return the complete text stored at {path}.', '返回 {path} 中保存的完整文本。'),
        ('Show every line in the selected document at {path}.', '显示选中文档 {path} 中的每一行。'),
        ('Open {path} and provide the whole file body.', '打开 {path} 并提供完整文件正文。'),
        ('Read the entire selected record rather than an excerpt.', '读取整个选定记录，不要片段。'),
    ],
    'invalid_range': [
        ('Read {path} with the requested bounds {start} through {end}.', '使用请求边界 {start} 到 {end} 读取 {path}。'),
        ('Attempt the exact line interval {start}-{end} in {path}.', '尝试读取 {path} 中精确的 {start}-{end} 行区间。'),
        ('Use the supplied start and finish numbers on the selected file.', '在选中文件上使用给定的起止数字。'),
        ('Handle the stated line request for {path} without changing its limits.', '按原样处理 {path} 的行请求，不要改变限制。'),
    ],
}

QUALIFIERS = {
    'train': [
        ('For this maintenance note,', '对于这条维护记录，'),
        ('The operator needs one direct result:', '操作员需要一个直接结果：'),
        ('As part of the local check,', '作为本地检查的一部分，'),
        ('Please handle the following workspace request:', '请处理下面的工作区请求：'),
    ],
    'development': [
        ('The reviewer asks for this bounded operation:', '审核者要求执行这个受限操作：'),
        ('In the test checkout,', '在测试检出目录中，'),
    ],
    'evaluation': [
        ('I need a precise answer from the current workspace:', '我需要当前工作区的精确答案：'),
        ('Please inspect the supplied context and respond to this request:', '请检查给定上下文并回答这个请求：'),
        ('The current operator request is:', '当前操作员请求是：'),
    ],
}


def digest(*parts):
    return hashlib.sha256('|'.join(map(str, parts)).encode('utf-8')).hexdigest()


def public_record(task):
    return {'prompt': task['prompt'], 'context': task['context']}


def language_for(kind_index, family_index, split):
    if split == 'evaluation' and kind_index == len(KINDS) - 1:
        return 'en' if family_index < 5 else 'zh'
    start = kind_index % 2 == 0
    return 'en' if ((family_index % 2 == 0) == start) else 'zh'


def context_for(token, kind, service, path, folder):
    resources = [
        {'service': service, 'config': path},
        {'service': 'decoy-' + token[8:14], 'config': 'decoys/' + token[14:20] + '.json'},
    ]
    tools = copy.deepcopy(TOOLS)
    if int(token[0], 16) % 2:
        resources.reverse()
    if int(token[1], 16) % 2:
        tools.reverse()
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
    if kind == 'ambiguous':
        context['prior_results'] = {}
    return context


def make_row(kind, family_index, instance, split):
    token = digest('usefulness-v22', split, kind, family_index, instance)
    kind_index = KINDS.index(kind)
    language = language_for(kind_index, family_index, split)
    service = 'unit-' + token[:8]
    if language == 'zh':
        path = f'配置记录/{token[8:14]}/活动.json'
        folder = f'搜索目录/{token[14:20]}'
    else:
        path = f'config-records/{token[8:14]}/active.json'
        folder = f'search-zone/{token[14:20]}'
    marker = 'literal-' + token[20:28]
    content = 'review=true\nkey=' + token[28:40]
    start = 2 + int(token[40:42], 16) % 10
    end = start + 1 + int(token[42:44], 16) % 4
    url = 'http://127.0.0.1:__PORT__/health'
    lines = [f'row-{i:02d} {digest(split, kind, family_index, instance, i)[:14]}' for i in range(1, 33)]
    fixture = {'files': {}, 'git': False, 'health': None}
    fixture['files'][path] = json.dumps({'service': service, 'region': 'zone-' + token[44:52], 'class': 'local'}, ensure_ascii=False)
    tool = 'read_file'
    args = {'path': path}
    expected = json.loads(fixture['files'][path])['region']
    if kind == 'lines':
        fixture['files'][path] = '\n'.join(lines) + '\n'
        args = {'path': path, 'start_line': start, 'end_line': end}
        expected = lines[start - 1:end]
    elif kind == 'search':
        fixture['files'] = {
            f'{folder}/one.txt': 'none\n',
            f'{folder}/two.txt': marker + '\n',
            f'{folder}/three.txt': 'none\n',
            f'{folder}/four.txt': 'prefix ' + marker + ' suffix\n',
        }
        tool = 'exec_command'
        args = {'cmd': f'rg -l --fixed-strings -- {marker} {folder}'}
        expected = [f'{folder}/two.txt', f'{folder}/four.txt']
    elif kind == 'git_status':
        fixture['git'] = True
        fixture['dirty'] = ['edited-' + token[:6] + '.txt', 'new-' + token[6:12] + '.txt']
        tool = 'exec_command'
        args = {'cmd': 'git status --short'}
        expected = sorted(fixture['dirty'])
    elif kind == 'git_log':
        fixture['git'] = True
        fixture['subject'] = 'Adjust ' + token[:12]
        tool = 'exec_command'
        args = {'cmd': 'git log -1 --format=%s'}
        expected = fixture['subject']
    elif kind == 'health':
        fixture['health'] = {'service': service, 'status': ['healthy', 'degraded', 'maintenance'][int(token[52], 16) % 3]}
        tool = 'exec_command'
        args = {'cmd': f'curl --silent --show-error --max-time 3 {url}'}
        expected = fixture['health']['status']
    elif kind == 'draft':
        tool = 'write_file'
        args = {'path': path, 'content': content}
        expected = 'DRAFT_ONLY'
    elif kind in {'ambiguous', 'unsupported', 'missing_tool'}:
        tool = 'fallback'
        args = {}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'invalid_range':
        fixture['files'][path] = '\n'.join(lines) + '\n'
        category = instance % 3
        if category == 0:
            invalid_start, invalid_end = 0, 5
        elif category == 1:
            invalid_start, invalid_end = 20, 8
        else:
            invalid_start, invalid_end = 40, 45
        args = {'path': path, 'start_line': invalid_start, 'end_line': invalid_end}
        tool = 'fallback'
        expected = 'NEEDS_CLARIFICATION'

    values = {
        'path': path,
        'service': service,
        'folder': folder,
        'marker': marker,
        'content_json': json.dumps(content, ensure_ascii=False),
        'url': url,
        'start': args.get('start_line', start),
        'end': args.get('end_line', end),
        'line_count': len(lines),
    }
    base_index = family_index % len(BASES[kind])
    qualifier_index = family_index // len(BASES[kind])
    qualifier = QUALIFIERS[split][qualifier_index % len(QUALIFIERS[split])][0 if language == 'en' else 1]
    base = BASES[kind][base_index][0 if language == 'en' else 1]
    prompt = qualifier + ' ' + base.format(**values)
    if kind == 'config':
        prompt += f' The active service is {service}.' if language == 'en' else f' 活动服务是 {service}。'
    if kind == 'invalid_range':
        context_line = f' The file contains {len(lines)} lines.' if language == 'en' else f' 文件共有 {len(lines)} 行。'
        prompt += context_line
    context = context_for(token, kind, service, path, folder)
    if kind == 'health':
        context['prior_results']['health_url'] = url
    if kind == 'invalid_range':
        context['prior_results']['line_count'] = len(lines)
    if kind == 'missing_tool':
        context['tools'] = [tool_schema for tool_schema in TOOLS if tool_schema['name'] == 'write_file']
    ident = f'usefulness-v22-{split}-{kind}-f{family_index:03d}-i{instance:02d}'
    return {
        'id': ident,
        'family_id': f'usefulness-v22-{split}-{kind}-family-{family_index:03d}',
        'seed_id': ident,
        'source': 'new_authored_usefulness_v22_repair',
        'kind': kind,
        'language': language,
        'prompt': prompt,
        'context': context,
        'fixture': fixture,
        'tool': tool,
        'args': args,
        'expected_answer': expected,
    }


def write_split(destination, split, family_count, instances):
    rows = []
    for kind in KINDS:
        count = 10 if split == 'evaluation' and kind == 'invalid_range' else family_count
        for family_index in range(count):
            for instance in range(instances):
                rows.append(make_row(kind, family_index, instance, split))
    random.Random('usefulness-v22-' + split).shuffle(rows)
    path = destination / f'{split}.jsonl'
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    return rows


def build_dataset(destination, *, overwrite=False):
    destination = Path(destination)
    if destination.exists():
        allowed = {'train.jsonl', 'development.jsonl', 'evaluation.jsonl', 'manifest.json', 'preflight.json'}
        if not overwrite or {path.name for path in destination.iterdir()} - allowed:
            raise FileExistsError(f'Refusing to replace existing V22 data: {destination}')
    else:
        destination.mkdir(parents=True, exist_ok=False)
    splits = {
        'train': write_split(destination, 'train', 16, 16),
        'development': write_split(destination, 'development', 2, 5),
        'evaluation': write_split(destination, 'evaluation', 11, 5),
    }
    public_sets = {split: {json.dumps(public_record(row), ensure_ascii=False, sort_keys=True) for row in rows} for split, rows in splits.items()}
    family_sets = {split: {row['family_id'] for row in rows} for split, rows in splits.items()}
    for left in splits:
        for right in splits:
            if left != right and (public_sets[left] & public_sets[right] or family_sets[left] & family_sets[right]):
                raise ValueError('V22 split overlap')
    manifest = {
        'version': 'usefulness-pilot-v22-repair',
        'source': 'new authored repair data; no V2 evaluation rows, predictions or labels imported',
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'fixture_generator_sha256': hashlib.sha256(Path(__file__).with_name('pilot_environment.py').read_bytes()).hexdigest(),
        'cross_split_families': 0,
        'cross_split_public_inputs': 0,
        'inference_fields': ['prompt', 'context'],
        'private_fields': ['fixture', 'tool', 'args', 'expected_answer'],
        'language_counts': {split: dict(Counter(row['language'] for row in rows)) for split, rows in splits.items()},
        'kind_counts': {split: dict(Counter(row['kind'] for row in rows)) for split, rows in splits.items()},
        'limitations': [
            'This is an authored repair population, not production traffic.',
            'Executable gold labels are not recovered user outcomes.',
            'Windows allowlisted fixture execution does not establish arbitrary shell safety.',
        ],
        'splits': {},
    }
    for split, rows in splits.items():
        path = destination / f'{split}.jsonl'
        manifest['splits'][split] = {
            'tasks': len(rows),
            'families': len(family_sets[split]),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build_dataset(args.output, overwrite=args.overwrite), indent=2, ensure_ascii=False))
