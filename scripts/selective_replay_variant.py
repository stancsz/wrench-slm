"""Replay a recorded immutable model prediction under another policy variant."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.selective_eval import evaluate_local_task, load_tasks, summarize


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--split', choices=['development', 'evaluation'], required=True)
    parser.add_argument('--predictions', required=True, help='rows.jsonl from a completed model prediction run')
    parser.add_argument('--output', required=True)
    parser.add_argument('--variant', choices=['agreement', 'safe', 'eligible'], required=True)
    parser.add_argument('--revision', choices=['v1', 'intent-v2'], default='v1')
    args = parser.parse_args()
    data = Path(args.data).resolve()
    prediction_path = Path(args.predictions).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f'Output exists: {output}')
    tasks = load_tasks(data / f'{args.split}.jsonl')
    prediction_rows = [json.loads(line) for line in prediction_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    predictions = {row['task_id']: row['prediction'] for row in prediction_rows}
    if len(predictions) != len(tasks) or set(predictions) != {task['id'] for task in tasks}:
        raise SystemExit('Prediction rows do not match the requested split')
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    with (output / 'rows.jsonl').open('w', encoding='utf-8') as handle:
        for index, task in enumerate(tasks, 1):
            predictor = lambda record, prediction=predictions[task['id']]: prediction
            row = evaluate_local_task(task, output / 'fixtures' / task['id'], predictor, args.variant, args.revision)
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
            rows.append(row)
            print(f'[{index}/{len(tasks)}] accepted={row["local_accepted"]} success={row["local_success"]}', flush=True)
    summary = summarize(rows)
    summary.update({
        'status': 'completed', 'data': str(data), 'split': args.split,
        'dataset_sha256': digest(data / f'{args.split}.jsonl'),
        'prediction_source': str(prediction_path), 'prediction_source_sha256': digest(prediction_path),
        'variant': args.variant, 'revision': args.revision,
        'policy_scope': 'public prompt and context only; no private labels or fixture contents',
    })
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
