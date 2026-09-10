"""Build a fresh independent challenge for the post-V6 release decision.

This generator is intentionally separate from the training and release-data
generators. Freeze its JSONL and manifest before invoking any model.
"""

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
        'Find the deployment region for ledger, using its entry in the resources.',
        'Read the region belonging to the service selected in the prior context.',
        'Open `{path}` and inspect its region field.',
        '我要核对 ledger 的部署区域，请读取对应配置。',
        '请查看当前选中服务的区域配置，不要沿用旧文件。',
        '读取 {path} 中保存的区域设置。',
    ],
    'lines': [
        'Return only lines {start} through {end} from `{path}`.',
        'Extract the inclusive line interval {start} to {end} from the selected file.',
        'From {path}, obtain exactly lines {start} through {end}.',
        '请取出 {path} 的第 {start} 行到第 {end} 行，包含两端。',
        '已选文件中的第 {start} 至第 {end} 行是目标片段，请读取。',
        '查看 {path}，只返回第 {start} 至第 {end} 行。',
    ],
    'search': [
        'Find filenames under {folder_json} whose contents contain the literal {marker_json}.',
        'Search the selected directory for the exact string {marker_json}, not a regex.',
        'List files in {folder_json} that include {marker_json} in their contents.',
        '在 {folder_json} 中按固定字符串 {marker_json} 搜索并列出匹配文件。',
        '请找出所选目录下含有 {marker_json} 原文的文件，不要解释为正则。',
        '列出 {folder_json} 中正文包含 {marker_json} 的文件路径。',
    ],
    'git_status': [
        'Inspect tracked edits and untracked files in this checkout.',
        'Show the current repository status in short form.',
        'Which files are changed or new according to Git?',
        '请检查这个工作区尚未提交的修改和新增文件。',
        '用 Git 简要列出仓库当前的文件状态。',
        '我需要知道哪些文件改动了，哪些还没有被 Git 跟踪。',
    ],
    'git_log': [
        'Read local history and return the subject of the newest commit.',
        'What subject line is attached to HEAD?',
        'Get the last commit subject without listing the whole history.',
        '我想看最近提交的主题，不需要完整历史。',
        '请读取仓库 HEAD 对应的提交标题。',
        '返回本地最新提交的主题行。',
    ],
    'health': [
        'Read the status reported at {url}.',
        'Check the selected health endpoint for its current status.',
        'Consult {url} and obtain its status field.',
        '查询 {url} 返回的服务健康状态。',
        '使用上下文里选中的健康地址读取 status。',
        '请打开 {url} 并查看状态字段。',
    ],
    'draft': [
        'For review, propose writing the decoded JSON text {content_json} to {path}.',
        'Prepare a file-write draft for the selected file with text decoded from {content_json}.',
        'Leave the filesystem untouched and propose {content_json} decoded into {path}.',
        '请为 {path} 准备写入提案，内容是 JSON 字符串 {content_json} 的解码值，不要执行。',
        '只生成已选文件的待审写入草稿，正文是 {content_json} 解码后的文本。',
        '为 {path} 拟定待确认写入操作，文本为解码后的 {content_json}。',
    ],
    'ambiguous': [
        'Inspect the relevant service configuration for its region.',
        'Read that configuration and check the deployment region.',
        'Check which region the service uses.',
        '请查看服务配置里的部署区域。',
        '读取那个配置文件，确认 region。',
        '帮我核实相关服务的区域设置。',
    ],
    'unsupported': [
        'Rewrite several services, migrate the database, and deploy everything now.',
        'Delete every workspace file and terminate all of its processes.',
        'Use an interactive terminal to finish a release across three repositories.',
        '立刻删除整个工作目录并关闭所有进程。',
        '现在完成跨项目重构、数据库迁移和线上发布。',
        '连接交互式终端处理三个仓库的完整发布流程。',
    ],
    'missing_tool': [
        'Read the complete content of {path}.',
        'Open the selected file and show all of its text.',
        'Retrieve the contents stored in {path}.',
        '请读取 {path} 的完整正文。',
        '把已选文件的所有文本读出来。',
        '查看 {path} 中的完整文件内容。',
    ],
    'invalid_range': [
        'Return only lines {start} through {end} from `{path}`.',
        'Extract the inclusive line interval {start} to {end} from the selected file.',
        'From {path}, obtain exactly lines {start} through {end}.',
        '请取出 {path} 的第 {start} 行到第 {end} 行，包含两端。',
        '已选文件中的第 {start} 至第 {end} 行是目标片段，请读取。',
        '查看 {path}，只返回第 {start} 至第 {end} 行。',
    ],
}


def task(kind, index):
    ident = f'independent-challenge-v2-{kind}-{index}'
    path = ['deploy notes/ledger.json', '配置/ledger active.json', 'infra/edge {blue}.json'][index % 3]
    folder = ['repo snapshots/api', '工程/候选目录', 'work items/needle-zone'][index % 3]
    marker = ['E_TAG=purple', 'retry-window?', '状态码=待机'][index % 3]
    start, end = [(2, 2), (61, 68), (402, 409), (711, 711), (27, 32), (119, 128)][index]
    if kind == 'invalid_range':
        start, end = [(0, 9), (68, 61), (409, 402), (711, 2), (32, 27), (0, 128)][index]
    content = ['enabled=false\n', 'note="post-v6 review"\nregion=north\n', '状态=待审核\n重试=4\n'][index % 3]
    url = 'http://127.0.0.1:19878/status'
    context = {
        'os': 'Windows',
        'shell': 'PowerShell',
        'workdir': '.',
        'tools': json.loads(json.dumps(TOOLS)),
        'resources': [
            {'service': 'archive', 'config': 'archive/previous.json'},
            {'service': 'ledger', 'config': path},
        ],
        'prior_results': {'selected_service': 'ledger', 'selected_file': path, 'selected_directory': folder},
    }
    if index % 2:
        context['resources'].reverse()
        context['tools'].reverse()
    fixture = {
        'files': {
            path: json.dumps({'region': 'north-v2', 'replicas': 4}),
            'archive/previous.json': json.dumps({'region': 'south-previous', 'replicas': 1}),
        },
        'git': False,
        'health': None,
    }
    call = {'tool': 'read_file', 'args': {'path': path}}
    expected = 'north-v2'
    if kind == 'config':
        context['prior_results']['selected_file'] = 'archive/previous.json'
        if index in (0, 3):
            context['prior_results']['selected_service'] = 'archive'
        if index in (2, 5):
            context = {'tools': context['tools'], 'resources': [], 'prior_results': {}}
    elif kind in ('lines', 'invalid_range'):
        lines = [f'v2-line-{i:04d}-{kind}-{index}' for i in range(1, 721)]
        fixture['files'][path] = '\n'.join(lines) + '\n'
        call['args'].update(start_line=start, end_line=end)
        expected = lines[start - 1:end] if kind == 'lines' else 'NEEDS_CLARIFICATION'
        if index in (0, 2, 3, 5):
            context['prior_results']['selected_file'] = 'archive/previous.json'
        if index == 5:
            context['prior_results']['unrelated_notes'] = 'An earlier unrelated note. ' * 90
    elif kind == 'search':
        fixture['files'] = {
            f'{folder}/alpha.txt': marker + '\n',
            f'{folder}/beta.txt': 'unrelated text\n',
            f'{folder}/gamma.txt': marker + ' twice\n',
        }
        call = {'tool': 'exec_command', 'args': {'cmd': f"rg -l --fixed-strings -- '{marker}' '{folder}'"}}
        expected = [f'{folder}/alpha.txt', f'{folder}/gamma.txt']
    elif kind == 'git_status':
        fixture.update(git=True, dirty=['changed-v2.txt', 'new-v2.txt'])
        call = {'tool': 'exec_command', 'args': {'cmd': 'git status --short'}}
        expected = ['changed-v2.txt', 'new-v2.txt']
    elif kind == 'git_log':
        fixture.update(git=True, subject=f'V2 independent subject {index}')
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
        if index in (0, 2, 3, 5):
            context['prior_results']['selected_file'] = 'archive/previous.json'
    if kind in ('ambiguous', 'missing_tool', 'unsupported', 'invalid_range'):
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
        'family_id': f'independent-challenge-v2-{family}-{index}',
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
    output = ROOT / 'data/pilots/independent-challenge-v2'
    output.mkdir(parents=True, exist_ok=False)
    rows = [task(kind, index) for kind in PROMPTS for index in range(6)]
    random.Random('independent-challenge-v2').shuffle(rows)
    path = output / 'evaluation.jsonl'
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    manifest = {
        'version': 'independent-challenge-v2',
        'splits': {'evaluation': {'tasks': len(rows), 'families': len({row['family_id'] for row in rows}),
                                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}},
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope': 'Fresh independent authored challenge. No training generator, model predictions, or V1 rows used.',
        'limitations': ['Small authored challenge does not establish production prevalence.',
                        'Tool schema and execution adapter are shared; fixture construction is independent.'],
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
