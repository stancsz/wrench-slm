"""Analyze complete selective A/B/C workflow receipts."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.pilot_analyze_v2 import accounting, comparisons, paired_groups, read_jsonl  # noqa: E402


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def summarize(rows):
    if not rows:
        raise ValueError('Cannot summarize an empty arm')
    local_routes = [row.get('local_route') or {} for row in rows]
    accepted = sum(route.get('route') == 'local' for route in local_routes)
    local_completed = sum(bool(row.get('local_completed')) for row in rows)
    local_attempted = sum(bool(route.get('local_attempted')) for route in local_routes)
    prompt_tokens = [row['prompt_tokens'] for row in rows]
    completion_tokens = [row['completion_tokens'] for row in rows]
    cached_tokens = [row.get('cached_tokens', 0) or 0 for row in rows]
    costs = []
    cost_complete = True
    for row in rows:
        value = row.get('provider_cost')
        if isinstance(value, (int, float)):
            costs.append(value)
        else:
            cost_complete = False
    return {
        'episodes': len(rows),
        'successes': sum(bool(row['success']) for row in rows),
        'success_rate': sum(bool(row['success']) for row in rows) / len(rows),
        'filesystem_unchanged': all(row.get('filesystem_unchanged', False) for row in rows),
        'usage_complete': all(row.get('usage_complete', False) for row in rows),
        'duration_s_mean': _mean([row['duration_s'] for row in rows]),
        'duration_s_p50': sorted(row['duration_s'] for row in rows)[len(rows) // 2],
        'prompt_tokens_total': sum(prompt_tokens),
        'completion_tokens_total': sum(completion_tokens),
        'cloud_tokens_total': sum(prompt_tokens) + sum(completion_tokens),
        'cached_tokens_total': sum(cached_tokens),
        'cloud_requests': sum(len(row['cloud_attempts']) for row in rows),
        'local_attempted': local_attempted,
        'local_accepted': accepted,
        'local_completed': local_completed,
        'local_attempt_rate': local_attempted / len(rows),
        'local_accepted_coverage': accepted / len(rows),
        'local_successful_coverage': local_completed / len(rows),
        'local_accepted_precision': local_completed / accepted if accepted else None,
        'local_predict_duration_s_total': sum(row.get('local_predict_duration_s', 0.0) for row in rows),
        'local_route_duration_s_total': sum(row.get('local_route_duration_s', 0.0) for row in rows),
        'local_policy_duration_s_total': sum((row.get('local_route') or {}).get('policy_duration_s', 0.0) for row in rows),
        'local_execution_duration_s_total': sum((row.get('local_route') or {}).get('execution_duration_s', 0.0) for row in rows),
        'local_format_duration_s_total': sum((row.get('local_route') or {}).get('format_duration_s', 0.0) for row in rows),
        'local_route_duration_s_mean': _mean([row.get('local_route_duration_s', 0.0) for row in rows]),
        'fallbacks': sum(bool((row.get('local_route') or {}).get('fallback_reason')) for row in rows),
        'correction_turns': sum(row.get('post_speculation_tool_request_turns', 0) for row in rows),
        'episode_failures': sum(bool(row.get('error')) for row in rows),
        'tool_errors': sum(bool(tool.get('error')) for row in rows for tool in row['tools']),
        'cost_available': cost_complete,
        'cost_total': sum(costs) if cost_complete else None,
    }


def verify_local_gate(path, meta):
    summary = json.loads(Path(path).read_text(encoding='utf-8'))
    expected = {
        'variant': meta['policy_variant'],
        'revision': meta['policy_revision'],
        'dataset_sha256': meta['dataset_split_sha256'],
        'manifest_sha256': meta['dataset_manifest_sha256'],
    }
    if summary.get('status') != 'completed':
        raise ValueError('Local quality receipt is incomplete')
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError('Local quality receipt identity differs from workflow')
    gates = {
        'nonempty': summary.get('accepted', 0) > 0,
        'zero_accepted_errors': summary.get('accepted_error_rate') == 0.0,
        'zero_mutations': summary.get('unexpected_mutations') == 0,
        'zero_ineligible_acceptance': all(
            value.get('accepted', 0) == 0
            for kind, value in summary.get('by_kind', {}).items()
            if kind in {'ambiguous', 'unsupported', 'missing_tool', 'invalid_range', 'over_budget'}
        ),
    }
    if not all(gates.values()):
        raise ValueError(f'Local quality gate failed: {gates}')
    return {'path': str(Path(path).resolve()), 'gates': gates, 'summary_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--local-quality-summary', required=True)
    args = parser.parse_args()
    run = Path(args.run).resolve()
    meta = json.loads((run / 'run.json').read_text(encoding='utf-8'))
    rows = read_jsonl(run / 'episodes.jsonl')
    grouped, families = paired_groups(rows)
    expected = int(meta['dataset_tasks_assigned'])
    if meta.get('status') != 'completed' or len(grouped) != expected or len(rows) != expected * 3:
        raise ValueError('Workflow is incomplete; no comparative verdict is allowed')
    if any(not row.get('usage_complete') for row in rows):
        raise ValueError('At least one episode lacks complete usage accounting')
    accounting_pass, gateway_receipts = accounting(run, meta['requested_cloud_model'])
    arms = {arm: summarize([row for row in rows if row['arm'] == arm]) for arm in ['A', 'B', 'C']}
    comp = comparisons(rows, int(meta['arguments']['seed']))
    local_gate = verify_local_gate(args.local_quality_summary, meta)
    intact = all(row.get('filesystem_unchanged') for row in rows)
    quality_pass = all(value['success_difference'] >= 0 and value['success_lower_95'] >= -0.02 for value in comp.values())
    c_vs_b = comp['C_vs_B']
    rules_value = comp['C_vs_A']
    learned_value = c_vs_b['tokens_saving_fraction'] > 0 and c_vs_b['tokens_saving_bootstrap_95'][0] > 0
    rules_only_value = rules_value['tokens_saving_fraction'] > 0 and rules_value['tokens_saving_bootstrap_95'][0] > 0
    if not accounting_pass:
        verdict = 'INCONCLUSIVE'
        reason = 'Provider model identity or usage accounting was incomplete.'
    elif not intact:
        verdict = 'NO-GO'
        reason = 'A workflow episode changed the fixture or crossed the execution boundary.'
    elif not quality_pass:
        verdict = 'INCONCLUSIVE'
        reason = 'Observed quality was not non-inferior to a matched baseline within the family uncertainty bound.'
    elif learned_value:
        verdict = 'MEASURED_SELECTIVE_BENEFIT'
        reason = 'The selectively admitted local model improved net cloud-token usage over the rules-only comparator with no observed quality loss.'
    elif rules_only_value:
        verdict = 'RULES_VALUE_LEARNED_PATH_NOT_EARNED'
        reason = 'Rules plus fallback created measured value, but the learned local proposal did not improve on the rules-only comparator.'
    else:
        verdict = 'NO_MEASURED_BENEFIT'
        reason = 'The complete matched workflow found no positive measured net token saving.'
    summary = {
        'verdict': verdict,
        'reason': reason,
        'workflow': meta.get('workflow'),
        'run': str(run),
        'arms': arms,
        'comparisons': comp,
        'decision_checks': {
            'complete_experiment': True,
            'accounting_pass': accounting_pass,
            'fixture_integrity': intact,
            'local_quality_gate': local_gate,
            'quality_noninferiority_pass': quality_pass,
            'learned_value_over_rules': learned_value,
            'rules_value_over_cloud_only': rules_only_value,
        },
        'gateway_receipts': gateway_receipts,
        'paired_families': len(families),
        'assigned_tasks': expected,
        'local_model_load_duration_s': meta.get('local_model_load_duration_s'),
        'uncertainty': '10,000 seeded family bootstrap resamples from the existing analyzer; authored families are not representative production traffic.',
        'analysis_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'episode_sha256': hashlib.sha256((run / 'episodes.jsonl').read_bytes()).hexdigest(),
    }
    (run / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    (run / 'REPORT.md').write_text(
        '\n'.join([
            '# Selective offload workflow result', '',
            f'**{verdict}: {reason}**', '',
            '| Arm | Success | Cloud tokens | Cloud requests | Local completions | Mean latency |',
            '| --- | ---: | ---: | ---: | ---: | ---: |',
            *[
                f'| {arm} | {value["successes"]}/{value["episodes"]} | {value["cloud_tokens_total"]} | {value["cloud_requests"]} | {value["local_completed"]} | {value["duration_s_mean"]:.3f}s |'
                for arm, value in arms.items()
            ],
            '',
            f'Paired families: {len(families)}. Assigned tasks: {expected}.',
            f'Rules value over cloud-only: {rules_value["tokens_saving_fraction"]:.3f}.',
            f'Learned value over rules-only: {c_vs_b["tokens_saving_fraction"]:.3f}.',
            'Per-arm summaries include cloud calls, prompt/completion/cached tokens, provider cost when available, local attempts/completions, fallbacks, correction turns, failures, load/prediction/validation timing, and total latency.',
            '',
        ]) + '\n', encoding='utf-8',
    )
    print(json.dumps({'verdict': verdict, 'reason': reason, 'comparisons': comp}, indent=2))


if __name__ == '__main__':
    main()
