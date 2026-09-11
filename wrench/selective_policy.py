"""Public-context eligibility and bounded local completion for selective offload."""

import json
import re
import shlex
from dataclasses import asdict, dataclass

from .public_helper import rules_predict
from .protocol import ROUTER_FALLBACK

POLICY_VARIANTS = {
    'agreement': 1.00,
    'safe': 0.90,
    'eligible': 0.85,
}


@dataclass
class PolicyDecision:
    accepted: bool
    score: float
    threshold: float
    reason: str
    action: str
    helper_action: str
    revision: str

    def to_dict(self):
        return asdict(self)


def _record_tools(record):
    return record.get('context', {}).get('tools') or []


def _visible_paths(record):
    context = record.get('context', {})
    paths = {item.get('config') for item in context.get('resources', []) if isinstance(item, dict)}
    selected = context.get('prior_results', {}).get('selected_file')
    if selected:
        paths.add(selected)
    return {path for path in paths if isinstance(path, str)}


def _prompt_has(record, words):
    prompt = record.get('prompt', '').lower()
    return any(word.lower() in prompt for word in words)


def _intent_aligned(record, tool, args):
    """Require the public request to support the proposed operation."""
    if tool == 'read_file':
        if 'start_line' in args or 'end_line' in args:
            return _prompt_has(record, ['line', 'range', 'excerpt', '行', '区间', '摘录'])
        return _prompt_has(record, ['region', 'config', 'configuration', 'json', 'settings', '区域', '配置', '设置'])
    if tool == 'write_file':
        return _prompt_has(record, ['draft', 'write', 'change', 'proposal', 'review', '草稿', '写入', '变更', '提案', '审阅'])
    if tool == 'exec_command':
        command = args.get('cmd', '')
        if command == 'git status --short':
            return _prompt_has(record, ['status', 'dirty', 'changed', 'working tree', 'worktree', '状态', '修改', '工作区', '工作树', '未跟踪'])
        if command == 'git log -1 --format=%s':
            return _prompt_has(record, ['commit', 'head', 'history', 'subject', 'title', '提交', '历史', '标题'])
        if command.startswith('rg '):
            return _prompt_has(record, ['find', 'search', 'file', 'filename', 'literal', 'marker', 'occurrence', 'locate', '搜索', '文件', '标记', '路径'])
        if command.startswith('curl '):
            return _prompt_has(record, ['health', 'status', 'healthy', 'service', '状态', '健康', '服务'])
    return False


def _safe_command(record, command):
    context = record.get('context', {})
    try:
        argv = shlex.split(command)
    except ValueError:
        return False, 'command_parse'
    if argv == ['git', 'status', '--short']:
        return True, 'git_status_command'
    if argv == ['git', 'log', '-1', '--format=%s']:
        return True, 'git_log_command'
    if len(argv) == 6 and argv[:4] == ['rg', '-l', '--fixed-strings', '--']:
        marker = re.search(r'KEY_[a-f0-9]+', record.get('prompt', ''))
        folder = context.get('prior_results', {}).get('selected_directory')
        if marker and folder and argv[4] == marker.group(0) and argv[5] == folder:
            return True, 'literal_search_command'
        return False, 'search_context_mismatch'
    if len(argv) == 6 and argv[:5] == ['curl', '--silent', '--show-error', '--max-time', '3']:
        url = context.get('prior_results', {}).get('health_url')
        parsed = argv[5]
        if url and parsed == url and re.fullmatch(r'http://127\.0\.0\.1:\d+/health', parsed):
            return True, 'loopback_health_command'
        return False, 'health_context_mismatch'
    return False, 'command_outside_contract'


def validate_public_action(record, action, revision='v1'):
    """Return a safe eligibility score using only the public record."""
    if action == ROUTER_FALLBACK:
        return 0.0, 'model_abstention'
    try:
        parsed = json.loads(action)
    except (TypeError, ValueError):
        return 0.0, 'invalid_json'
    if not isinstance(parsed, dict) or not isinstance(parsed.get('tool'), str) or not isinstance(parsed.get('args'), dict):
        return 0.0, 'invalid_shape'
    tool = parsed['tool']
    visible_tools = {item.get('name') for item in _record_tools(record)}
    if tool not in visible_tools:
        return 0.0, 'tool_not_visible'
    args = parsed['args']
    paths = _visible_paths(record)
    if revision == 'intent-v2' and not _intent_aligned(record, tool, args):
        return 0.0, 'request_intent_mismatch'
    if tool == 'read_file':
        if args.get('path') not in paths:
            return 0.0, 'path_not_visible'
        if set(args) - {'path', 'start_line', 'end_line'}:
            return 0.0, 'unexpected_read_arguments'
        if ('start_line' in args) != ('end_line' in args):
            return 0.0, 'incomplete_line_range'
        if 'start_line' in args and (args['start_line'] < 1 or args['end_line'] < args['start_line']):
            return 0.0, 'invalid_line_range'
        return 0.9, 'visible_read_action'
    if tool == 'exec_command':
        if set(args) != {'cmd'} or not isinstance(args.get('cmd'), str):
            return 0.0, 'invalid_command_arguments'
        safe, reason = _safe_command(record, args['cmd'])
        return (0.9 if safe else 0.0), reason
    if tool == 'write_file':
        if set(args) != {'path', 'content'} or args.get('path') not in paths:
            return 0.0, 'draft_target_not_visible'
        if not isinstance(args.get('content'), str) or not args['content']:
            return 0.0, 'empty_draft'
        if args['content'] not in record.get('prompt', ''):
            return 0.0, 'draft_content_not_visible'
        return 0.9, 'review_only_draft'
    return 0.0, 'tool_not_allowed'


def decide(record, action, variant='agreement', revision='v1'):
    if variant not in POLICY_VARIANTS:
        raise ValueError(f'Unknown policy variant: {variant}')
    score, reason = validate_public_action(record, action, revision)
    helper_action = rules_predict(record)
    threshold = POLICY_VARIANTS[variant]
    if score <= 0:
        accepted = False
    elif variant == 'agreement':
        accepted = action == helper_action
    elif variant == 'safe':
        accepted = action == helper_action or score >= threshold
    else:
        accepted = score >= threshold
    if not accepted:
        reason = f'bypass_{reason}'
    return PolicyDecision(accepted, score, threshold, reason, action, helper_action, revision)


def format_local_answer(record, observation):
    """Format one bounded observation into a JSON answer using public intent."""
    if observation.get('error') or not observation.get('executed') and not observation.get('draft_only'):
        return None, 'observation_error'
    call = observation.get('call', {})
    tool = call.get('tool')
    output = observation.get('output', '')
    prompt = record.get('prompt', '').lower()
    if tool == 'write_file' and observation.get('draft_only'):
        return json.dumps({'answer': 'DRAFT_ONLY'}), 'draft_answer'
    if tool == 'read_file':
        if 'region' in prompt or '区域' in prompt:
            try:
                return json.dumps({'answer': json.loads(output)['region']}), 'json_region_answer'
            except (ValueError, KeyError, TypeError):
                return None, 'region_parse_error'
        return json.dumps({'answer': output.splitlines()}), 'line_answer'
    if tool == 'exec_command':
        command = call.get('args', {}).get('cmd', '')
        if command.startswith('rg '):
            paths = [line.replace('\\', '/') for line in output.splitlines() if line]
            return json.dumps({'answer': paths}), 'search_answer'
        if command == 'git status --short':
            paths = []
            for line in output.splitlines():
                if len(line) >= 3:
                    paths.append(line[3:].replace('\\', '/'))
            return json.dumps({'answer': sorted(paths)}), 'git_status_answer'
        if command == 'git log -1 --format=%s':
            return json.dumps({'answer': output.strip()}), 'git_log_answer'
        if command.startswith('curl '):
            try:
                return json.dumps({'answer': json.loads(output)['status']}), 'health_answer'
            except (ValueError, KeyError, TypeError):
                return None, 'health_parse_error'
    return None, 'no_local_formatter'
