"""Add a bounded contrast set after the V6 held-out semantic failures."""

from collections import Counter
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


TEMPLATES = {
    'config': [
        'This is a configuration-file inspection task, not a repository status task. Use read_file on {path} and preserve that path.',
        'The requested region is a value inside the selected config file. Read {path}; do not substitute Git status.',
        '这是配置文件读取任务，不是 Git 状态查询。请用 read_file 读取 {path}，保留该路径。',
        'region 在所选配置文件中。请读取 {path}，不要把请求改成工作区状态检查。',
    ],
    'git_status': [
        'This is a repository working-tree task, not a file-content task. Use exec_command with exactly git status --short.',
        'Inspect changed and untracked files with the Git status command; do not read the selected config file.',
        '这是仓库工作树状态任务，不是文件读取。请用 exec_command 执行 git status --short。',
        '请检查 Git 工作区的修改和未跟踪文件，不要用 read_file 代替 git status --short。',
    ],
    'git_log': [
        'This asks for the newest commit subject, not a file or search result. Use exec_command with git log -1 --format=%s.',
        'Read the local HEAD subject with the Git log command; do not substitute a file read or literal search.',
        '这是读取最新提交主题的任务，请用 exec_command 执行 git log -1 --format=%s。',
        '请从本地 Git 历史读取 HEAD 的主题，不要读取配置文件或执行搜索。',
    ],
    'search': [
        'This is a literal content search. Use exec_command with the fixed-string search for {marker} under {folder}.',
        'Find matching filenames with the exact text {marker}; do not read one file or run Git status.',
        '这是固定字符串搜索任务，请在 {folder} 下用 exec_command 查找原文 {marker}。',
        '请按字面字符串 {marker} 搜索 {folder} 中的文件，不要改成文件读取或 Git 查询。',
    ],
    'draft': [
        'Prepare a review-only write_file proposal for {path}. Preserve the decoded body, including its final newline: {content}.',
        'Draft the write for {path} exactly as decoded from {content}; keep every character and do not execute it.',
        '请为 {path} 生成待审核 write_file 草稿，完整保留解码正文及末尾换行：{content}，不要执行。',
        '只拟定写入提案，目标是 {path}，正文 {content} 必须逐字符保留，包括最后的换行。',
    ],
    'invalid_range': [
        'The requested line bounds are invalid. Return the fallback instead of emitting a read_file call for {path}.',
        'Do not repair or execute this invalid range for {path}; explicitly abstain with the fallback.',
        '请求的行范围无效。请对 {path} 返回 fallback，不要生成 read_file 调用。',
        '不要修正无效边界，也不要读取 {path}；此请求必须使用 fallback。',
    ],
    'missing_tool': [
        'The context does not provide a file-reading tool. Return the fallback for {path} rather than inventing a tool.',
        'Only the listed tools are available, so abstain explicitly instead of calling read_file for {path}.',
        '上下文没有文件读取工具。请对 {path} 明确返回 fallback，不要虚构 read_file。',
        '只能使用当前列出的工具，不能读取 {path}；请返回 fallback。',
    ],
    'lines': [
        'This is a file line-range read. Use read_file on {path} with the inclusive bounds {start} and {end}.',
        'Return only the requested inclusive lines from {path}; preserve both numeric arguments exactly.',
        '这是文件行范围读取任务，请用 read_file 读取 {path} 的第 {start} 到第 {end} 行。',
        '请只读取 {path} 中包含首尾的第 {start} 至第 {end} 行，不要改变参数。',
    ],
}


def command_values(row):
    command = row.get('args', {}).get('cmd', '')
    marker = 'the requested literal'
    folder = 'the selected directory'
    if "-- '" in command and "' '" in command:
        marker = command.split("-- '", 1)[1].split("' '", 1)[0]
        folder = command.rsplit("'", 2)[-2]
    return marker, folder


def clone_with_prompt(kind, template, instance):
    language = 'en' if template < 2 else 'zh'
    row = make_release_task(kind, 0 if language == 'en' else 2, template * 96 + instance,
                            'train', 'generalization-v7')
    row['id'] = f'generalization-v7-{kind}-{language}-{template}-{instance}'
    row['seed_id'] = row['id']
    row['family_id'] = f'generalization-v7-{kind}-{language}-contrast-{template}'
    row['source'] = 'fresh_authored_contrast_training'
    path = row.get('args', {}).get('path') or row.get('context', {}).get('prior_results', {}).get('selected_file',
                                                                                              'the selected file')
    start = row.get('args', {}).get('start_line', 1)
    end = row.get('args', {}).get('end_line', 2)
    marker, folder = command_values(row)
    content = row.get('args', {}).get('content', '')
    if kind == 'draft':
        bodies = [
            'review=false\nowner=v7\n',
            '区域=北方\n状态=待审\n',
            'note="keep-final-newline"\n',
        ]
        content = bodies[instance % len(bodies)]
        row['args']['content'] = content
    if kind == 'invalid_range':
        start, end = 0, 17
    values = {'path': path, 'start': start, 'end': end, 'marker': marker, 'folder': folder,
              'content': json.dumps(content, ensure_ascii=False)}
    row['prompt'] = TEMPLATES[kind][template].format(**values)
    return row


def main():
    source = ROOT / 'artifacts/archive/data/pilots/release-generalization-v6'
    parent_rows = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    additions = [clone_with_prompt(kind, template, instance)
                 for kind in TEMPLATES
                 for template in range(4)
                 for instance in range(96)]
    combined = parent_rows + additions
    random.Random('release-generalization-v7').shuffle(combined)
    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError(f'Conflicting labels for {row["id"]}')
        if key not in seen:
            seen[key] = label
            unique.append(row)
    output = ROOT / 'artifacts/archive/data/pilots/release-generalization-v7'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in unique),
                                        encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {
        'version': 'release-generalization-v7',
        'source': 'Fresh contrast wording after V6 held-out failures; no scored rows imported.',
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
