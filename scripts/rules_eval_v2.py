"""Evaluate the deterministic public-context helper on the frozen V2 data."""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_environment import PilotEnvironment
from wrench.pilot_tasks_v2 import public_record
from wrench.pilot_workflow import rules_predict
from wrench.protocol import ROUTER_FALLBACK, prediction_matches_target
from wrench.release_eval import outcome_matches, quality_gates, summarize


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--split', choices=['development', 'evaluation'], default='evaluation')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = Path(args.data).resolve()
    output = Path(args.output).resolve()
    if not data.is_relative_to(ROOT / 'data/pilots'):
        raise SystemExit('V2 data must be under data/pilots')
    if not output.is_relative_to(ROOT / 'artifacts/model-release'):
        raise SystemExit('Output must be under artifacts/model-release')
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    task_path = data / f'{args.split}.jsonl'
    if manifest.get('version') != 'usefulness-pilot-v2' or digest(task_path) != manifest['splits'][args.split]['sha256']:
        raise ValueError('V2 data identity or checksum mismatch')
    tasks = [json.loads(line) for line in task_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    output.mkdir(parents=True, exist_ok=False)
    meta = {
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'data': str(data),
        'split': args.split,
        'dataset_sha256': digest(task_path),
        'source_sha256': {name: digest(ROOT / name) for name in ['scripts/rules_eval_v2.py', 'wrench/pilot_workflow.py', 'wrench/pilot_environment.py', 'wrench/release_eval.py']},
        'scope': 'Deterministic public-context helper, authored V2 tasks, no model or cloud calls',
    }
    (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    rows = []
    started = time.perf_counter()
    with (output / 'predictions.jsonl').open('w', encoding='utf-8') as handle:
        for task in tasks:
            env = PilotEnvironment(task, output / 'fixtures' / task['id'])
            try:
                source = env.task
                pred_start = time.perf_counter()
                action = rules_predict(public_record(source))
                prediction_duration = time.perf_counter() - pred_start
                execution = None
                if action != ROUTER_FALLBACK:
                    execution = env.execute(json.loads(action))
                row = {
                    'id': source['id'], 'family_id': source['family_id'], 'kind': source['kind'], 'language': source['language'],
                    'input': public_record(source), 'expected_call': {'tool': source['tool'], 'args': source['args']},
                    'expected_outcome': source['expected_answer'], 'expected_fallback': source['tool'] == 'fallback',
                    'raw': action, 'action': action, 'invalid_output': False, 'reason': 'rules',
                    'input_tokens': 0, 'output_tokens': 0, 'duration_s': prediction_duration,
                    'exact': prediction_matches_target(action, source), 'execution_checked': True,
                    'execution': execution, 'outcome_correct': outcome_matches(source, action, execution),
                }
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
                rows.append(row)
            finally:
                env.close()
    summary = summarize(rows)
    summary['model_quality_gates'] = quality_gates(summary)
    summary['model_quality_passed'] = all(summary['model_quality_gates'].values())
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    meta.update(status='completed', finished_at=datetime.now(timezone.utc).isoformat(), duration_s=time.perf_counter() - started)
    (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
