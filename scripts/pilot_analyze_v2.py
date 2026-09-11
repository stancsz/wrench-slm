"""Analyze a complete V2 matched workflow without V1 fixed denominators."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 10_000


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def summarize(rows):
    if not rows:
        raise ValueError('Cannot summarize an empty arm')
    result = {
        'episodes': len(rows),
        'successes': sum(bool(row['success']) for row in rows),
        'success_rate': float(np.mean([bool(row['success']) for row in rows])),
        'filesystem_unchanged': all(row.get('filesystem_unchanged', False) for row in rows),
        'usage_complete': all(row.get('usage_complete', False) for row in rows),
    }
    for key in ['duration_s', 'prompt_tokens', 'completion_tokens']:
        values = [row[key] for row in rows]
        result[key + '_mean'] = float(np.mean(values))
        result[key + '_p50'] = float(np.percentile(values, 50))
        result[key + '_p95'] = float(np.percentile(values, 95))
        result[key + '_p99'] = float(np.percentile(values, 99))
    result['total_cloud_tokens_mean'] = result['prompt_tokens_mean'] + result['completion_tokens_mean']
    result['cloud_requests'] = sum(len(row['cloud_attempts']) for row in rows)
    result['actual_tool_executions'] = sum(tool['executed'] for row in rows for tool in row['tools'])
    result['draft_submissions'] = sum(tool['draft_only'] for row in rows for tool in row['tools'])
    result['tool_errors'] = sum(bool(tool.get('error')) for row in rows for tool in row['tools'])
    result['invalid_predictions'] = sum(bool(row.get('prediction', {}).get('invalid_output')) for row in rows if row.get('prediction'))
    result['explicit_fallbacks'] = sum(row.get('prediction', {}).get('action') == 'ROUTER_FALLBACK' for row in rows if row.get('prediction'))
    result['prediction_exact'] = sum(bool(row.get('prediction_exact')) for row in rows if row.get('prediction'))
    result['speculation_supplied'] = sum(bool(row.get('speculation_supplied')) for row in rows)
    result['speculation_sufficient'] = sum(bool(row.get('speculation_sufficient')) for row in rows)
    result['post_speculation_tool_request_turns'] = sum(row.get('post_speculation_tool_request_turns', 0) for row in rows)
    return result


def paired_groups(rows):
    grouped = defaultdict(dict)
    for row in rows:
        grouped[row['task_id']][row['arm']] = row
    if not grouped:
        raise ValueError('No paired episodes')
    if any(set(group) != {'A', 'B', 'C'} for group in grouped.values()):
        raise ValueError('Every assigned task must have exactly one A, B, and C episode')
    family_ids = sorted({group['A']['family_id'] for group in grouped.values()})
    if any({group['A']['family_id'], group['B']['family_id'], group['C']['family_id']} != {group['A']['family_id']} for group in grouped.values()):
        raise ValueError('Matched arms disagree on family')
    families = {family: [group for group in grouped.values() if group['A']['family_id'] == family] for family in family_ids}
    return grouped, families


def comparisons(rows, seed):
    _, families = paired_groups(rows)
    family_ids = sorted(families)
    family_count = len(family_ids)
    indices = np.random.default_rng(seed).integers(0, family_count, size=(BOOTSTRAP_RESAMPLES, family_count))
    output = {}
    for comparator in ['A', 'B']:
        c_success = np.array([np.mean([group['C']['success'] for group in families[family]]) for family in family_ids], dtype=float)
        b_success = np.array([np.mean([group[comparator]['success'] for group in families[family]]) for family in family_ids], dtype=float)
        success_differences = c_success - b_success
        success_samples = success_differences[indices].mean(axis=1)
        observed_success = float(success_differences.mean())
        quality_method = 'family_bootstrap_percentile'
        quality_lower = float(np.percentile(success_samples, 2.5))
        if np.all(success_differences == 0):
            quality_method = 'all_success_family_exact_fallback'
            c_all_success = bool(np.all(c_success == 1))
            c_lower = ALPHA ** (1 / family_count) if c_all_success else 0.0
            quality_lower = c_lower - 1.0
        c_tokens = np.array([np.mean([group['C']['prompt_tokens'] + group['C']['completion_tokens'] for group in families[family]]) for family in family_ids])
        b_tokens = np.array([np.mean([group[comparator]['prompt_tokens'] + group[comparator]['completion_tokens'] for group in families[family]]) for family in family_ids])
        token_samples = 1 - c_tokens[indices].mean(axis=1) / b_tokens[indices].mean(axis=1)
        c_latency = np.array([np.mean([group['C']['duration_s'] for group in families[family]]) for family in family_ids])
        b_latency = np.array([np.mean([group[comparator]['duration_s'] for group in families[family]]) for family in family_ids])
        latency_samples = 1 - c_latency[indices].mean(axis=1) / b_latency[indices].mean(axis=1)
        output['C_vs_' + comparator] = {
            'families': family_count,
            'success_difference': observed_success,
            'success_lower_95': quality_lower,
            'success_bootstrap_95': np.percentile(success_samples, [2.5, 97.5]).tolist(),
            'success_uncertainty_method': quality_method,
            'tokens_saving_fraction': float(1 - c_tokens.mean() / b_tokens.mean()),
            'tokens_saving_bootstrap_95': np.percentile(token_samples, [2.5, 97.5]).tolist(),
            'latency_saving_fraction': float(1 - c_latency.mean() / b_latency.mean()),
            'latency_saving_bootstrap_95': np.percentile(latency_samples, [2.5, 97.5]).tolist(),
        }
    return output


def accounting(run, expected_model):
    receipts = []
    for path in sorted((run / 'cloud').glob('*.json')):
        receipt = json.loads(path.read_text(encoding='utf-8'))
        response = receipt.get('response') or {}
        usage = response.get('usage') or {}
        valid_usage = all(isinstance(usage.get(key), int) and usage[key] >= 0 for key in ['prompt_tokens', 'completion_tokens'])
        receipts.append({
            'file': path.name,
            'request_model': receipt.get('request', {}).get('model'),
            'response_model': response.get('model'),
            'provider_usage': valid_usage,
            'cheap_plus_telemetry': bool(response.get('_cheap_plus_telemetry')),
            'error': receipt.get('error'),
        })
    passed = bool(receipts) and all(
        row['request_model'] == expected_model and row['response_model'] == expected_model
        and row['provider_usage'] and not row['cheap_plus_telemetry'] and not row['error']
        for row in receipts
    )
    return passed, receipts


def validate_complete(meta, rows):
    expected_tasks = int(meta['dataset_tasks_assigned'])
    counts = Counter((row['task_id'], row['arm']) for row in rows)
    grouped, _ = paired_groups(rows)
    complete = (
        meta['status'] == 'completed'
        and len(rows) == expected_tasks * 3
        and len(grouped) == expected_tasks
        and len(counts) == expected_tasks * 3
        and all(value == 1 for value in counts.values())
        and all(row.get('usage_complete') for row in rows)
    )
    if not complete:
        raise ValueError('Incomplete V2 experiment; no comparative verdict is allowed')
    return grouped


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def validate_quality_receipts(meta, quality_paths):
    """Bind local quality summaries to the exact completed workflow identity."""
    if not quality_paths:
        return {'state': 'missing', 'reason': 'No local quality receipt was supplied', 'receipts': []}
    source = meta.get('model_source') or {}
    expected = {
        'model': meta.get('model'),
        'revision': meta.get('revision'),
        'dataset_sha256': meta.get('dataset_split_sha256'),
        'protocol_sha256': meta.get('protocol_sha256'),
        'adapter_sha256': source.get('adapter_sha256'),
        'package_manifest_sha256': source.get('package_manifest_sha256'),
        'base_weights_sha256': source.get('base_weights_sha256'),
    }
    if any(value is None for value in expected.values()):
        return {'state': 'missing', 'reason': 'Workflow identity is incomplete', 'receipts': []}
    receipts = []
    for supplied in quality_paths:
        path = Path(supplied).resolve()
        summary_path = path / 'summary.json' if path.is_dir() else path
        run_path = summary_path.parent / 'run.json'
        summary = _read_json(summary_path)
        receipt = _read_json(run_path)
        if not isinstance(summary, dict) or not isinstance(receipt, dict):
            return {'state': 'missing', 'reason': f'Missing or invalid quality receipt: {path}', 'receipts': receipts}
        if receipt.get('status') != 'completed':
            return {'state': 'missing', 'reason': f'Quality run is not completed: {run_path}', 'receipts': receipts}
        if any(receipt.get(key) != value for key, value in expected.items()):
            return {'state': 'missing', 'reason': f'Quality receipt identity mismatch: {run_path}', 'receipts': receipts}
        if not isinstance(summary.get('model_quality_passed'), bool) or not isinstance(summary.get('model_quality_gates'), dict):
            return {'state': 'missing', 'reason': f'Quality summary lacks complete gate fields: {summary_path}', 'receipts': receipts}
        receipts.append({
            'summary': str(summary_path),
            'run': str(run_path),
            'model_quality_passed': summary['model_quality_passed'],
            'model_quality_gates': summary['model_quality_gates'],
        })
    state = 'passed' if all(item['model_quality_passed'] for item in receipts) else 'failed'
    reason = 'All identity-bound local quality gates passed' if state == 'passed' else 'An identity-bound local quality gate failed'
    return {'state': state, 'reason': reason, 'receipts': receipts}


def latency_tradeoffs(comparisons, threshold=-.10):
    return {
        key: {
            'latency_saving_fraction': value['latency_saving_fraction'],
            'material_regression': value['latency_saving_fraction'] < threshold,
        }
        for key, value in comparisons.items()
    }


def slice_summary(rows, field):
    return {
        value: {arm: summarize([row for row in rows if row[field] == value and row['arm'] == arm]) for arm in ['A', 'B', 'C']}
        for value in sorted({row[field] for row in rows})
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--quality-summary', action='append', default=[], help='Completed local quality summary paths')
    args = parser.parse_args()
    run = Path(args.run).resolve()
    meta = json.loads((run / 'run.json').read_text(encoding='utf-8'))
    rows = read_jsonl(run / 'episodes.jsonl')
    validate_complete(meta, rows)
    complete = True
    accounting_pass, receipt_rows = accounting(run, meta['requested_cloud_model'])
    arms = {arm: summarize([row for row in rows if row['arm'] == arm]) for arm in ['A', 'B', 'C']}
    comp = comparisons(rows, int(meta['seed']))
    quality_pass = all(value['success_difference'] >= 0 and value['success_lower_95'] >= -.02 for value in comp.values())
    value_pass = all(
        value['tokens_saving_fraction'] >= .10 and value['tokens_saving_bootstrap_95'][0] > 0
        for value in comp.values()
    )
    intact = all(row['filesystem_unchanged'] for row in rows)
    quality_paths = [Path(path).resolve() for path in args.quality_summary]
    quality_receipts = validate_quality_receipts(meta, quality_paths)
    local_quality_pass = quality_receipts['state'] == 'passed'
    local_quality_failed = quality_receipts['state'] == 'failed'
    latency = latency_tradeoffs(comp)
    material_latency_regression = any(value['material_regression'] for value in latency.values())
    if not intact or any(arms[arm]['tool_errors'] and arm == 'C' for arm in arms):
        verdict, reason = 'NO-GO', 'The workflow violated a fixture or execution boundary.'
    elif not accounting_pass:
        verdict, reason = 'INCONCLUSIVE', 'Complete provider model identity or usage accounting was not established.'
    elif quality_receipts['state'] == 'missing':
        verdict, reason = 'INCONCLUSIVE', quality_receipts['reason']
    elif local_quality_failed:
        verdict, reason = 'NO-GO', quality_receipts['reason']
    elif not value_pass:
        verdict, reason = 'NO-GO', 'V21 did not meet the prespecified token-saving criterion against both comparators.'
    elif not quality_pass:
        verdict, reason = 'INCONCLUSIVE', 'Observed value was sufficient, but the prespecified quality noninferiority bound was not met.'
    elif material_latency_regression:
        verdict, reason = 'INCONCLUSIVE', 'Primary value passed, but a greater-than-10% latency regression requires a qualified decision.'
    else:
        verdict, reason = 'GO', 'The declared local quality, accounting, quality, and token-value criteria passed within this authored population.'
    summary = {
        'verdict': verdict,
        'reason': reason,
        'arms': arms,
        'comparisons': comp,
        'decision_checks': {
            'complete_experiment': complete,
            'accounting_pass': accounting_pass,
            'fixture_integrity': intact,
            'local_quality_pass': local_quality_pass,
            'local_quality_state': quality_receipts['state'],
            'value_pass': value_pass,
            'quality_noninferiority_pass': quality_pass,
            'material_latency_regression': material_latency_regression,
        },
        'quality_summaries': [str(path) for path in quality_paths],
        'quality_receipts': quality_receipts,
        'latency_tradeoffs': latency,
        'gateway_receipts': receipt_rows,
        'per_kind': slice_summary(rows, 'kind'),
        'per_language': slice_summary(rows, 'language'),
        'analysis_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'episode_sha256': hashlib.sha256((run / 'episodes.jsonl').read_bytes()).hexdigest(),
        'uncertainty': '10,000 seeded wording-family bootstrap resamples; degenerate all-zero paired differences use the predeclared exact all-success family fallback. Authored families are not representative production traffic.',
    }
    (run / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = [
        '# Wrench usefulness pilot V2 result',
        '',
        f'**{verdict}: {reason}**',
        '',
        'This result concerns the exact V21 package on newly authored Windows scenarios. It does not establish production coverage or arbitrary tool safety.',
        '',
        '| Arm | Success | Mean latency | Mean cloud tokens | Cloud requests |',
        '|---|---:|---:|---:|---:|',
    ]
    for arm, value in arms.items():
        lines.append(f'| {arm} | {value["successes"]}/{value["episodes"]} | {value["duration_s_mean"]:.3f} s | {value["total_cloud_tokens_mean"]:.1f} | {value["cloud_requests"]} |')
    lines += ['', 'A is cloud-only, B is the deterministic helper, and C is V21. Every assigned episode is included.', '', '## Comparisons', '']
    for key, value in comp.items():
        lines.append(f'- {key}: token saving {100 * value["tokens_saving_fraction"]:.1f}% with interval {value["tokens_saving_bootstrap_95"]}; latency saving {100 * value["latency_saving_fraction"]:.1f}%; success difference {100 * value["success_difference"]:.1f} points with lower bound {100 * value["success_lower_95"]:.1f} points.')
    if material_latency_regression:
        lines += ['', 'Qualification: a greater-than-10% latency regression was observed against at least one comparator; this result is not an unqualified GO.']
    lines += ['', '## Limits', '', '- Authored wording families do not estimate production traffic.', '- A GO would authorize only a supervised pilot, not deployment.', '- Missing usage or model identity is a failed accounting condition, not zero cost.', '']
    (run / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'verdict': verdict, 'reason': reason, 'comparisons': comp}, indent=2))


if __name__ == '__main__':
    main()
