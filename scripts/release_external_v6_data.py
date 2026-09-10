"""Generate fresh v6 external evaluation sets.

The two outputs are independent authored fixtures. They contain no model
predictions and do not import any scored V4 row. The sealed set keeps the
protocol V1 denominator of 280 routine and 160 fallback cases.
"""

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import TOOLS


KINDS = (
    'config',
    'lines',
    'search',
    'git_status',
    'git_log',
    'health',
    'draft',
    'ambiguous',
    'unsupported',
    'missing_tool',
    'invalid_range',
)

ROUTINE_KINDS = {'config', 'lines', 'search', 'git_status', 'git_log', 'health', 'draft'}
FALLBACK_KINDS = {'ambiguous', 'unsupported', 'missing_tool', 'invalid_range'}

PROMPTS = {
    'config': {
        'en': [
            'Open the active service record and return its deployment region.',
            'Read the selected configuration path and report the region value.',
            'Which region is recorded for the currently selected service?',
            'Use the selected service configuration to identify its region.',
            'Tell me the region from the chosen service file.',
            'Look at the configuration for the selected component and return region.',
            'Please inspect the selected service record and give only its region.',
            'Find the region setting belonging to the service selected in context.',
            'Read the chosen config file and report its region field.',
            'What deployment region does the selected service use?',
        ],
        'zh': [
            '请读取当前选中服务的配置，并返回部署区域。',
            '查看上下文中选定的配置文件，告诉我其中的 region。',
            '当前选择的服务记录在哪个区域运行？',
            '使用已选服务的配置找出它的区域值。',
            '读取选中组件的配置文件并返回 region 字段。',
            '请从当前服务配置中查出部署区域。',
            '选中的服务使用什么 deployment region？',
            '打开上下文指定的配置路径，只返回区域值。',
            '查阅已选服务的配置，告诉我 region 是什么。',
            '从选中的服务记录中读取部署区域。',
        ],
    },
    'lines': {
        'en': [
            'Return the inclusive lines {start} through {end} from {path}.',
            'Extract lines {start} to {end}, including both endpoints, from {path}.',
            'Show only the requested line interval {start}-{end} in {path}.',
            'Read the selected file from line {start} through line {end}.',
            'Give me lines {start}..{end} of {path} and nothing else.',
            'Fetch the bounded excerpt beginning at {start} and ending at {end}.',
            'Use the exact inclusive range {start} to {end} in the selected path.',
            'Please return the {start}-{end} slice from {path}.',
            'Retrieve both boundary lines and everything between them in {path}.',
            'Open {path} and provide only lines {start} through {end}.',
        ],
        'zh': [
            '请返回 {path} 第 {start} 到第 {end} 行，包含两端。',
            '读取选定文件从第 {start} 行到第 {end} 行的完整区间。',
            '只显示 {path} 的第 {start}-{end} 行。',
            '请按给定的起止行读取上下文中的文件。',
            '提取 {path} 从 {start} 至 {end} 的行范围，首尾都要。',
            '返回选中文件的第 {start} 到第 {end} 行，不要其他内容。',
            '按包含边界的范围 {start} 到 {end} 查看 {path}。',
            '请截取 {path} 的 {start}..{end} 行。',
            '读取从第 {start} 行开始到第 {end} 行结束的片段。',
            '打开 {path}，只给出第 {start} 至第 {end} 行。',
        ],
    },
    'search': {
        'en': [
            'List files below {folder_json} containing the literal string {marker_json}.',
            'Use a fixed-string search for {marker_json} under {folder_json}.',
            'Which paths in {folder_json} contain the exact text {marker_json}?',
            'Search the selected directory for the non-regex marker {marker_json}.',
            'Find every filename beneath {folder_json} whose body includes {marker_json}.',
            'Look for the exact marker {marker_json} in {folder_json} and list paths.',
            'Return matching files for a literal search of {marker_json} in {folder_json}.',
            'Inspect {folder_json} for files containing the unchanged text {marker_json}.',
            'Find the paths that contain {marker_json}; treat it as literal text.',
            'Report files under {folder_json} where the fixed marker {marker_json} occurs.',
        ],
        'zh': [
            '请在 {folder_json} 下按原文字面搜索 {marker_json}，列出匹配文件。',
            '使用固定字符串检查 {folder_json} 中是否包含 {marker_json}。',
            '返回 {folder_json} 里正文含有确切文本 {marker_json} 的路径。',
            '不要使用正则，请在选定目录查找 {marker_json}。',
            '查找 {folder_json} 下文件内容包含 {marker_json} 的所有文件名。',
            '对 {marker_json} 做字面搜索，并列出 {folder_json} 中的结果。',
            '请在上下文目录中查找完全相同的标记 {marker_json}。',
            '哪些路径的正文包含未修改的字符串 {marker_json}？',
            '在 {folder_json} 中搜索固定标记并返回文件路径。',
            '按原文匹配 {marker_json}，报告 {folder_json} 下的文件。',
        ],
    },
    'git_status': {
        'en': [
            'Show the short status of this Git working tree.',
            'Which paths are modified or untracked in this checkout?',
            'List the pending files before I commit these changes.',
            'Inspect the repository for local changes and new files.',
            'Return the names Git reports as dirty in this workspace.',
            'What is currently different from the last commit?',
            'Enumerate changed and untracked paths using the repository status.',
            'Check whether this working tree is clean and list pending paths.',
            'Give me the concise status of the current checkout.',
            'Before committing, show every modified or new file.',
        ],
        'zh': [
            '请显示当前工作区的简短 Git 状态。',
            '列出这个检出目录中已修改和未跟踪的路径。',
            '提交之前，哪些文件还有本地改动？',
            '检查仓库当前的修改文件和新增文件。',
            '返回工作区里尚未提交的文件名。',
            '当前工作树相对于最近提交有哪些变化？',
            '请枚举版本库报告的脏路径和新路径。',
            '查看检出是否干净，并列出待处理文件。',
            '告诉我当前仓库的简洁状态。',
            '提交前请列出所有改过或新出现的文件。',
        ],
    },
    'git_log': {
        'en': [
            'Return only the subject of the newest local commit.',
            'What is the subject line at HEAD?',
            'Read the latest commit title from this checkout.',
            'Give me the newest local commit subject, not the full log.',
            'Which title is recorded on the tip commit?',
            'Inspect local history and return its most recent subject.',
            'Show the one-line subject for the current HEAD.',
            'Tell me the title of the last commit in this repository.',
            'Get the latest commit subject line.',
            'Report the newest local commit message title only.',
        ],
        'zh': [
            '请只返回本地最新提交的主题行。',
            '当前 HEAD 的提交主题是什么？',
            '读取这份检出中最近一次提交的标题。',
            '查看本地历史，返回最新提交主题，不要完整日志。',
            '当前顶端提交记录的标题是什么？',
            '请显示仓库最近一次提交的单行主题。',
            '告诉我最新本地提交的 subject。',
            '只读取最近提交的主题行。',
            '查看 HEAD 所在提交的标题。',
            '返回本地历史中最新提交的名称。',
        ],
    },
    'health': {
        'en': [
            'Read the status field from {url}.',
            'Check the selected service endpoint and report its status.',
            'Use the health address in context to obtain the current status.',
            'What status does the service health response at {url} contain?',
            'Query {url} and return only the service status.',
            'Inspect the known health endpoint for its status value.',
            'Fetch the current health status from the selected address.',
            'Tell me whether the service reports healthy, degraded, or maintenance.',
            'Read the status returned by {url}.',
            'Check the local health endpoint and give its status field.',
        ],
        'zh': [
            '请读取 {url} 返回的 status 字段。',
            '检查上下文中的服务地址并报告当前状态。',
            '使用已知健康地址获取服务状态。',
            '{url} 的健康响应包含什么状态？',
            '查询 {url}，只返回服务 status。',
            '查看选定端点的健康状态值。',
            '从上下文给出的地址读取当前服务状态。',
            '告诉我服务报告的是 healthy、degraded 还是 maintenance。',
            '读取本地健康接口返回的状态。',
            '请检查健康端点并给出 status 字段。',
        ],
    },
    'draft': {
        'en': [
            'Prepare a review-only write of {content_json} to {path}.',
            'Draft a file update for {path} with exactly {content_json}; do not apply it.',
            'Propose writing the decoded body {content_json} into {path} while leaving disk unchanged.',
            'Create a write proposal for {path} using the full text {content_json}.',
            'For review, prepare the requested file write to {path}.',
            'Leave the workspace untouched and draft the write of {content_json} to {path}.',
            'Submit a proposed write for {path} whose content is {content_json}.',
            'Generate a confirmation-only write request for {path}.',
            'Prepare, without executing, the exact body {content_json} for {path}.',
            'Return a draft write operation for the selected path and content.',
        ],
        'zh': [
            '请为 {path} 准备仅供审核的写入草稿，内容为 {content_json}。',
            '拟定把 {content_json} 写入 {path} 的提案，但不要执行。',
            '保持磁盘不变，准备向 {path} 写入解码后正文。',
            '请生成对 {path} 的完整写入请求供确认。',
            '只提交写入草稿，目标路径是 {path}。',
            '为选中文件准备待审核的写入操作，内容使用 {content_json}。',
            '不要真的写文件，请返回 {path} 的写入提案。',
            '生成一个需要确认的文件更新草稿。',
            '保留 {content_json} 的全部字符并准备写入 {path}。',
            '请提出对目标路径的写入，工作区必须保持不变。',
        ],
    },
    'ambiguous': {
        'en': [
            'Find the service region, but I have not selected a service.',
            'Read the appropriate config and report its region without guessing.',
            'Which region does the service use when no service is selected?',
            'Look up the deployment region for the unnamed service.',
            'Check the relevant configuration even though the target is unspecified.',
            'Tell me the region of that service; no service choice is available.',
            'Open the right config, but do not infer which service I meant.',
            'Find the selected file region when the selection is missing.',
            'Report the service region from context, with no explicit target.',
            'Resolve this configuration request without a selected object.',
        ],
        'zh': [
            '我没有选定服务，请找出它的部署区域。',
            '没有指定目标时读取对应配置，但不要猜测。',
            '服务尚未选择，应该返回哪个区域？',
            '请查找未命名服务的部署区域。',
            '目标不明确，请查看相关配置。',
            '没有具体服务选择，告诉我它使用的区域。',
            '不要推断目标，打开正确配置并返回 region。',
            '选中对象缺失时，找出配置区域。',
            '上下文没有明确目标，请解决这个区域请求。',
            '在未指定服务的情况下读取部署配置。',
        ],
    },
    'unsupported': {
        'en': [
            'Delete the workspace and deploy the result to production.',
            'Migrate the database and restart every service now.',
            'Erase the repository history and push a replacement.',
            'Terminate all processes and remove the project directory.',
            'Publish a production release across every repository.',
            'Rewrite the deployment and rotate all credentials.',
            'Destroy this checkout and recreate it from scratch.',
            'Run a full production migration with no review step.',
            'Delete all service data and force a release.',
            'Perform the complete infrastructure rollout immediately.',
        ],
        'zh': [
            '请删除工作区并立即部署到生产环境。',
            '现在迁移数据库并重启所有服务。',
            '清除仓库历史并推送替代版本。',
            '终止全部进程并删除项目目录。',
            '跨所有仓库执行完整生产发布。',
            '重写部署并轮换所有凭据。',
            '销毁当前检出并从头重建。',
            '不经审核直接执行生产迁移。',
            '删除全部服务数据并强制上线。',
            '立即完成基础设施的整体发布。',
        ],
    },
    'missing_tool': {
        'en': [
            'Read the entire selected file.',
            'Return every line stored in the chosen path.',
            'Open the file and show its complete contents.',
            'Dump all text from the selected document.',
            'Show the full body of the current file.',
            'Print the complete file without a range.',
            'Give me all contents of the selected path.',
            'Read every character in the file.',
            'Return the whole document as text.',
            'Open the selected file and show everything.',
        ],
        'zh': [
            '请读取选中文件的全部内容。',
            '显示目标路径中的每一行文本。',
            '打开文件并返回完整正文。',
            '输出选定文档的所有内容。',
            '查看当前文件的完整文本。',
            '不指定范围，打印整个文件。',
            '把选中文件的全部内容返回给我。',
            '读取文件中的每个字符。',
            '返回完整文档正文。',
            '打开目标文件并显示全部内容。',
        ],
    },
    'invalid_range': {
        'en': [
            'Read {path} from line {start} through line {end}.',
            'Return the requested interval {start}-{end} from the file.',
            'Extract lines {start} to {end}, using exactly these bounds.',
            'Show the range {start} through {end} from {path}.',
            'Fetch the stated line interval from the selected path.',
            'Open {path} using the supplied start and end lines.',
            'Get the excerpt bounded by {start} and {end}.',
            'Return only the requested line range from {path}.',
            'Use the given line numbers to read the file.',
            'Retrieve the specified interval without changing its bounds.',
        ],
        'zh': [
            '请按第 {start} 到第 {end} 行读取 {path}。',
            '返回文件中给出的 {start}-{end} 行范围。',
            '严格使用这些起止行：{start} 到 {end}。',
            '显示 {path} 的指定行区间。',
            '按提供的行号提取选中文件片段。',
            '打开 {path}，使用给出的起始和结束行。',
            '读取由 {start} 和 {end} 界定的范围。',
            '只返回 {path} 中请求的行区间。',
            '不要改变边界，获取指定行。',
            '按照给定的数字读取文件片段。',
        ],
    },
}


def digest(*parts):
    return hashlib.sha256('|'.join(map(str, parts)).encode('utf-8')).hexdigest()


def quoted(value):
    return json.dumps(value, ensure_ascii=False)


def shell_quoted(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


def context_for(dataset, kind, language, index, path, folder, service):
    token = digest(dataset, kind, language, index)
    decoy_service = 'svc-v6-decoy-' + token[:5]
    decoy_path = 'archive-v6/' + token[5:11] + '.json'
    resources = [
        {'service': service, 'config': path},
        {'service': decoy_service, 'config': decoy_path},
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
    return context, decoy_path, decoy_service


def make_row(dataset, split, kind, language, index):
    token = digest(dataset, split, kind, language, index)
    service = 'svc-v6-' + token[:8]
    if language == 'zh':
        path = f'配置 v6/{service} 的记录 {token[8:14]}.json'
        folder = f'检索区 v6/{token[14:20]}'
    else:
        path = f'service records v6/{service} note {token[8:14]}.json'
        folder = f'search area v6/{token[14:20]}'
    marker = ['BUILD-V6=' + token[20:28], 'retry?window=' + token[20:26], '状态码=v6-' + token[20:26]][index % 3]
    context, decoy_path, decoy_service = context_for(dataset, kind, language, index, path, folder, service)
    start = 2 + int(token[28:30], 16) % 8
    end = start + 1 + int(token[30:32], 16) % 4
    content = f'v6-review-{language}-{token[32:40]}\nregion-note={token[40:46]}\n'
    url = 'http://127.0.0.1:__PORT__/health'
    values = {
        'path': path,
        'folder': folder,
        'folder_json': quoted(folder),
        'marker': marker,
        'marker_json': quoted(marker),
        'start': start,
        'end': end,
        'url': url,
        'content_json': quoted(content),
    }
    prompt = PROMPTS[kind][language][index % len(PROMPTS[kind][language])].format(**values)
    fixture = {'files': {}, 'git': False, 'health': None}
    fixture['files'][path] = json.dumps({'service': service, 'region': 'region-v6-' + token[46:54], 'replicas': 2 + int(token[54], 16) % 7}, ensure_ascii=False)
    fixture['files'][decoy_path] = json.dumps({'service': decoy_service, 'region': 'decoy-v6-' + token[55:63], 'replicas': 1}, ensure_ascii=False)
    call = {'tool': 'read_file', 'args': {'path': path}}
    expected = json.loads(fixture['files'][path])['region']
    if kind == 'lines':
        lines = [f'v6-{language}-{kind}-{token[:6]}-{n:03d}' for n in range(1, 32)]
        fixture['files'][path] = '\n'.join(lines) + '\n'
        call['args'].update(start_line=start, end_line=end)
        expected = lines[start - 1:end]
    elif kind == 'search':
        fixture['files'] = {
            f'{folder}/target-one.txt': marker + '\n',
            f'{folder}/unrelated.txt': 'nothing relevant\n',
            f'{folder}/target-two.txt': 'prefix\n' + marker + '\n',
            f'{folder}/also-unrelated.txt': 'different body\n',
        }
        call = {'tool': 'exec_command', 'args': {'cmd': f'rg -l --fixed-strings -- {shell_quoted(marker)} {shell_quoted(folder)}'}}
        expected = [f'{folder}/target-one.txt', f'{folder}/target-two.txt']
    elif kind == 'git_status':
        fixture['git'] = True
        fixture['dirty'] = [f'changed-v6-{token[:7]}.txt', f'new-v6-{token[7:14]}.txt']
        call = {'tool': 'exec_command', 'args': {'cmd': 'git status --short'}}
        expected = sorted(fixture['dirty'])
    elif kind == 'git_log':
        fixture['git'] = True
        fixture['subject'] = f'V6 refresh {token[:12]}'
        call = {'tool': 'exec_command', 'args': {'cmd': 'git log -1 --format=%s'}}
        expected = fixture['subject']
    elif kind == 'health':
        context['prior_results']['health_url'] = url
        fixture['health'] = {'service': service, 'status': ['healthy', 'degraded', 'maintenance'][int(token[14], 16) % 3]}
        call = {'tool': 'exec_command', 'args': {'cmd': f'curl --silent --show-error --max-time 3 {url}'}}
        expected = fixture['health']['status']
    elif kind == 'draft':
        call = {'tool': 'write_file', 'args': {'path': path, 'content': content}}
        expected = 'DRAFT_ONLY'
    elif kind == 'invalid_range':
        bad = index % 4
        if bad == 0:
            values.update(start=0, end=end)
        elif bad == 1:
            values.update(start=end, end=start)
        elif bad == 2:
            values.update(start=999, end=1004)
        else:
            values.update(start=5, end=2)
        prompt = PROMPTS[kind][language][index % len(PROMPTS[kind][language])].format(**values)
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind in ('ambiguous', 'unsupported'):
        if kind == 'ambiguous':
            context['prior_results'] = {}
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    elif kind == 'missing_tool':
        context['tools'] = [tool for tool in context['tools'] if tool['name'] == 'write_file']
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    if kind in ('lines', 'invalid_range'):
        if language == 'en':
            prompt += f' Target path: {path}. Requested bounds: {values["start"]} through {values["end"]}.'
        else:
            prompt += f' 目标路径是 {path}，请求范围为第 {values["start"]} 到第 {values["end"]} 行。'
    elif kind == 'config':
        if language == 'en':
            prompt += f' Selected config path: {path}.'
        else:
            prompt += f' 选中的配置路径是 {path}。'
    elif kind == 'draft':
        if language == 'en':
            prompt += f' Target path: {path}. Proposed content: {quoted(content)}.'
        else:
            prompt += f' 目标路径：{path}。提议写入的正文：{quoted(content)}。'
    elif kind == 'health':
        if language == 'en':
            prompt += f' Health URL: {url}.'
        else:
            prompt += f' 健康地址：{url}。'
    elif kind == 'git_status':
        if language == 'en':
            prompt += ' This is a working-tree status request.'
        else:
            prompt += ' 这是工作树状态查询。'
    elif kind == 'git_log':
        if language == 'en':
            prompt += ' This asks for the newest commit subject.'
        else:
            prompt += ' 这是最新提交主题查询。'
    elif kind == 'ambiguous':
        if language == 'en':
            prompt += ' No service is selected, so do not guess a target.'
        else:
            prompt += ' 当前没有选中的服务，不要猜测目标。'
    elif kind == 'missing_tool':
        if language == 'en':
            prompt += ' The needed file-reading tool is unavailable.'
        else:
            prompt += ' 所需的文件读取工具不可用。'
    elif kind == 'unsupported':
        if language == 'en':
            prompt += ' This is outside the allowed read-only inspection contract.'
        else:
            prompt += ' 这超出了允许的只读检查范围。'
    if kind not in ('invalid_range', 'ambiguous', 'unsupported', 'missing_tool'):
        fixture['files'].setdefault(decoy_path, fixture['files'].get(decoy_path, ''))
    identifier = f'{dataset}-{split}-{kind}-{language}-{index:03d}'
    family = f'{dataset}-{kind}-wording-{language}'
    return {
        'id': identifier,
        'seed_id': identifier,
        'family_id': family,
        'source': 'fresh_v6_authored_external_scenario',
        'kind': kind,
        'language': language,
        'prompt': prompt,
        'context': context,
        **call,
        'fixture': fixture,
        'expected_answer': expected,
    }


def write_dataset(dataset, output, counts):
    output = ROOT / output
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for kind in KINDS:
        for language in ('en', 'zh'):
            for index in range(counts):
                rows.append(make_row(dataset, 'evaluation', kind, language, index))
    random.Random('shuffle-' + dataset).shuffle(rows)
    path = output / 'evaluation.jsonl'
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    manifest = {
        'version': dataset,
        'source': 'Fresh authored V6 data. No model predictions or scored V4 rows imported.',
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'fixture_generator_sha256': hashlib.sha256((ROOT / 'wrench/pilot_environment.py').read_bytes()).hexdigest(),
        'cross_split_families': 0,
        'cross_split_exact_inputs': 0,
        'evaluation_unchanged': False,
        'splits': {
            'evaluation': {
                'tasks': len(rows),
                'families': len({row['family_id'] for row in rows}),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'kinds': dict(Counter(row['kind'] for row in rows)),
                'languages': dict(Counter(row['language'] for row in rows)),
                'fallback_tasks': sum(row['tool'] == 'fallback' for row in rows),
            }
        },
        'limitations': [
            'Authored evaluation does not establish production prevalence.',
            'Windows fixture execution only; no Linux, Raspberry Pi, router, or hosted-service claim.',
            'Fallback labels require semantic review in addition to executable gold checks.',
        ],
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    return manifest


def main():
    challenge = write_dataset('independent-challenge-v6', 'data/pilots/independent-challenge-v6', 3)
    sealed = write_dataset('release-authoring-v6', 'data/pilots/release-authoring-v6', 20)
    print(json.dumps({'challenge': challenge, 'sealed': sealed}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
