"""Evaluation helpers for selective local completion receipts."""

import json
import time
from pathlib import Path

from .pilot_environment import PilotEnvironment, score_answer
from .protocol import ROUTER_FALLBACK
from .selective_runtime import run_local_completion


def load_tasks(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def evaluate_local_task(task, root, predictor, variant, revision='v1', bypass=False):
    started = time.perf_counter()
    env = PilotEnvironment(task, root)
    try:
        record = {'prompt': env.task['prompt'], 'context': env.task['context']}
        if bypass:
            prediction = {'action': ROUTER_FALLBACK, 'raw': ROUTER_FALLBACK,
                          'invalid_output': False, 'duration_s': 0.0}
        else:
            prediction = predictor(record)
        prediction_dict = prediction.to_dict() if hasattr(prediction, 'to_dict') else prediction
        action = prediction_dict['action']
        route = run_local_completion(env, record, action, variant, revision, bypass=bypass)
        row = {
            'task_id': task['id'], 'family_id': task['family_id'], 'kind': task['kind'],
            'language': task['language'], 'variant': variant, 'revision': revision,
            'prediction': prediction_dict, 'policy': route['policy'],
            'local_attempted': route['local_attempted'],
            'local_proposal_accepted': route['local_accepted'],
            'local_accepted': route['route'] == 'local',
            'local_success': route['local_success'],
            'local_answer': route['local_answer'], 'tools': route['tools'],
            'fallback_reason': route['fallback_reason'],
            'route': route['route'], 'local_duration_s': route['duration_s'],
            'runtime_verifier_passed': bool(route.get('runtime_verifier_passed')),
            'offline_correct': False,
        }
        if 'format_reason' in route:
            row['format_reason'] = route['format_reason']
        row['filesystem_unchanged'] = env.fingerprint() == env.initial_fingerprint
        row['duration_s'] = time.perf_counter() - started
        if not row['filesystem_unchanged']:
            row['fallback_reason'] = 'unexpected_mutation'
            row['route'] = 'fallback'
            row['local_success'] = False
        if row['route'] == 'local' and row['filesystem_unchanged']:
            row['offline_correct'] = bool(score_answer(env.task, row['local_answer'], row['tools']))
            row['local_success'] = row['offline_correct']
        else:
            row['local_success'] = False
        return row
    finally:
        env.close()


def _percentile(values, percentile):
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * percentile / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def _counts(values):
    output = {}
    for value in values:
        output[str(value)] = output.get(str(value), 0) + 1
    return output


def _summarize_core(rows):
    total = len(rows)
    accepted = [row for row in rows if row['local_accepted']]
    proposals = [row for row in rows if row.get('local_proposal_accepted')]
    successful = [row for row in rows if row['local_success']]
    wrong_accepted = [row for row in accepted if not row['local_success']]
    return {
        'tasks': total,
        'families': len({row['family_id'] for row in rows}),
        'accepted': len(accepted),
        'attempt_rate': len(accepted) / total if total else 0.0,
        'proposal_accepted': len(proposals),
        'proposal_acceptance_rate': len(proposals) / total if total else 0.0,
        'successful_local_completions': len(successful),
        'correct_local_completions_all_requests': len(successful) / total if total else 0.0,
        'accepted_precision': len(successful) / len(accepted) if accepted else None,
        'accepted_error_rate': len(wrong_accepted) / len(accepted) if accepted else 0.0,
        'unnecessary_fallbacks': sum(row['fallback_reason'] == 'local_outcome_failed' for row in rows),
        'unexpected_mutations': sum(not row['filesystem_unchanged'] for row in rows),
        'local_duration_s_p50': _percentile([row['duration_s'] for row in rows], 50),
        'local_duration_s_p95': _percentile([row['duration_s'] for row in rows], 95),
        'reason_breakdown': _counts([row['policy']['reason'] if row['local_accepted'] else row['fallback_reason'] for row in rows]),
    }


def summarize(rows):
    output = _summarize_core(rows)
    output['by_kind'] = {value: _summarize_core([row for row in rows if row['kind'] == value]) for value in sorted({row['kind'] for row in rows})}
    output['by_language'] = {value: _summarize_core([row for row in rows if row['language'] == value]) for value in sorted({row['language'] for row in rows})}
    return output
