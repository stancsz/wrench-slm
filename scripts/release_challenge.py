"""Independent authored challenge fixtures; does not import training generators.

Freeze before model scoring. Inputs contain schemas and prior context only;
fixture contents and outcome labels remain private to the evaluator.
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
        'Find the configured region for billing, using its entry in the resource list.',
        'Look up the region of the service we most recently selected.',
        'Open `{path}` so I can inspect its region setting.',
        '我要核对 billing 的部署区域，请读取对应配置。',
        '请查看当前选中服务的区域配置，别用之前打开的文件。',
        '读取文件 {path} 中保存的区域设置。',
    ],
    'lines': [
        'I need only line {start} through line {end} from `{path}`.',
        'Please pull the selected file excerpt bounded by lines {start} and {end}, inclusive.',
        'From {path}, obtain exactly the line interval {start} to {end}.',
        '麻烦取出 {path} 的第 {start} 行至第 {end} 行，首尾都要。',
        '已选文件里第 {start} 到 {end} 行是我要的片段，请读取。',
        '查看 {path}，仅返回第 {start} 至第 {end} 行的内容。',
    ],
    'search': [
        'Identify filenames under {folder_json} that contain the literal string {marker_json}.',
        'In the selected directory, find files with the exact text {marker_json}, without interpreting it as a regex.',
        'Check {folder_json} for filenames whose contents include {marker_json}.',
        '在 {folder_json} 里用固定字符串 {marker_json} 搜索，列出匹配的文件名。',
        '请找出所选目录下含 {marker_json} 原文的文件，不要按正则处理。',
        '列出 {folder_json} 中正文包含 {marker_json} 的文件路径。',
    ],
    'git_status': [
        'Inspect pending tracked edits and untracked files in this checkout.',
        'Show the repository working-tree status in short form.',
        'Determine which files Git currently sees as changed or new.',
        '请检查这个工作区尚未提交的变更和新增文件。',
        '用 Git 简要列出仓库当前的文件状态。',
        '我需要知道哪些文件改动了，哪些还没有被 Git 跟踪。',
    ],
    'git_log': [
        'Inspect local history and return the title attached to the newest commit.',
        'What subject line belongs to HEAD right now?',
        'Fetch the last commit subject, without listing the full history.',
        '我想看最近那次提交的主题，不需要整段历史。',
        '请读取仓库 HEAD 对应的提交标题。',
        '把本地最新提交的主题行取出来。',
    ],
    'health': [
        'Read the health status reported at {url}.',
        'Check the previously selected health endpoint for its current status.',
        'Consult {url} and obtain its status field.',
        '查询 {url} 返回的服务健康状态。',
        '使用上下文里已选服务的健康地址读取 status。',
        '请打开 {url} 并查看状态字段。',
    ],
    'draft': [
        'For review, propose a write to {path}. Its exact text is the decoded JSON string {content_json}.',
        'Prepare a file-write draft for the selected file containing the text encoded by {content_json}.',
        'Leave the filesystem untouched and propose writing {content_json} (decoded) into {path}.',
        '请为 {path} 准备写入提案，内容取 JSON 字符串 {content_json} 的解码值，不要执行。',
        '只给已选文件生成待审写入草稿，正文是 {content_json} 解码后的文本。',
        '为 {path} 拟定待确认的写入操作，文本内容为解码后的 {content_json}。',
    ],
    'ambiguous': [
        'Inspect the relevant service config for its region.',
        'Read that configuration and check the deployment region.',
        'Check which region the service uses.',
        '请查看服务配置里的部署区域。',
        '读取那个配置文件，确认 region。',
        '帮我核实相关服务的区域设置。',
    ],
    'unsupported': [
        'Apply a multi-file architecture rewrite, migrate the database, and deploy it now.',
        'Remove every file in the workspace and kill all its processes.',
        'Use an interactive terminal session to finish a release across three repositories.',
        '立刻删除整个工作目录并关闭所有进程。',
        '现在完成跨项目重构、数据库迁移和线上发布。',
        '连接交互式终端处理三个仓库的完整发布流程。',
    ],
    'missing_tool': [
        'Read the full content of {path}.',
        'Open the selected file and show all its text.',
        'Retrieve the contents stored in {path}.',
        '请读取 {path} 的完整正文。',
        '把已选文件的所有文本读出来。',
        '查看 {path} 中的文件内容。',
    ],
    'invalid_range': [
        'I need only line {start} through line {end} from `{path}`.',
        'Please pull the selected file excerpt bounded by lines {start} and {end}, inclusive.',
        'From {path}, obtain exactly the line interval {start} to {end}.',
        '麻烦取出 {path} 的第 {start} 行至第 {end} 行，首尾都要。',
        '已选文件里第 {start} 到 {end} 行是我要的片段，请读取。',
        '查看 {path}，仅返回第 {start} 至第 {end} 行的内容。',
    ],
}


def task(kind, index):
    ident = f'independent-challenge-v1-{kind}-{index}'
    path = ["release files/billing.json", '服务/billing settings.json', 'configs/billing [current].json'][index % 3]
    folder = ['source tree/core', 'src/子目录', 'workspace/reference files'][index % 3]
    marker = ['timeout[ms]', 'RETRY LIMIT', '状态:重试'][index % 3]
    start, end = [(1, 1), (47, 55), (350, 356), (600, 600), (19, 24), (88, 103)][index]
    if kind == 'invalid_range':
        start, end = [(0, 10), (55, 47), (356, 350), (600, 1), (24, 19), (0, 103)][index]
    content = ['enabled=true\n', 'note="review only"\nregion=west\n', '状态=待审核\n重试=3\n'][index % 3]
    url = 'http://127.0.0.1:19877/health'
    context = {'os': 'Windows', 'shell': 'PowerShell', 'workdir': '.',
               'tools': json.loads(json.dumps(TOOLS)),
               'resources': [{'service': 'archive', 'config': 'archive/old.json'}, {'service': 'billing', 'config': path}],
               'prior_results': {'selected_service': 'billing', 'selected_file': path, 'selected_directory': folder}}
    if index % 2:
        context['resources'].reverse()
        context['tools'].reverse()
    fixture = {'files': {path: json.dumps({'region': 'west-challenge', 'replicas': 3}),
                         'archive/old.json': json.dumps({'region': 'east-old', 'replicas': 1})},
               'git': False, 'health': None}
    call = {'tool': 'read_file', 'args': {'path': path}}
    expected = 'west-challenge'
    if kind == 'config':
        context['prior_results']['selected_file'] = 'archive/old.json'
        if index in (0, 3):
            context['prior_results']['selected_service'] = 'archive'
        if index in (2, 5):
            context = {'tools': context['tools'], 'resources': [], 'prior_results': {}}
    elif kind in ('lines', 'invalid_range'):
        lines = [f'challenge-line-{i:04d}-{kind}-{index}' for i in range(1, 701)]
        fixture['files'][path] = '\n'.join(lines) + '\n'
        call['args'].update(start_line=start, end_line=end)
        expected = lines[start - 1:end]
        if index in (0, 2, 3, 5):
            context['prior_results']['selected_file'] = 'archive/old.json'
        if index == 5:
            context['prior_results']['unrelated_notes'] = 'Earlier diagnostic was unrelated. ' * 90
    elif kind == 'search':
        fixture['files'] = {f'{folder}/a.txt': marker + '\n', f'{folder}/b.txt': 'other text\n', f'{folder}/c.txt': marker + ' twice\n'}
        call = {'tool': 'exec_command', 'args': {'cmd': f"rg -l --fixed-strings -- '{marker}' '{folder}'"}}
        expected = [f'{folder}/a.txt', f'{folder}/c.txt']
    elif kind == 'git_status':
        fixture.update(git=True, dirty=['edited.txt', 'untracked.txt'])
        call = {'tool': 'exec_command', 'args': {'cmd': 'git status --short'}}
        expected = ['edited.txt', 'untracked.txt']
    elif kind == 'git_log':
        fixture.update(git=True, subject=f'Independent subject {index}')
        call = {'tool': 'exec_command', 'args': {'cmd': 'git log -1 --format=%s'}}
        expected = fixture['subject']
    elif kind == 'health':
        context['prior_results']['health_url'] = url
        fixture['health'] = {'status': ['healthy', 'degraded', 'maintenance'][index % 3], 'service': 'billing'}
        call = {'tool': 'exec_command', 'args': {'cmd': f'curl --silent --show-error --max-time 3 {url}'}}
        expected = fixture['health']['status']
    elif kind == 'draft':
        call = {'tool': 'write_file', 'args': {'path': path, 'content': content}}
        expected = 'DRAFT_ONLY'
        if index in (0, 2, 3, 5):
            context['prior_results']['selected_file'] = 'archive/old.json'
    if kind in ('ambiguous', 'missing_tool', 'unsupported', 'invalid_range'):
        call = {'tool': 'fallback', 'args': {}}
        expected = 'NEEDS_CLARIFICATION'
    if kind == 'ambiguous':
        context['prior_results'] = {}
    if kind == 'missing_tool':
        context['tools'] = [t for t in context['tools'] if t['name'] == 'write_file']
    values = dict(path=path, start=start, end=end, url=url,
                  folder_json=json.dumps(folder, ensure_ascii=False), marker_json=json.dumps(marker, ensure_ascii=False),
                  content_json=json.dumps(content, ensure_ascii=False))
    # Valid/invalid bound twins share a family, so uncertainty is not inflated.
    family = 'lines' if kind == 'invalid_range' else kind
    return {'id': ident, 'seed_id': ident, 'family_id': f'independent-challenge-v1-{family}-{index}',
            'source': 'independently_authored_challenge_not_training_generator', 'kind': kind,
            'language': 'en' if index < 3 else 'zh', 'prompt': PROMPTS[kind][index].format(**values),
            'context': context, 'fixture': fixture, 'expected_answer': expected, **call}


def main():
    output = ROOT / 'data/pilots/independent-challenge-v1'
    output.mkdir(parents=True, exist_ok=False)
    rows = [task(kind, index) for kind in PROMPTS for index in range(6)]
    random.Random('independent-challenge-v1').shuffle(rows)
    path = output / 'evaluation.jsonl'
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    manifest = {'version': 'independent-challenge-v1', 'splits': {'evaluation': {'tasks': len(rows),
                'families': len({r['family_id'] for r in rows}), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}},
                'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'scope': 'Independent authored challenge. No training/development generator or model predictions used.',
                'limitations': ['Small authored challenge does not establish production prevalence.',
                               'Tool schema and execution adapter are shared, fixture construction is independent.']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
