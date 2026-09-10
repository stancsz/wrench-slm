"""Versioned authored training tasks, with wording families split before generation.

These fixtures are authored data, not recovered production requests. The frozen
pilot evaluation is never imported into this dataset or training.
"""

import hashlib
import json
from pathlib import Path
import random

from .pilot_tasks import make_task, public_record
from .protocol import canonical_json


# Four training families, two development families, two untouched test families.
# Each partition includes English and Chinese. No test wording is used in training.
WORDING = {
    'config': [
        'Read the configuration file {path} to find its region.',
        'For the service selected earlier, retrieve its configuration.',
        '读取 {path}，我要查看 region 配置。',
        '查询之前选中的服务配置里的 region。',
        'Consult the config associated with {service} and check the region.',
        '刚才选中的服务部署在哪个 region？请读取配置确认。',
        'The selected service needs a region check. Open the relevant configuration.',
        '请从 {path} 取出部署区域的设置。',
    ],
    'lines': [
        'Read {path}, inclusive lines {start} through {end}.',
        'In the selected file, retrieve line {start} through line {end}, inclusive.',
        '请读取 {path} 第 {start} 到 {end} 行，包括两端。',
        '打开已选文件，提取第 {start} 至第 {end} 行。',
        'Fetch the portion of {path} beginning at {start} and ending at {end}.',
        '我只需要所选文件的第 {start} 到 {end} 行内容。',
        'Display an excerpt from {path}: first line {start}, last line {end}.',
        '截取 {path} 中从第 {start} 行开始、到第 {end} 行结束的片段。',
    ],
    'search': [
        'Find filenames containing the literal string {marker_json} in {folder_json}.',
        'Look under the selected directory for files containing literal {marker_json}.',
        '请在 {folder_json} 中查找包含字面字符串 {marker_json} 的文件名。',
        '在之前选中的目录内搜索字面文本 {marker_json}，返回文件名。',
        'Which files below {folder_json} include the exact string {marker_json}?',
        '列出 {folder_json} 下含有原样文本 {marker_json} 的文件。',
        'Identify files referencing {marker_json}, treating it as plain text, beneath {folder_json}.',
        '用固定字符串 {marker_json} 检索所选目录，告诉我匹配的文件路径。',
    ],
    'git_status': [
        'Inspect the working tree for changed and untracked files.',
        'Give me a short Git status for this checkout.',
        '查看当前工作树有哪些修改和未跟踪文件。',
        '用简短格式查看 Git 工作区状态。',
        'Check whether the local checkout has pending file changes.',
        '这个仓库现在有哪些尚未提交的文件变动？',
        'Inspect this repository for files that differ from the index or are untracked.',
        '列一下工作区里待处理的已修改文件和新文件。',
    ],
    'git_log': [
        'Read the subject of the latest Git commit.',
        'Find the title of HEAD in this repository.',
        '读取最近一次 Git 提交的标题。',
        '查询本仓库 HEAD 的提交主题。',
        'Retrieve the most recent commit subject from local history.',
        '当前分支末尾那个提交的标题是什么？',
        'What is the subject recorded for the tip commit?',
        '请从本地提交历史中取出最新提交的主题行。',
    ],
    'health': [
        'Read the service status from {url}.',
        'Use the selected service health URL to check status.',
        '访问 {url}，读取服务状态。',
        '读取之前选定的健康检查地址，查看 status。',
        'Consult {url} and retrieve its reported status.',
        '根据上下文里的健康检查地址确认服务状态。',
        'Check the status field exposed by the previously selected health endpoint.',
        '请读取 {url} 的健康检查结果中的 status 值。',
    ],
    'draft': [
        'Prepare a write draft for {path} with this JSON-encoded text: {content_json}. Do not execute it.',
        'Draft replacing the selected file with the decoded string {content_json}, for review.',
        '为 {path} 拟定写入草稿，内容是 JSON 字符串 {content_json} 解码后的文本，不要执行。',
        '给所选文件准备写入提案，正文为解码后的 {content_json}，等待审核。',
        'Propose writing the text represented by {content_json} into {path}; leave disk unchanged.',
        '仅生成 {path} 的写入草稿，写入内容为 JSON 字符串 {content_json} 对应的文字。',
        'Create a reviewable file-write proposal: destination {path}, decoded content {content_json}.',
        '请准备一个等待审批的文件写入建议：{path}，内容取自 {content_json} 的解码结果。',
    ],
    'ambiguous': [
        'Read the region configuration; I have not selected which service.',
        'Open the config for that service and find region.',
        '我还没选服务，请读取配置中的 region。',
        '查一下那个服务的 region 配置。',
        'Retrieve the region from the appropriate service config.',
        '帮我读取服务配置，看看它的部署区域。',
        'Check the region setting, using whichever service configuration is relevant.',
        '请查询相关配置的 region 字段，现在还没有确定具体服务。',
    ],
    'unsupported': [
        'Delete all files in the repository immediately.',
        'Refactor the entire application and deploy the result.',
        '立即删除仓库中的所有文件。',
        '重构整个应用并部署上线。',
        'Terminate every running process on this machine.',
        '帮我完成跨仓库架构迁移并发布新版本。',
        'Rewrite the system architecture, run a migration, and push to production.',
        '关闭所有服务并且彻底清空工作目录。',
    ],
    'missing_tool': [
        'Read the complete text of {path}.',
        'Open the selected file and return its contents.',
        '读取 {path} 的全部内容。',
        '打开所选文件并返回正文。',
        'Retrieve all text from {path}.',
        '请查看此前选中文件的完整内容。',
        'Display everything stored in the selected file.',
        '把 {path} 中保存的文本读出来。',
    ],
    'invalid_range': [
        'Read {path} from line {start} to line {end}, without correcting these bounds.',
        'Retrieve the inclusive interval {start}-{end} from the selected file.',
        '读取 {path} 的第 {start} 到 {end} 行，不要修改范围。',
        '提取所选文件的第 {start} 至第 {end} 行。',
        'Fetch the selected file starting at {start} and stopping at {end}.',
        '请按照起点 {start}、终点 {end} 读取 {path}。',
        'Use the requested line bounds exactly: {start} through {end} of {path}.',
        '请从所选文件的第 {start} 行读到第 {end} 行，按所给边界处理。',
    ],
}


def make_release_task(kind, template, instance, split, version):
    ident = f'{version}-{split}-{kind}-{template}-{instance}'
    digest = hashlib.sha256(ident.encode()).hexdigest()
    rng = random.Random(digest)
    original_kind = kind if kind in {'config', 'lines', 'search', 'git_status', 'git_log', 'health', 'draft', 'ambiguous'} else 'config'
    task = make_task(original_kind, 0, instance, ident)
    old_path = task['context']['resources'][0]['config']
    service = task['context']['resources'][0]['service']
    path = rng.choice(['configs', 'project files', '配置', "developer's notes"]) + '/' + digest[:10] + '.txt'
    folder = 'src/' + rng.choice(['modules', 'shared files', '组件']) + '-' + digest[10:16]
    marker = rng.choice(['KEY_', 'find me ', 'TAG[', '状态_']) + digest[16:24]
    content = rng.choice(['enabled=', 'message=hello\nregion=', '状态=启用\n标记=', "name='test'\nkey="]) + digest[24:32]
    old_folder = task['context']['prior_results'].get('selected_directory', '')
    replacements = {old_path: path}
    if old_folder:
        replacements[old_folder] = folder

    def replace(value):
        if isinstance(value, str):
            for old, new in replacements.items():
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, dict):
            return {replace(k): replace(v) for k, v in value.items()}
        return value

    task = replace(task)
    start = rng.randint(1, 180)
    end = start + rng.randint(0, 15)
    url = 'http://127.0.0.1:__PORT__/health'
    if kind in {'lines', 'invalid_range'}:
        lines = [f'entry {i}: {hashlib.sha256((ident + str(i)).encode()).hexdigest()[:12]}' for i in range(1, 220)]
        task['fixture']['files'][path] = '\n'.join(lines) + '\n'
        if kind == 'invalid_range':
            start, end = (0, end) if instance % 2 else (end + 5, start)
        else:
            task.update(tool='read_file', args={'path': path, 'start_line': start, 'end_line': end}, expected_answer=lines[start - 1:end])
    if kind == 'search':
        task['fixture']['files'] = {f'{folder}/module_{i}.txt': (marker if i in (1, 3) else 'unrelated') + '\n' for i in range(4)}
        task['args'] = {'cmd': f"rg -l --fixed-strings -- '{marker}' '{folder}'"}
        task['expected_answer'] = [f'{folder}/module_1.txt', f'{folder}/module_3.txt']
    if kind == 'draft':
        task['args'] = {'path': path, 'content': content}
    if kind in {'unsupported', 'missing_tool', 'invalid_range'}:
        task.update(tool='fallback', args={}, expected_answer='NEEDS_CLARIFICATION')
    if kind == 'missing_tool':
        task['context']['tools'] = [t for t in task['context']['tools'] if t['name'] == 'write_file']
    values = dict(path=path, service=service, start=start, end=end, url=url,
                  marker_json=json.dumps(marker, ensure_ascii=False), folder_json=json.dumps(folder, ensure_ascii=False),
                  content_json=json.dumps(content, ensure_ascii=False))
    task.update(id=ident, family_id=f'{version}-{kind}-wording-{template}', seed_id=ident,
                kind=kind, language='zh' if template in (2, 3, 5, 7) else 'en',
                prompt=WORDING[kind][template].format(**values), source='authored_release_scenario')
    return task


def build_release_data(destination, *, version='release-authoring-v1'):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    sets = {}
    for split, templates, count in [('train', range(4), 32), ('development', range(4, 6), 8), ('evaluation', range(6, 8), 20)]:
        rows = [make_release_task(k, t, i, split, version) for k in WORDING for t in templates for i in range(count)]
        # Training and static prediction checks use varied concrete local URLs.
        # The real execution harness substitutes an actual bound port before inference.
        rows = [json.loads(json.dumps(row).replace('__PORT__', str(19000 + i))) for i, row in enumerate(rows)]
        random.Random(version + split).shuffle(rows)
        sets[split] = rows
    families = {split: {row['family_id'] for row in rows} for split, rows in sets.items()}
    inputs = {split: {canonical_json(public_record(row)) for row in rows} for split, rows in sets.items()}
    for a in sets:
        for b in sets:
            if a != b and (families[a] & families[b] or inputs[a] & inputs[b]):
                raise ValueError('Cross-partition family or input overlap')
    manifest = {'version': version, 'source': 'New authored data; no private logs or pilot evaluation records.',
                'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'fixture_generator_sha256': hashlib.sha256(Path(__file__).with_name('pilot_tasks.py').read_bytes()).hexdigest(),
                'cross_split_families': 0, 'cross_split_exact_inputs': 0,
                'limitations': ['Authored task families do not measure production distribution.',
                               'Shared fixture construction is not independent evidence of label correctness; validate using OS outcomes.',
                               'Windows fixture execution only; no Linux/Pi or router savings claim.'], 'splits': {}}
    for split, rows in sets.items():
        path = destination / f'{split}.jsonl'
        path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
        manifest['splits'][split] = {'tasks': len(rows), 'families': len(families[split]),
                                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest
