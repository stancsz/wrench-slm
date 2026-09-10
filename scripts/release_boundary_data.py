"""Broaden training-only abstention semantics and paired numeric boundaries."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release_context_data import clone  # noqa: E402
from wrench.pilot_tasks import public_record  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402


UNSUPPORTED = [
    'Install dependencies and start the application server.',
    'Perform a database upgrade, verify it, and deploy the backend.',
    'Move the code into a new repository and publish the project.',
    'Replace the application architecture with microservices.',
    'Stop the background worker and erase its persistent storage.',
    'Push every local change to the upstream repository.',
    'Apply the proposed edits to disk now, without review.',
    'Restart the operating system after installing updates.',
    'Investigate the bug, rewrite the module, and run all tests.',
    'Synchronize the repositories, resolve conflicts, and ship a release.',
    'Execute a shell script that modifies the production database.',
    'Create a new branch and commit all pending work.',
    'Launch an interactive editor to update the configuration.',
    'Remove the service from the cluster and delete its volumes.',
    'Fetch external packages and build an executable installer.',
    'Copy the repository to a remote machine and run the deployment.',
    '安装项目依赖，然后启动应用服务器。',
    '执行数据库升级，验证结果，再部署后端。',
    '把代码搬到新的仓库并公开发布项目。',
    '将应用的整体设计替换为微服务结构。',
    '停止后台工作进程并删除它的持久化存储。',
    '把全部本地改动推送到上游仓库。',
    '不用审核，立刻把建议的修改实际写到磁盘。',
    '安装操作系统更新，然后重启电脑。',
    '调查这个错误，重写相关模块，并运行所有测试。',
    '同步几个代码库，解决冲突，然后制作发行版。',
    '执行会修改生产数据库的命令脚本。',
    '新建一个分支并提交全部待处理改动。',
    '启动交互式编辑器来修改配置。',
    '从集群中移除这个服务，并删除它的数据卷。',
    '下载外部软件包，构建可执行安装程序。',
    '把仓库复制到远程主机，并在那里执行部署。',
]

RANGES = [
    'Return the inclusive line interval [{start}, {end}] from {path}.',
    'For {path}, use first line {start} and last line {end} in a read proposal.',
    'A file read is requested: {path}; lower bound {start}; upper bound {end}.',
    'Read {path}, beginning with line number {start} and ending with line number {end}.',
    'Propose reading the selected file over inclusive lines {start} to {end}.',
    'Give me the selected file segment with line bounds {start} and {end}, in that order.',
    '返回 {path} 中闭区间 [{start}, {end}] 对应的行。',
    '文件 {path} 的读取建议：首行编号 {start}，末行编号 {end}。',
    '请求读取 {path}，下界为 {start}，上界为 {end}，两端都包含。',
    '读取 {path} 中从行号 {start} 开始到行号 {end} 结束的部分。',
    '对已选文件拟定读取调用，行号区间是 {start} 到 {end}。',
    '请按顺序用 {start} 和 {end} 作为已选文件片段的两个行边界。',
]


def additions(rows):
    additions = []
    unsupported = [r for r in rows if r['kind'] == 'unsupported']
    lines = [r for r in rows if r['kind'] == 'lines']
    for style, prompt in enumerate(UNSUPPORTED):
        for index in range(24):
            row = clone(unsupported[(style * 24 + index) % len(unsupported)], f'boundary-v4-unsupported-{style}-{index}')
            row.update(prompt=prompt, family_id=f'boundary-v4-unsupported-style-{style}',
                       language='en' if style < 16 else 'zh', source='authored_training_scope_variation')
            additions.append(row)
    for style, prompt in enumerate(RANGES):
        for index in range(16):
            parent = lines[(style * 16 + index) % len(lines)]
            path = parent['args']['path']
            high = [4, 9, 15, 37, 96, 127, 183, 300][index % 8]
            low = 1 + index % 3
            for variant, (start, end) in enumerate([(low, high), (0, high), (high, low), (-low, high)]):
                row = clone(parent, f'boundary-v4-range-{style}-{index}-{variant}')
                row.update(prompt=prompt.format(path=path, start=start, end=end),
                           family_id=f'boundary-v4-range-style-{style}', language='en' if style < 6 else 'zh',
                           source='authored_training_boundary_contrast')
                content = [f'line {number}: fixture value' for number in range(1, 401)]
                row['fixture']['files'][path] = '\n'.join(content) + '\n'
                row['context']['prior_results']['selected_file'] = path
                if variant == 0:
                    row.update(tool='read_file', kind='lines', args={'path': path, 'start_line': start, 'end_line': end},
                               expected_answer=content[start - 1:end])
                else:
                    row.update(tool='fallback', kind='invalid_range', args={}, expected_answer='NEEDS_CLARIFICATION')
                additions.append(row)
    return additions


def main():
    source = ROOT / 'artifacts/archive/data/pilots/release-literal-v3'
    rows = [json.loads(line) for line in (source / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    combined = rows + additions(rows)
    random.Random('release-boundary-v4').shuffle(combined)
    seen, unique = {}, []
    for row in combined:
        key = canonical_json(public_record(row))
        label = canonical_json({'tool': row['tool'], 'args': row['args']})
        if key in seen and seen[key] != label:
            raise ValueError('Conflicting training labels')
        if key not in seen:
            unique.append(row)
            seen[key] = label
    output = ROOT / 'artifacts/archive/data/pilots/release-boundary-v4'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'train.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in unique), encoding='utf-8')
    for split in ['development', 'evaluation']:
        (output / f'{split}.jsonl').write_bytes((source / f'{split}.jsonl').read_bytes())
    manifest = {'version': 'release-boundary-v4', 'source': 'Authored training-only scope and boundary variations; no release or challenge cases imported.',
                'parent_train_sha256': hashlib.sha256((source / 'train.jsonl').read_bytes()).hexdigest(),
                'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'dropped_identical_duplicates': len(combined) - len(unique), 'label_conflicts': 0,
                'evaluation_unchanged': True, 'splits': {}}
    inputs, families = {}, {}
    for split in ['train', 'development', 'evaluation']:
        path = output / f'{split}.jsonl'
        records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        inputs[split] = {canonical_json(public_record(r)) for r in records}
        families[split] = {r['family_id'] for r in records}
        manifest['splits'][split] = {'tasks': len(records), 'families': len(families[split]),
                                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                     'kinds': dict(Counter(r['kind'] for r in records))}
    for a in inputs:
        for b in inputs:
            if a != b and (inputs[a] & inputs[b] or families[a] & families[b]):
                raise ValueError('Cross-split overlap')
    manifest.update(cross_split_families=0, cross_split_exact_inputs=0)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
