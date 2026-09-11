"""Fresh authored tasks for the bounded selective-offload experiment.

This module deliberately does not reuse the V1/V2 wording families. Private
fixture fields stay out of ``public_record`` and are used only by the
disposable evaluator.
"""

import hashlib
import json
import random
from pathlib import Path

from .pilot_tasks import TOOLS

FAMILY_PROMPTS = {
    'config': [
        ('en', 'Use the selected service configuration to identify its deployment region.'),
        ('zh', '请从已选服务的配置中找出部署区域。'),
        ('en', 'Inspect the JSON settings associated with the chosen service and report the region value.'),
        ('zh', '查看当前选定服务的 JSON 设置，并返回 region 值。'),
        ('en', 'The active service has a configuration resource. What region is recorded there?'),
        ('zh', '当前服务的配置资源里记录了哪个 region？'),
        ('en', 'Resolve the selected service to its config file and extract the deployment region.'),
        ('zh', '请根据已选择的服务定位配置文件，提取部署区域。'),
        ('en', 'Read the configuration belonging to the active service and give only its region.'),
        ('zh', '读取当前服务对应的配置，只返回它的 region。'),
        ('en', 'Find the region field for the service named in the preceding selection.'),
        ('zh', '查找前面选择的服务所使用的 region 字段。'),
        ('en', 'Report the configured deployment region for the service already selected.'),
        ('zh', '返回已经选定服务的配置部署区域。'),
        ('en', 'From the visible service resource, determine the JSON region setting.'),
        ('zh', '根据可见的服务资源确定 JSON 中的 region 设置。'),
        ('en', 'Check the active service settings and state the configured region value.'),
        ('zh', '检查当前服务设置并说明配置的 region 值。'),
        ('en', 'Use the service resource in context to retrieve its region field.'),
        ('zh', '使用上下文中的服务资源读取它的 region 字段。'),
    ],
    'lines': [
        ('en', 'Return lines {start} through {end} from {path}, preserving order.'),
        ('zh', '按顺序返回 {path} 第 {start} 到第 {end} 行。'),
        ('en', 'Retrieve the inclusive line interval {start}-{end} from the active file {path}.'),
        ('zh', '读取当前文件 {path} 中的闭区间 {start}-{end}。'),
        ('en', 'Extract numbered lines {start} to {end} from {path}.'),
        ('zh', '提取 {path} 的第 {start} 到第 {end} 行。'),
        ('en', 'Open {path} and provide exactly its requested excerpt, lines {start} through {end}.'),
        ('zh', '打开 {path} 并准确返回第 {start} 到 {end} 行摘录。'),
        ('en', 'Read the bounded portion {start}..{end} of the active text file {path}.'),
        ('zh', '读取当前文本文件 {path} 的限定部分 {start}..{end}。'),
        ('en', 'Give only lines {start} through {end} from {path}.'),
        ('zh', '仅返回 {path} 中第 {start} 到 {end} 行。'),
        ('en', 'Fetch the numbered excerpt {start}-{end} from the workspace file {path}.'),
        ('zh', '获取工作区文件 {path} 的编号摘录 {start}-{end}。'),
        ('en', 'Use the visible file {path} to return lines {start} through {end}.'),
        ('zh', '使用可见文件 {path} 返回第 {start} 到 {end} 行。'),
        ('en', 'Read the exact bounded excerpt {start}-{end} requested from {path}.'),
        ('zh', '读取 {path} 中请求的准确限定摘录 {start}-{end}。'),
    ],
    'search': [
        ('en', 'Locate files containing the exact marker {marker} under {folder}.'),
        ('zh', '在 {folder} 下定位包含确切标记 {marker} 的文件。'),
        ('en', 'Find every filename beneath {folder} that contains the supplied literal {marker}.'),
        ('zh', '找出 {folder} 下包含给定字面文本 {marker} 的所有文件名。'),
        ('en', 'Search {folder} for the exact identifier {marker} and return matching paths.'),
        ('zh', '在 {folder} 中搜索确切标识符 {marker} 并返回匹配路径。'),
        ('en', 'Which files in {folder} include the literal marker {marker}?'),
        ('zh', '{folder} 中哪些文件包含字面标记 {marker}？'),
        ('en', 'Report paths found by an exact-text search for {marker} in {folder}.'),
        ('zh', '返回在 {folder} 中精确搜索 {marker} 找到的路径。'),
        ('en', 'Use the visible directory {folder} and marker {marker} to identify matches.'),
        ('zh', '使用可见目录 {folder} 和标记 {marker} 识别匹配项。'),
        ('en', 'List files under {folder} where the literal token {marker} occurs.'),
        ('zh', '列出 {folder} 下出现字面令牌 {marker} 的文件。'),
        ('en', 'Check {folder} for references to the exact marker {marker}.'),
        ('zh', '检查 {folder} 中对确切标记 {marker} 的引用。'),
        ('en', 'Return filenames with an exact occurrence of {marker} inside {folder}.'),
        ('zh', '返回 {folder} 内确切出现 {marker} 的文件名。'),
    ],
    'git_status': [
        ('en', 'Inspect the checkout and list paths with pending working-tree changes.'),
        ('zh', '检查当前检出并列出工作区中有待处理变更的路径。'),
        ('en', 'Report the filenames Git currently marks as modified or untracked.'),
        ('zh', '返回 Git 当前标记为已修改或未跟踪的文件名。'),
        ('en', 'Before the next commit, identify every dirty path in this repository.'),
        ('zh', '在下一次提交前找出此仓库的所有脏路径。'),
        ('en', 'What paths are not clean in the active Git worktree?'),
        ('zh', '当前 Git 工作树中哪些路径不是干净的？'),
        ('en', 'Read the checkout status and return only the changed path names.'),
        ('zh', '读取检出状态，只返回发生变化的路径名。'),
        ('en', 'Enumerate local modifications and untracked files reported by Git.'),
        ('zh', '列出 Git 报告的本地修改和未跟踪文件。'),
        ('en', 'Check whether this fixture repository has dirty files and name them.'),
        ('zh', '检查这个仓库是否有脏文件并列出它们。'),
        ('en', 'Use the repository status to identify pending file changes.'),
        ('zh', '根据仓库状态识别待处理的文件变更。'),
        ('en', 'Return the paths that would appear in a short Git status listing.'),
        ('zh', '返回短格式 Git 状态列表中会出现的路径。'),
    ],
    'git_log': [
        ('en', 'Give the subject line of the commit currently at the tip of this checkout.'),
        ('zh', '返回当前检出顶端提交的主题行。'),
        ('en', 'Read the newest commit subject from the active repository history.'),
        ('zh', '读取当前仓库历史中最新提交的主题。'),
        ('en', 'What title belongs to HEAD in this Git repository?'),
        ('zh', '这个 Git 仓库的 HEAD 对应什么标题？'),
        ('en', 'Report only the subject of the most recent local commit.'),
        ('zh', '只返回最近一次本地提交的主题。'),
        ('en', 'Inspect the repository tip and state its commit subject.'),
        ('zh', '检查仓库顶端并说明提交主题。'),
        ('en', 'Find the latest commit title in the provided checkout.'),
        ('zh', '查找所提供检出中的最新提交标题。'),
        ('en', 'Use Git history to retrieve the subject at HEAD.'),
        ('zh', '使用 Git 历史读取 HEAD 的主题。'),
        ('en', 'Return the newest commit message subject, without extra text.'),
        ('zh', '返回最新提交消息主题，不要附加文本。'),
        ('en', 'Which subject line was recorded by the last commit?'),
        ('zh', '最近一次提交记录了哪一行主题？'),
    ],
    'health': [
        ('en', 'Query the selected local health endpoint and report its status field.'),
        ('zh', '查询选定的本地健康端点并返回 status 字段。'),
        ('en', 'Use the visible service address to retrieve the current health status.'),
        ('zh', '使用可见服务地址读取当前健康状态。'),
        ('en', 'Check the loopback service endpoint and state the returned status.'),
        ('zh', '检查回环服务端点并说明返回的 status。'),
        ('en', 'Read the known health resource for the active service.'),
        ('zh', '读取当前服务已知的健康资源。'),
        ('en', 'Fetch the local service health response and return only its status.'),
        ('zh', '获取本地服务健康响应，只返回 status。'),
        ('en', 'Inspect the supplied loopback URL for the service status value.'),
        ('zh', '检查给定回环 URL 中的服务 status 值。'),
        ('en', 'Ask the selected health endpoint what state the service reports.'),
        ('zh', '向选定健康端点询问服务报告的状态。'),
        ('en', 'Retrieve the status property from the visible local health response.'),
        ('zh', '从可见的本地健康响应中读取 status 属性。'),
        ('en', 'Check the active service health address and report its state.'),
        ('zh', '检查当前服务健康地址并返回其状态。'),
    ],
    'draft': [
        ('en', 'Prepare a review-only change to {path} containing {content}.'),
        ('zh', '准备仅供审阅的变更，将 {content} 放入 {path}。'),
        ('en', 'Submit a non-applied draft that places {content} in {path}.'),
        ('zh', '提交不执行的草稿，把 {content} 放入 {path}。'),
        ('en', 'Create a proposed write of {content} to {path}, leaving disk untouched.'),
        ('zh', '创建把 {content} 写入 {path} 的提案，不改变磁盘。'),
        ('en', 'Express the requested update to {path} with content {content} as a draft.'),
        ('zh', '将对 {path} 的内容 {content} 更新表达为草稿。'),
        ('en', 'Prepare the exact review proposal for {path}: {content}.'),
        ('zh', '为 {path} 准备准确的审阅提案：{content}。'),
        ('en', 'Return a write proposal for {path} with {content}, without applying it.'),
        ('zh', '返回对 {path} 写入 {content} 的提案，但不要应用。'),
        ('en', 'Draft the human-review change that puts {content} in {path}.'),
        ('zh', '拟定人工审阅变更，将 {content} 放入 {path}。'),
        ('en', 'Provide a reviewable write action for {path} using {content}.'),
        ('zh', '为 {path} 提供使用 {content} 的可审阅写入动作。'),
        ('en', 'Prepare the operation on {path} as an unapplied draft of {content}.'),
        ('zh', '将对 {path} 的 {content} 操作准备为未应用草稿。'),
    ],
    'ambiguous': [
        ('en', 'Find the service region, but no service has been selected yet.'),
        ('zh', '查找服务 region，但目前尚未选择服务。'),
        ('en', 'Use the available configurations to report the region for the intended service.'),
        ('zh', '使用可用配置返回目标服务的 region。'),
    ],
    'unsupported': [
        ('en', 'Compress the workspace into an archive and tell me where it was saved.'),
        ('zh', '将工作区压缩成归档并告诉我保存位置。'),
        ('en', 'Install the requested package and report the installed version.'),
        ('zh', '安装请求的软件包并返回安装版本。'),
    ],
    'missing_tool': [
        ('en', 'Inspect the selected document with the unavailable spreadsheet tool.'),
        ('zh', '使用当前不可用的电子表格工具检查所选文档。'),
        ('en', 'Use the missing database client to query the selected service.'),
        ('zh', '使用缺失的数据库客户端查询所选服务。'),
    ],
    'invalid_range': [
        ('en', 'Return the file excerpt from line {bad_start} through line {bad_end}.'),
        ('zh', '返回文件从第 {bad_start} 行到第 {bad_end} 行的摘录。'),
        ('en', 'Read the selected file using the requested impossible line interval {bad_start}-{bad_end}.'),
        ('zh', '使用请求的无效行区间 {bad_start}-{bad_end} 读取所选文件。'),
    ],
    'over_budget': [
        ('en', 'Use the selected configuration to report its region after considering the following long context: {padding}'),
        ('zh', '考虑以下长上下文后，使用所选配置返回 region：{padding}'),
    ],
}


ELIGIBLE_KINDS = {'config', 'lines', 'search', 'git_status', 'git_log', 'health', 'draft'}
INELIGIBLE_KINDS = {'ambiguous', 'unsupported', 'missing_tool', 'invalid_range', 'over_budget'}


def public_record(task):
    return {'prompt': task['prompt'], 'context': task['context']}


def _digest(campaign, split, kind, family, instance):
    return hashlib.sha256(f'{campaign}:{split}:{kind}:{family}:{instance}'.encode()).hexdigest()


def _tools_without(name):
    return [tool for tool in TOOLS if tool['name'] != name]


def make_task(kind, family_index, instance, split, campaign='selective-offload-v1'):
    digest = _digest(campaign, split, kind, family_index, instance)
    rng = random.Random(digest)
    family_prompt_index = family_index % len(FAMILY_PROMPTS[kind])
    language, template = FAMILY_PROMPTS[kind][family_prompt_index]
    service = 'svc-' + digest[:7]
    path = f'configs/{service}.json'
    folder = 'src/' + digest[7:13]
    marker = 'KEY_' + digest[13:21]
    start = 2 + (int(digest[21:23], 16) % 7)
    end = start + 1 + (int(digest[23:25], 16) % 3)
    content = 'enabled=' + digest[25:33]
    region = 'region-' + digest[33:41]
    bad_start = 11
    bad_end = 3
    url = 'http://127.0.0.1:__PORT__/health'
    padding = ' '.join(f'context-note-{i:04d}-{digest[i % 32]}' for i in range(2300))
    values = locals()
    prompt = template.format(**values)
    resources = [
        {'service': service, 'config': path},
        {'service': 'other-' + digest[:4], 'config': 'configs/other.json'},
    ]
    context = {
        'os': 'Windows', 'shell': 'PowerShell', 'workdir': '.', 'tools': TOOLS,
        'resources': resources,
        'prior_results': {'selected_service': service, 'selected_file': path,
                          'selected_directory': folder, 'health_url': url},
    }
    fixture = {'files': {}, 'git': False, 'health': None}
    fixture['files'][path] = json.dumps({'service': service, 'region': region, 'replicas': 1 + rng.randrange(9)})
    fixture['files']['configs/other.json'] = json.dumps({'service': 'other-' + digest[:4], 'region': 'region-' + digest[41:49]})
    lines = [f'entry-{hashlib.sha256((digest + str(i)).encode()).hexdigest()[:14]}' for i in range(18)]
    call = {'tool': 'read_file', 'args': {'path': path}}
    expected = region

    if kind == 'lines' or kind == 'invalid_range':
        fixture['files'][path] = '\n'.join(lines) + '\n'
        if kind == 'lines':
            call['args'].update(start_line=start, end_line=end)
            expected = lines[start - 1:end]
        else:
            call['args'].update(start_line=bad_start, end_line=bad_end)
            expected = 'NEEDS_CLARIFICATION'
    elif kind == 'search':
        for i in range(5):
            fixture['files'][f'{folder}/module_{i}.txt'] = ('reference ' + marker if i in (1, 4) else 'unrelated') + '\n'
        call = {'tool': 'exec_command', 'args': {'cmd': f'rg -l --fixed-strings -- {marker} {folder}'} }
        expected = [f'{folder}/module_1.txt', f'{folder}/module_4.txt']
    elif kind == 'git_status':
        fixture['git'] = True
        fixture['dirty'] = ['changed_' + digest[:6] + '.txt', 'new_' + digest[6:12] + '.txt']
        call = {'tool': 'exec_command', 'args': {'cmd': 'git status --short'}}
        expected = sorted(fixture['dirty'])
    elif kind == 'git_log':
        fixture['git'] = True
        fixture['subject'] = 'Refresh service ' + digest[:12]
        call = {'tool': 'exec_command', 'args': {'cmd': 'git log -1 --format=%s'}}
        expected = fixture['subject']
    elif kind == 'health':
        fixture['health'] = {'service': service, 'status': rng.choice(['healthy', 'degraded', 'maintenance'])}
        call = {'tool': 'exec_command', 'args': {'cmd': f'curl --silent --show-error --max-time 3 {url}'}}
        expected = fixture['health']['status']
    elif kind == 'draft':
        call = {'tool': 'write_file', 'args': {'path': path, 'content': content}}
        expected = 'DRAFT_ONLY'
    elif kind == 'ambiguous':
        context['prior_results'] = {}
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'unsupported':
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'missing_tool':
        context['tools'] = _tools_without('read_file')
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'over_budget':
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'

    return {
        'id': f'{split}-{kind}-family-{family_index:03d}-i{instance:02d}',
        'family_id': f'{split}-{kind}-family-{family_index:03d}',
        'source': f'{campaign}_fresh_authoring',
        'kind': kind, 'language': language, 'prompt': prompt, 'context': context,
        **call, 'fixture': fixture, 'expected_answer': expected,
    }


def build_dataset(destination, *, development_families=24, evaluation_families=120,
                  campaign='selective-offload-v1'):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    kinds = list(FAMILY_PROMPTS)
    # Two development families and ten evaluation families per kind.
    dev_counts = {kind: 2 for kind in kinds}
    eval_counts = {kind: 10 for kind in kinds}
    if sum(dev_counts.values()) != development_families or sum(eval_counts.values()) != evaluation_families:
        raise ValueError('Family allocation mismatch')
    split_counts = {'development': dev_counts, 'evaluation': eval_counts}
    split_tasks = {}
    for split, allocation in split_counts.items():
        tasks = []
        for kind in kinds:
            for family_index in range(allocation[kind]):
                for instance in range(5):
                    tasks.append(make_task(kind, family_index, instance, split, campaign))
        random.Random(f'{campaign}-{split}').shuffle(tasks)
        path = destination / f'{split}.jsonl'
        path.write_text(''.join(json.dumps(task, ensure_ascii=False) + '\n' for task in tasks), encoding='utf-8')
        split_tasks[split] = tasks
    family_sets = {split: {task['family_id'] for task in tasks} for split, tasks in split_tasks.items()}
    if family_sets['development'] & family_sets['evaluation']:
        raise ValueError('Development and evaluation families overlap')
    manifest = {
        'version': 'selective-offload-v1',
        'campaign': campaign,
        'source': 'fresh authored families, separate from prior V1/V2 wording families',
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'family_counts': {'development': development_families, 'evaluation': evaluation_families},
        'instances_per_family': 5,
        'kinds': kinds,
        'languages': ['en', 'zh'],
        'splits': {},
        'private_fields': ['fixture', 'expected_answer', 'tool', 'args', 'kind'],
        'inference_fields': ['prompt', 'context'],
        'limitations': [
            'Authored fixtures are not representative production traffic.',
            'The evaluation measures bounded Windows developer-tool workflows only.',
            'The local gate is not a general safety or production claim.',
        ],
    }
    for split, tasks in split_tasks.items():
        path = destination / f'{split}.jsonl'
        manifest['splits'][split] = {
            'tasks': len(tasks),
            'families': len({task['family_id'] for task in tasks}),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'kind_counts': {kind: sum(task['kind'] == kind for task in tasks) for kind in kinds},
            'language_counts': {lang: sum(task['language'] == lang for task in tasks) for lang in ['en', 'zh']},
        }
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest
