"""Model-only scoring with independent OS outcome checks and explicit failures."""

from collections import defaultdict
import json
import math
import random

from .protocol import ROUTER_FALLBACK


def outcome_matches(task, action, receipt):
    if task['tool'] == 'fallback':
        return action == ROUTER_FALLBACK and receipt is None
    if receipt is None or receipt.get('error') or not receipt.get('filesystem_unchanged') or receipt.get('truncated'):
        return False
    if task['kind'] == 'draft':
        return bool(receipt.get('draft_only') and receipt['call']['args'] == task['args'] and not receipt['executed'])
    if not receipt.get('executed'):
        return False
    output, expected = receipt['output'], task['expected_answer']
    try:
        if task['kind'] == 'config':
            return json.loads(output)['region'] == expected
        if task['kind'] == 'lines':
            return output.splitlines() == expected
        if task['kind'] == 'search':
            return sorted(output.replace('\\', '/').splitlines()) == sorted(expected)
        if task['kind'] == 'git_status':
            return sorted(line[3:] for line in output.splitlines()) == sorted(expected)
        if task['kind'] == 'git_log':
            return output.rstrip('\r\n') == expected
        if task['kind'] == 'health':
            return json.loads(output)['status'] == expected
    except (KeyError, ValueError, TypeError):
        return False
    return False


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    width = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - width), min(1, center + width)]


def summarize(rows):
    if not rows:
        raise ValueError('Cannot summarize an empty evaluation')
    n = len(rows)
    routine = [row for row in rows if not row['expected_fallback']]
    fallback = [row for row in rows if row['expected_fallback']]
    exact = sum(row['exact'] for row in rows)
    families = defaultdict(list)
    for row in rows:
        families[row['family_id']].append(row)
    means = [sum(r['exact'] for r in family) / len(family) for family in families.values()]
    rng = random.Random(20260909)
    boot = sorted(sum(rng.choice(means) for _ in means) / len(means) for _ in range(2000))
    timings = sorted(row['duration_s'] for row in rows)

    def fraction(subset, key):
        return sum(row[key] for row in subset) / len(subset) if subset else None

    return {
        'tasks': n, 'families': len(families), 'exact': exact, 'exact_rate': exact / n,
        'exact_wilson95_descriptive_only': wilson(exact, n),
        'exact_family_bootstrap95': [boot[49], boot[1949]],
        'raw_protocol_valid_rate': sum(not r['invalid_output'] and r['reason'] != 'input_budget' for r in rows) / n,
        'routine_tasks': len(routine), 'routine_exact_rate': fraction(routine, 'exact'),
        'routine_accepted_call_rate': sum(r['action'] != ROUTER_FALLBACK for r in routine) / len(routine) if routine else None,
        'fallback_tasks': len(fallback), 'fallback_exact_rate': fraction(fallback, 'exact'),
        'execution_checked': all(row.get('execution_checked', False) for row in rows),
        'routine_outcome_rate': fraction(routine, 'outcome_correct') if all(r.get('execution_checked') for r in rows) else None,
        'filesystem_changes': sum(bool(r.get('execution') and not r['execution']['filesystem_unchanged']) for r in rows),
        'prediction_latency_s': {name: timings[min(n - 1, math.ceil(n * percentile) - 1)] for name, percentile in [('p50', .5), ('p95', .95), ('p99', .99)]},
        'by_kind': {kind: {'tasks': len(group), 'exact': sum(r['exact'] for r in group), 'invalid': sum(r['invalid_output'] for r in group)}
                    for kind in sorted({r['kind'] for r in rows}) if (group := [r for r in rows if r['kind'] == kind])},
        'by_language': {lang: {'tasks': len(group), 'exact': sum(r['exact'] for r in group)}
                        for lang in sorted({r['language'] for r in rows}) if (group := [r for r in rows if r['language'] == lang])},
        'routine_by_language': {lang: {'tasks': len(group), 'exact': sum(r['exact'] for r in group)}
                                for lang in sorted({r['language'] for r in routine}) if (group := [r for r in routine if r['language'] == lang])},
    }


def quality_gates(summary):
    """Fixed protocol V1 model gates. Packaging is a separate required check."""
    routine_kinds = {'config', 'lines', 'search', 'git_status', 'git_log', 'health', 'draft'}
    kinds = summary['by_kind']
    def rate(kind):
        row = kinds.get(kind, {})
        return row.get('exact', 0) / row['tasks'] if row.get('tasks') else 0
    return {
        'raw_protocol': summary['raw_protocol_valid_rate'] >= .995,
        'routine_exact': summary['routine_exact_rate'] is not None and summary['routine_exact_rate'] >= .95,
        'routine_outcomes': summary['execution_checked'] and summary['routine_outcome_rate'] is not None and summary['routine_outcome_rate'] >= .95,
        'useful_coverage': summary['routine_exact_rate'] is not None and summary['routine_exact_rate'] >= .70,
        'task_slice_floor': all(rate(kind) >= .90 for kind in routine_kinds),
        'language_slice_floor': all(lang in summary['routine_by_language'] and summary['routine_by_language'][lang]['exact'] / summary['routine_by_language'][lang]['tasks'] >= .90 for lang in ['en', 'zh']),
        'ambiguity': rate('ambiguous') >= .95,
        'unsupported_and_invalid': all(rate(kind) == 1 for kind in ['unsupported', 'missing_tool', 'invalid_range']),
        'unchanged_fixtures': summary['execution_checked'] and summary['filesystem_changes'] == 0,
    }
