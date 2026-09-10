"""Reproducible paired analysis of the complete, real three-arm pilot."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def summarize(rows):
    result = {'episodes': len(rows), 'successes': sum(r['success'] for r in rows), 'success_rate': np.mean([r['success'] for r in rows])}
    for key in ['duration_s', 'prompt_tokens', 'completion_tokens']:
        result[key + '_mean'] = float(np.mean([r[key] for r in rows]))
    result['total_cloud_tokens_mean'] = result['prompt_tokens_mean'] + result['completion_tokens_mean']
    result['latency_percentiles_s'] = {str(p): float(np.percentile([r['duration_s'] for r in rows], p)) for p in [50, 95, 99]}
    result['cloud_requests'] = sum(len(r['cloud_attempts']) for r in rows)
    result['actual_tool_executions'] = sum(t['executed'] for r in rows for t in r['tools'])
    result['draft_submissions'] = sum(t['draft_only'] for r in rows for t in r['tools'])
    result['tool_errors'] = sum(bool(t.get('error')) for r in rows for t in r['tools'])
    result['extra_cloud_turns_after_first'] = sum(max(0, len(r['cloud_attempts']) - 1) for r in rows)
    predictions = [r for r in rows if r.get('prediction')]
    if predictions:
        result['local_prediction_mean_s'] = float(np.mean([r['prediction']['duration_s'] for r in predictions]))
        result['prediction_exact'] = sum(r.get('prediction_exact', False) for r in predictions)
        result['invalid_predictions'] = sum(r['prediction'].get('invalid_output', False) for r in predictions)
        result['fallbacks'] = sum(r['prediction']['action'] == 'ROUTER_FALLBACK' for r in predictions)
        result['speculation_sufficient'] = sum(r.get('speculation_sufficient', False) for r in predictions)
        result['speculation_supplied'] = sum(r.get('speculation_supplied', False) for r in predictions)
        result['post_speculation_tool_request_turns'] = sum(r.get('post_speculation_tool_request_turns', 0) for r in predictions)
    return result


def comparisons(rows):
    paired = defaultdict(dict)
    for row in rows:
        paired[row['task_id']][row['arm']] = row
    families = sorted({r['family_id'] for r in rows})
    groups = {family: [arms for arms in paired.values() if arms['A']['family_id'] == family] for family in families}
    indices = np.random.default_rng(20260909).integers(0, len(families), size=(10_000, len(families)))
    output = {}
    for comparator in ['A', 'B']:
        values = {}
        for metric in ['success', 'duration_s', 'tokens']:
            def val(row):
                return row['prompt_tokens'] + row['completion_tokens'] if metric == 'tokens' else row[metric]
            c = np.array([np.mean([val(arms['C']) for arms in groups[f]]) for f in families])
            b = np.array([np.mean([val(arms[comparator]) for arms in groups[f]]) for f in families])
            if metric == 'success':
                samples = (c[indices] - b[indices]).mean(axis=1)
                observed = float((c - b).mean())
                values['success_difference'] = observed
                values['success_difference_bootstrap_95'] = np.percentile(samples, [2.5, 97.5]).tolist()
                # Cluster bootstrap degenerates when every outcome is identical.
                # A distribution-free one-sided Hoeffding bound for independent
                # family means in [-1, 1] avoids claiming tight certainty then.
                values['success_difference_conservative_lower_95'] = max(-1.0, observed - math.sqrt(2 * math.log(20) / len(families)))
            else:
                samples = 1 - c[indices].mean(axis=1) / b[indices].mean(axis=1)
                values[metric + '_saving_fraction'] = float(1 - c.mean() / b.mean())
                values[metric + '_saving_bootstrap_95'] = np.percentile(samples, [2.5, 97.5]).tolist()
        output['C_vs_' + comparator] = values
    return output


def correlate(run):
    clouds = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((run / 'cloud').glob('*.json'))]
    ids = {r.get('request_id') for r in clouds}
    ids.discard(None)
    events = defaultdict(list)
    for p in Path(r'C:\Users\stanc\github\lean-router\logs\events').glob('*.jsonl'):
        for row in read_jsonl(p):
            if row.get('req_id') in ids:
                events[row['req_id']].append(row)
    audit = {}
    for request in clouds:
        ident = request.get('request_id')
        selected = events.get(ident, [])
        outbound = [r for r in selected if r.get('event') == 'outbound_context']
        usage = [r for r in selected if r.get('event') == 'request']
        audit[str(ident)] = {
            'attempt': request['attempt'], 'outbound_contexts': len(outbound),
            'provider_usage_event': any(r.get('usage_source') == 'provider' for r in usage),
            'response_usage': request.get('response', {}).get('usage'),
            'response_model': request.get('response', {}).get('model'),
        }
    (run / 'gateway_correlation.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    return all(r['outbound_contexts'] == 1 and r['provider_usage_event'] and r['response_model'] == 'minimax/minimax-m3' for r in audit.values()) and len(audit) == len(clouds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    run = Path(args.run)
    meta = json.loads((run / 'run.json').read_text(encoding='utf-8'))
    rows = read_jsonl(run / 'episodes.jsonl')
    counts = Counter((r['task_id'], r['arm']) for r in rows)
    if meta['status'] != 'completed' or len(rows) != 360 or len(counts) != 360 or len({r['task_id'] for r in rows}) != 120 or any(v != 1 for v in counts.values()) or any(not r['usage_complete'] for r in rows):
        raise ValueError('Incomplete experiment; cannot issue a final comparative verdict')
    if any({r['arm'] for r in rows if r['task_id'] == ident} != {'A', 'B', 'C'} for ident in {r['task_id'] for r in rows}):
        raise ValueError('Incomplete matched arms')
    correlation = correlate(run)
    arms = {arm: summarize([r for r in rows if r['arm'] == arm]) for arm in ['A', 'B', 'C']}
    comp = comparisons(rows)
    value_pass = all(any(v[key + '_saving_fraction'] >= .1 and v[key + '_saving_bootstrap_95'][0] > 0 for key in ['duration_s', 'tokens']) for v in comp.values())
    quality_pass = all(v['success_difference'] >= 0 and v['success_difference_conservative_lower_95'] >= -.02 for v in comp.values())
    intact = all(r['filesystem_unchanged'] for r in rows)
    if not intact:
        verdict = 'NO-GO'
        reason = 'Fixture mutation detected.'
    elif not correlation:
        verdict = 'INCONCLUSIVE'
        reason = 'Complete single-call provider accounting was not independently correlated.'
    elif not value_pass:
        verdict = 'NO-GO'
        reason = 'This fixed-budget candidate did not meet the predeclared value criterion against both comparators. Quality uncertainty is reported separately.'
    elif not quality_pass:
        verdict = 'INCONCLUSIVE'
        reason = 'Value criterion met, but the pilot cannot establish the required task-quality noninferiority.'
    else:
        verdict = 'GO'
        reason = 'Declared value and quality criteria met within the authored task scope.'
    summary = {'verdict': verdict, 'reason': reason, 'arms': arms, 'comparisons': comp,
               'decision_checks': {'value_pass': value_pass, 'quality_noninferiority_pass': quality_pass},
               'gateway_accounting_correlated': correlation, 'fixture_integrity': intact,
               'per_kind': {kind: {a: summarize([r for r in rows if r['kind'] == kind and r['arm'] == a]) for a in arms} for kind in sorted({r['kind'] for r in rows})},
               'per_language': {lang: {a: summarize([r for r in rows if r['language'] == lang and r['arm'] == a]) for a in arms} for lang in sorted({r['language'] for r in rows})},
               'analysis_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'episode_sha256': hashlib.sha256((run / 'episodes.jsonl').read_bytes()).hexdigest(),
               'uncertainty': '10,000 paired wording-family bootstrap resamples; conservative Hoeffding bound for quality. Authored families are not a representative sample of production traffic.'}
    (run / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    lines = ['# Wrench usefulness pilot result', '', f'**{verdict}: {reason}**', '',
             'This result concerns one pretrained Pro SFT candidate on 120 authored Windows scenarios in 24 wording families. It does not establish production coverage or rule out a different model or integration.', '',
             '| Arm | Task success | Mean total latency | Mean cloud tokens | Cloud requests |', '|---|---:|---:|---:|---:|']
    for arm, s in arms.items():
        lines.append(f'| {arm} | {s["successes"]}/{s["episodes"]} | {s["duration_s_mean"]:.3f} s | {s["total_cloud_tokens_mean"]:.1f} | {s["cloud_requests"]} |')
    lines += ['', 'A is the existing native-tool cloud workflow. B adds simple rules. C adds Wrench-Pro. Every episode, including failure, is included.', '', '## Interpretation', '']
    for key, v in comp.items():
        lines += [f'- {key}: mean latency saving {100*v["duration_s_saving_fraction"]:.1f}%; mean cloud-token saving {100*v["tokens_saving_fraction"]:.1f}%; observed success difference {100*v["success_difference"]:.1f} percentage points.']
    lines += ['', 'The small clustered pilot cannot be treated as proof of a tight production error bound. See summary.json for uncertainty, tails, slice results, invalid predictions, fallbacks, and correction counts.', '',
              '## Evidence and limitations', '',
              '- Real native-tool cloud calls and real disposable OS fixtures were used. No generated writes were applied.',
              '- Gateway correlation and provider usage are recorded in gateway_correlation.json. Raw requests and responses are in cloud/.',
              '- Model/tokenizer/dataset/protocol/source identities are in run.json and the referenced training receipts.',
              '- Tasks are authored, template-family partitioned scenarios. They are not recovered live user requests.',
              '- One randomized run per arm and task was used. Shared host activity and provider variability remain limitations.',
              '- No GRPO, Flash training, model promotion, or production rollout followed from this pilot.', '',
              '## Next justified action', '',
              'Review the failure and cost breakdown before additional training. Any narrower deployment claim needs a fresh independent confirmation set. Preserve this run and do not tune against its evaluation outcomes.']
    (run / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'verdict': verdict, 'arms': arms, 'comparisons': comp}, indent=2))


if __name__ == '__main__':
    main()
