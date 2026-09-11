"""Oracle-free runtime route for a bounded read-only local completion."""

import json
import time

from .selective_policy import decide


def validate_runtime_action(record, action):
    """Validate the single operation shape permitted by this runtime route."""
    del record
    try:
        parsed = json.loads(action)
    except (TypeError, ValueError):
        return None, 'runtime_action_invalid'
    if not isinstance(parsed, dict) or parsed.get('tool') != 'read_file':
        return None, 'runtime_action_unsupported'
    args = parsed.get('args')
    if not isinstance(args, dict) or set(args) - {'path', 'start_line', 'end_line'}:
        return None, 'runtime_read_arguments'
    if not isinstance(args.get('path'), str):
        return None, 'runtime_read_path'
    has_start = 'start_line' in args
    has_end = 'end_line' in args
    if has_start != has_end:
        return None, 'runtime_incomplete_range'
    if has_start and (
        not isinstance(args['start_line'], int)
        or not isinstance(args['end_line'], int)
        or args['start_line'] < 1
        or args['end_line'] < args['start_line']
    ):
        return None, 'runtime_invalid_range'
    return parsed, 'runtime_read_action'


def verify_runtime_observation(record, action, observation):
    """Verify one public read observation without private task data.

    The verifier establishes operation shape and execution integrity. It does
    not compare the output with an evaluator answer or inspect the environment
    task object.
    """
    if not isinstance(observation, dict):
        return None, 'verifier_observation_shape'
    if observation.get('error'):
        return None, 'verifier_observation_error'
    if not observation.get('executed'):
        return None, 'verifier_not_executed'
    if observation.get('truncated'):
        return None, 'verifier_truncated_observation'
    if observation.get('filesystem_unchanged') is False:
        return None, 'verifier_boundary_changed'
    parsed, action_reason = validate_runtime_action(record, action)
    if parsed is None:
        return None, f'verifier_{action_reason}'
    if observation.get('call') != parsed:
        return None, 'verifier_call_mismatch'
    args = parsed['args']
    output = observation.get('output')
    if not isinstance(output, str) or len(output) > 8192:
        return None, 'verifier_output_shape'
    prompt = record.get('prompt', '').lower()
    if 'start_line' in args and 'end_line' in args:
        if not any(word in prompt for word in ['line', 'range', 'excerpt', '行', '区间', '摘录']):
            return None, 'verifier_request_shape_mismatch'
        return json.dumps({'answer': output.splitlines()}), 'verifier_line_range'
    if any(word in prompt for word in ['region', 'config', 'configuration', 'json', 'settings', '区域', '配置', '设置']):
        try:
            document = json.loads(output)
        except (TypeError, ValueError):
            return None, 'verifier_json_parse'
        if not isinstance(document, dict) or not isinstance(document.get('region'), str):
            return None, 'verifier_region_field_missing'
        return json.dumps({'answer': document['region']}), 'verifier_region_field'
    return None, 'verifier_request_shape_unsupported'


def run_local_completion(env, record, action, variant, revision='v1', bypass=False):
    """Attempt one verified local completion and return a route receipt.

    This function deliberately knows nothing about private evaluator labels or
    answers. Offline scoring occurs only after this route has been fixed.
    """
    started = time.perf_counter()
    result = {
        'route': 'fallback',
        'local_attempted': False,
        'local_accepted': False,
        'local_success': False,
        'local_answer': None,
        'tools': [],
        'fallback_reason': None,
        'policy': None,
        'policy_duration_s': 0.0,
        'execution_duration_s': 0.0,
        'format_duration_s': 0.0,
    }
    if bypass:
        result['fallback_reason'] = 'bypass_operator_switch'
        result['duration_s'] = time.perf_counter() - started
        return result

    policy_started = time.perf_counter()
    decision = decide(record, action, variant, revision)
    result['policy_duration_s'] = time.perf_counter() - policy_started
    result['policy'] = decision.to_dict()
    if not decision.accepted:
        result['fallback_reason'] = decision.reason
        result['duration_s'] = time.perf_counter() - started
        return result

    result['local_attempted'] = True
    result['local_accepted'] = True
    parsed_action, action_reason = validate_runtime_action(record, action)
    if parsed_action is None:
        result['local_attempted'] = False
        result['fallback_reason'] = action_reason
        result['duration_s'] = time.perf_counter() - started
        return result
    execution_started = time.perf_counter()
    try:
        observation = env.execute(parsed_action)
    except TimeoutError as exc:
        result['fallback_reason'] = 'local_timeout'
        result['tools'].append({'executed': False, 'error': str(exc), 'output': json.dumps({'error': str(exc)})})
    except Exception as exc:  # noqa: BLE001
        result['fallback_reason'] = 'local_tool_error'
        result['tools'].append({'executed': False, 'error': str(exc), 'output': json.dumps({'error': str(exc)})})
    else:
        result['execution_duration_s'] = time.perf_counter() - execution_started
        observation.setdefault('speculative', False)
        result['tools'].append(observation)
        if observation.get('error'):
            result['fallback_reason'] = 'local_tool_error'
        else:
            format_started = time.perf_counter()
            answer, format_reason = verify_runtime_observation(record, action, observation)
            result['format_duration_s'] = time.perf_counter() - format_started
            result['local_answer'] = answer
            result['format_reason'] = format_reason
            unchanged = env.fingerprint() == env.initial_fingerprint
            result['runtime_verifier_passed'] = bool(answer and unchanged)
            if result['runtime_verifier_passed']:
                result['local_success'] = True
                result['route'] = 'local'
            else:
                result['fallback_reason'] = 'runtime_verifier_failed'

    result['filesystem_unchanged'] = env.fingerprint() == env.initial_fingerprint
    if not result['filesystem_unchanged']:
        result['fallback_reason'] = 'unexpected_mutation'
        result['route'] = 'fallback'
        result['local_success'] = False
    result['duration_s'] = time.perf_counter() - started
    return result
