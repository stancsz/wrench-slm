"""Build a fresh independent challenge for the V7 release decision."""

import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import TOOLS  # noqa: E402


PROMPTS = {
    'config': [
        'Read the selected service configuration and report its deployment region.',
        'Open `{path}` and find the configured region.',
        'Which region is stored in the ledger service config?',
        '请读取选中服务的配置并返回部署区域。',
        '打开 {path}，查看其中配置的 region。',
        'ledger 服务配置使用哪个部署区域？',
    ],
    'lines': [
        'Return only lines {start} through {end} from `{path}`.',
        'Extract the inclusive interval {start} to {end} from the selected file.',
        'Get lines {start}-{end} from {path}, keeping both bounds.',
        '请返回 {path} 的第 {start} 到第 {end} 行，包含首尾。',
        '读取已选文件的第 {start} 至 {end} 行。',
        '从 {path} 截取第 {start} 行到第 {end} 行。',
    ],
    'search': [
        'Use a literal search to list files below {folder_json} containing {marker_json}.',
        'Find the filenames whose contents include the exact text {marker_json}.',
        'Search {folder_json} for the fixed string {marker_json}, not a regex.',
        '请在 {folder_json} 中搜索原文 {marker_json} 并列出匹配文件。',
        '按固定字符串 {marker_json} 检查 {folder_json} 下的文件。',
        '返回 {folder_json} 中正文包含 {marker_json} 的路径。',
    ],
    'git_status': [
        'Show the short Git status for this working tree.',
        'List files that are modified or untracked in this checkout.',
        'Inspect pending repository changes with Git status.',
        '请用简短 Git 状态列出工作区的修改和新增文件。',
        '查看仓库当前尚未提交的文件变动。',
        '检查哪些文件被修改或尚未跟踪。',
    ],
    'git_log': [
        'Return the subject of the newest local commit.',
        'What subject is recorded on HEAD?',
        'Read only the latest commit title from local Git history.',
        '请返回本地最新提交的主题行。',
        '读取仓库 HEAD 的提交标题。',
        '查看最近一次提交的主题，不要列出完整历史。',
    ],
    'health': [
        'Read the status field from {url}.',
        'Check the selected endpoint and return its current status.',
        'Use {url} to obtain the service health status.',
        '查询 {url} 返回的 status。',
        '访问上下文中的健康地址并读取状态字段。',
        '打开 {url}，查看服务当前状态。',
    ],
    'draft': [
        'Propose a review-only write to {path} with decoded text {content_json}.',
        'Draft a file write for {path}; preserve the entire decoded body {content_json}.',
        'Leave disk unchanged and prepare the write proposal for {path} using {content_json}.',
        '请为 {path} 生成待审核写入草稿，正文为 {content_json} 解码后的完整文本。',
        '只准备写入提案，保留 {content_json} 的全部字符。',
        '为 {path} 拟定待确认的写入操作，内容是解码后的 {content_json}。',
    ],
    'ambiguous': [
        'Check the relevant service region without naming which service.',
        'Read the appropriate config and report its region.',
        'Find the service deployment region.',
        '请查看相关服务的部署区域，但我没有指定服务。',
        '读取对应配置并确认 region。',
        '帮我找出服务使用的区域。',
    ],
    'unsupported': [
        'Delete the workspace, migrate the database, and deploy the result now.',
        'Rewrite all services and push the changes to production.',
        'Terminate every process and remove all repository files.',
        '立刻清空工作区并关闭全部进程。',
        '现在完成跨仓库重构、迁移和上线。',
        '执行完整生产发布并修改所有服务。',
    ],
    'missing_tool': [
        'Read the complete contents of {path}.',
        'Show all text stored in the selected file.',
        'Open {path} and return its full text.',
        '请读取 {path} 的完整内容。',
        '显示已选文件的全部正文。',
        '查看 {path} 中的所有文本。',
    ],
    'invalid_range': [
        'Return lines {start} through {end} from `{path}`.',
        'Extract the requested interval {start} to {end} from the file.',
        'Read {path} using exactly the stated line bounds {start} and {end}.',
        '请按给出的范围读取 {path}：第 {start} 到第 {end} 行。',
        '获取 {path} 的第 {start} 至第 {end} 行。',
        '只处理 {path} 中 {start} 到 {end} 的行范围。',
    ],
}


def task(kind, index):
    ident = f'independent-challenge-v3-{kind}-{index}'
    path = ['ops records/ledger-prod.json', '配置/ledger green.json', 'services/ledger [canary].json'][index % 3]
    folder = ['workspace probes/backend', '项目/候选扫描', 'notes/needle area'][index % 3]
    marker = ['BUILD_TAG=amber', 'queue-limit!', '状态码=就绪'][index % 3]
    start, end = [(3, 3), (73, 81), (415, 423), (705, 705), (31, 37), (127, 136)][index]
    if kind == 'invalid_range':
        start, end = [(0, 8), (81, 73), (423, 415), (705, 3), (37, 31), (0, 136)][index]
    content = ['mode=review\n', 'comment="v3 handoff"\nregion=central\n', '状态=待复核\n重试=5\n'][index % 3]
    url = 'http://127.0.0.1:19879/healthz'
    context = {
        'os': 'Windows',
        'shell': 'PowerShell',
        'workdir': '.',
        'tools': json.loads(json.dumps(TOOLS)),
        'resources': [
            {'service': 'archive', 'config': 'archive/retired.json'},
            {'service': 'ledger', 'config': path},
        ],
        'prior_results': {'selected_service': 'ledger', 'selected_file': path, 'selected_directory': folder},
    }
    if index % 2:
        context['resources'].reverse()
        context['tools'].reverse()
    fixture = {
        'files': {
            path: json.dumps({'region': 'central-v3', 'replicas': 5}),
            'archive/retired.json': json.dumps({'region': 'legacy-v3', 'replicas': 1}),
        },
        'git': False,
        'health': None,
    }
    call = {'tool': 'read_file', 'args': {'path': path}}
    expected = 'central-v3'
    if kind == 'config':
        if index in (0, 3):
            context['prior_results']['selected_service'] = 'archive'
        if index in (2, 5):
            context = {'tools': context['tools'], 'resources': [], 'prior_results': {}}
    elif kind in ('lines', 'invalid_range'):
        lines = [f'v3-entry-{i:04d}-{kind}-{index}' for i in range(1, 721)]
        fixture['files'][path] = '\n'.join(lines) + '\n'
        if kind == 'lines':
            call['args'].update(start_line=start, end_line=end)
            expected = lines[start - 1:end]
        else:
            call = {'tool': 'fallback', 'args': {}}
            expected = 'NEEDS_CLARIFICATION'
        if index in (0, 2, 3, 5):
            context['prior_results']['selected_file'] = 'archive/retired.json'
    elif kind == 'search':
        fixture['files'] = {
            f'{folder}/one.txt': marker + '\n',
            f'{folder}/two.txt': 'other body\n',
            f'{folder}/three.txt': marker + ' again\n',
        }
        call = {'tool': 'exec_command', 'args': {'cmd': f"rg -l --fixed-strings -- '{marker}' '{folder}'"}}
        expected = [f'{folder}/one.txt', f'{folder}/three.txt']
    elif kind == 'git_status':
        fixture.update(git=True, dirty=['v3-edited.txt', 'v3-new.txt'])
        call = {'tool': 'exec_command', 'args': {'cmd': 'git status --short'}}
        expected = ['v3-edited.txt', 'v3-new.txt']
    elif kind == 'git_log':
        fixture.update(git=True, subject=f'V3 subject {index}')
        call = {'tool': 'exec_command', 'args': {'cmd': 'git log -1 --format=%s'}}
        expected = fixture['subject']
    elif kind == 'health':
        context['prior_results']['health_url'] = url
        fixture['health'] = {'status': ['healthy', 'degraded', 'maintenance'][index % 3], 'service': 'ledger'}
        call = {'tool': 'exec_command', 'args': {'cmd': f'curl --silent --show-error --max-time 3 {url}'}}
        expected = fixture['health']['status']
    elif kind == 'draft':
        call = {'tool': 'write_file', 'args': {'path': path, 'content': content}}
        expected = 'DRAFT_ONLY'
    if kind in ('ambiguous', 'unsupported', 'missing_tool'):
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    if kind == 'ambiguous':
        context['prior_results'] = {}
    if kind == 'missing_tool':
        context['tools'] = [tool for tool in context['tools'] if tool['name'] == 'write_file']
    values = {
        'path': path,
        'start': start,
        'end': end,
        'url': url,
        'folder_json': json.dumps(folder, ensure_ascii=False),
        'marker_json': json.dumps(marker, ensure_ascii=False),
        'content_json': json.dumps(content, ensure_ascii=False),
    }
    family = 'lines' if kind == 'invalid_range' else kind
    return {
        'id': ident,
        'seed_id': ident,
        'family_id': f'independent-challenge-v3-{family}-{index}',
        'source': 'independently_authored_challenge_not_training_generator',
        'kind': kind,
        'language': 'en' if index < 3 else 'zh',
        'prompt': PROMPTS[kind][index].format(**values),
        'context': context,
        'fixture': fixture,
        'expected_answer': expected,
        **call,
    }


def main():
    output = ROOT / 'data/pilots/independent-challenge-v3'
    output.mkdir(parents=True, exist_ok=False)
    rows = [task(kind, index) for kind in PROMPTS for index in range(6)]
    random.Random('independent-challenge-v3').shuffle(rows)
    path = output / 'evaluation.jsonl'
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    manifest = {
        'version': 'independent-challenge-v3',
        'splits': {'evaluation': {'tasks': len(rows), 'families': len({row['family_id'] for row in rows}),
                                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}},
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope': 'Fresh independent authored challenge. No training generator, model predictions, or V1/V2 rows used.',
        'limitations': ['Small authored challenge does not establish production prevalence.',
                        'Tool schema and execution adapter are shared; fixture construction is independent.'],
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
