"""Authored, resettable developer tasks. Private fixtures never enter model inputs."""

import hashlib
import json
from pathlib import Path
import random


def tool(name, description, properties, required):
    return {'name': name, 'description': description, 'parameters': {
        'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False,
    }}


TOOLS = [
    tool('read_file', 'Read UTF-8 text in this workspace. Optional inclusive 1-based line range.', {
        'path': {'type': 'string'}, 'start_line': {'type': 'integer', 'minimum': 1},
        'end_line': {'type': 'integer', 'minimum': 1},
    }, ['path']),
    tool('exec_command', 'Run a read-only inspection command in the workspace. Supported: git status --short; git log -1 --format=%s; rg -l --fixed-strings -- PATTERN DIRECTORY; curl --silent --show-error --max-time 3 URL.', {
        'cmd': {'type': 'string'},
    }, ['cmd']),
    tool('write_file', 'Submit a proposed UTF-8 file write for review. Never executes a write in this pilot.', {
        'path': {'type': 'string'}, 'content': {'type': 'string'},
    }, ['path', 'content']),
]


# Template indices are assigned to partitions BEFORE instances are generated.
# Test-only wording must never be reused to improve a selected candidate.
TEMPLATES = {
    'config': [
        'What is the region in {path}?', 'Read {path} and tell me the region.',
        'For {service}, find its configured region.', 'Which region does the selected service use?',
        'Look up the region setting for {service}.', 'Report the region value stored in {path}.',
        'I need the deployment region for {service}; consult its configuration.',
        '帮我查一下 {service} 的配置，region 是什么？',
        'Use the configuration for the previously selected service and return its region.',
    ],
    'lines': [
        'Read lines {start} through {end} of {path}.', 'Show {path} from line {start} to line {end}.',
        'Give me the inclusive line range {start}-{end} in {path}.', 'Fetch lines {start}..{end} from the selected file.',
        'Extract the {start}-{end} line interval of {path}.', 'Return just lines {start} to {end} from {path}.',
        'The relevant excerpt is at lines {start} through {end} in the selected file. Retrieve it.',
        '请读取 {path} 的第 {start} 到第 {end} 行。',
        'Open {path} at line {start} and include everything up to line {end}.',
    ],
    'search': [
        'Find filenames containing the literal text {marker} under {folder}.',
        'Which files under {folder} contain {marker}?',
        'Search {folder} for {marker}; return matching filenames.',
        'Locate files containing {marker} in the selected directory.',
        'List the files in {folder} where the exact text {marker} occurs.',
        'Find occurrences of {marker} in {folder} and report the filenames.',
        'The identifier {marker} is referenced somewhere beneath {folder}. Which files reference it?',
        '在 {folder} 中找到包含字面文本 {marker} 的文件名。',
        'Look for the literal marker {marker} inside the previously selected directory and return paths.',
    ],
    'git_status': [
        'Which files are currently changed or untracked?', 'List the dirty files in this Git workspace.',
        'Check the working tree and return changed filenames.', 'Show the names of modified and untracked files.',
        'Find all files with pending working tree changes.', 'Give me the filenames that Git reports as dirty.',
        'Before I commit, which paths still have local changes or are untracked?',
        '当前 Git 工作区有哪些修改过或未跟踪的文件？',
        'Inspect this checkout and enumerate the paths that are not clean.',
    ],
    'git_log': [
        'What is the latest commit subject?', 'Read the most recent Git commit message subject.',
        'Tell me the title of the latest commit.', 'Get the subject line for HEAD.',
        'Which commit subject is at the tip of this checkout?', 'Report only the newest commit title.',
        'What was the last change called in this repository history?',
        '请查看当前仓库最近一次提交的标题。',
        'Inspect HEAD in the local history and return its subject line.',
    ],
    'health': [
        'Check {url} and report the service status.', 'Fetch the status from {url}.',
        'Is the selected service healthy? Return its status field.', 'Read the health endpoint for {service} and return status.',
        'Consult {url} for the current status value.', 'Query the known health URL and report status.',
        'The service is reachable at {url}. What status does its health response contain?',
        '请访问 {url} 并返回服务的 status 字段。',
        'Use the health address from the previous service selection to check its reported status.',
    ],
    'draft': [
        'Draft a write of {content} to {path}. Do not apply it.',
        'Prepare a file write for {path} containing {content}, for review only.',
        'Propose replacing {path} with exactly {content}.',
        'Create a draft to write {content} to the selected file; leave disk untouched.',
        'Submit a proposed write to {path} with content {content}.',
        'Prepare, without executing, a write of {content} into {path}.',
        'For review, supply a write proposal that puts exactly {content} in {path}.',
        '请为 {path} 拟定写入草稿，内容是 {content}，不要实际写入。',
        'The selected file should contain {content}. Produce the write draft for approval.',
    ],
    'ambiguous': [
        'Read the config and tell me its region.', 'What region is the service configured for?',
        'Look up the region for that service.', 'Use the configuration to find the region.',
        'Find the configured region; I have not chosen the service yet.', 'Check its region setting.',
        'Tell me the deployment region from the relevant configuration.',
        '帮我看看配置中的 region 是什么。',
        'Read the service configuration and report its region, please.',
    ],
}


def public_record(task):
    """Only this allowlisted view is passed to either model or rules."""
    return {'prompt': task['prompt'], 'context': task['context']}


def make_task(kind, template, instance, split):
    ident = f'{split}-{kind}-t{template}-{instance:03d}'
    digest = hashlib.sha256(ident.encode()).hexdigest()
    rng = random.Random(digest)
    service = 'svc-' + digest[:7]
    path = f'configs/{service}.json'
    folder = 'src/' + digest[7:13]
    marker = 'KEY_' + digest[13:21]
    start = rng.randint(2, 8)
    end = start + rng.randint(1, 3)
    content = 'enabled=' + digest[21:29]
    # Render a real bound port only when preparing the fixture. No answer in context.
    url = 'http://127.0.0.1:__PORT__/health'
    values = locals()
    prompt = TEMPLATES[kind][template].format(**values)
    context = {
        'os': 'Windows', 'shell': 'PowerShell', 'workdir': '.', 'tools': TOOLS,
        'resources': [{'service': service, 'config': path}, {'service': 'other-' + digest[:4], 'config': 'configs/other.json'}],
        'prior_results': {'selected_service': service, 'selected_file': path, 'selected_directory': folder, 'health_url': url},
    }
    if kind != 'health':
        context['prior_results'].pop('health_url')
    fixture = {'files': {}, 'git': False, 'health': None}
    region = 'region-' + digest[29:37]
    fixture['files'][path] = json.dumps({'service': service, 'region': region, 'replicas': rng.randint(1, 9)})
    fixture['files']['configs/other.json'] = json.dumps({'service': 'other-' + digest[:4], 'region': 'region-' + digest[37:45]})
    call = {'tool': 'read_file', 'args': {'path': path}}
    expected = region
    if kind == 'lines':
        lines = ['line-' + hashlib.sha256((ident + str(i)).encode()).hexdigest()[:12] for i in range(15)]
        fixture['files'][path] = '\n'.join(lines) + '\n'
        call['args'].update(start_line=start, end_line=end)
        expected = lines[start - 1:end]
    elif kind == 'search':
        for i in range(4):
            fixture['files'][f'{folder}/module_{i}.txt'] = ('reference ' + marker if i in (1, 3) else 'unrelated') + '\n'
        call = {'tool': 'exec_command', 'args': {'cmd': f'rg -l --fixed-strings -- {marker} {folder}'}}
        expected = [f'{folder}/module_1.txt', f'{folder}/module_3.txt']
    elif kind == 'git_status':
        fixture['git'] = True
        fixture['dirty'] = ['changed_' + digest[:6] + '.txt', 'new_' + digest[6:12] + '.txt']
        call = {'tool': 'exec_command', 'args': {'cmd': 'git status --short'}}
        expected = sorted(fixture['dirty'])
    elif kind == 'git_log':
        fixture['git'] = True
        fixture['subject'] = 'Update service ' + digest[:12]
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
    return {
        'id': ident, 'family_id': f'{kind}-template-{template}', 'seed_id': ident,
        'source': 'authored_resettable_developer_scenario', 'kind': kind,
        'language': 'zh' if template == 7 else 'en',
        'prompt': prompt, 'context': context, **call, 'fixture': fixture, 'expected_answer': expected,
    }


def build_dataset(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    specs = {'train': (range(4), 20), 'development': ([4], 10), 'calibration': ([5], 10), 'evaluation': (range(6, 9), 5)}
    sets = {}
    for split, (templates, count) in specs.items():
        tasks = [make_task(kind, template, i, split) for kind in TEMPLATES for template in templates for i in range(count)]
        random.Random('pilot-v1-' + split).shuffle(tasks)
        # Training health records use explicit varied valid-shaped ports, not unresolved placeholders.
        if split != 'evaluation':
            tasks = [json.loads(json.dumps(t).replace('__PORT__', str(18000 + i))) for i, t in enumerate(tasks)]
        sets[split] = tasks
        (destination / f'{split}.jsonl').write_text(''.join(json.dumps(t, ensure_ascii=False) + '\n' for t in tasks), encoding='utf-8')
    families = {s: {t['family_id'] for t in ts} for s, ts in sets.items()}
    for a in families:
        for b in families:
            if a != b and families[a] & families[b]:
                raise ValueError('Cross-split template family leakage')
    manifest = {
        'version': 'authored-developer-v1', 'source': 'authored, not recovered production requests',
        'splits': {s: {'tasks': len(ts), 'template_families': len(families[s]), 'sha256': hashlib.sha256((destination / f'{s}.jsonl').read_bytes()).hexdigest()} for s, ts in sets.items()},
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'cross_split_template_families': 0, 'cross_split_seed_ids': 0,
        'privacy': 'All file contents are generated; no private repository content is sent to teachers.',
        'inference_fields': ['prompt', 'context'], 'private_fields': ['fixture', 'expected_answer', 'tool', 'args', 'kind'],
        'limitations': ['Authored tasks do not establish production traffic coverage.', '120 evaluation scenarios share 24 wording families; uncertainty must cluster by family.', 'Actual execution target is Windows; no Linux or Pi claim.', 'Only bounded inspection, local health, draft-only writes and ambiguity are included.'],
    }
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest
