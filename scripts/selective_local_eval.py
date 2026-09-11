"""Run the fresh selective local gate on the immutable V21 package."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.pilot_run import load_executor  # noqa: E402
from wrench.selective_eval import evaluate_local_task, load_tasks, summarize  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def args_for_loader(args):
    return argparse.Namespace(
        package=args.package, base_path=args.base_path, checkpoint=None,
        device=args.device, max_input_tokens=args.max_input_tokens,
        max_new_tokens=args.max_new_tokens,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--split', choices=['development', 'evaluation'], required=True)
    parser.add_argument('--package', required=True)
    parser.add_argument('--base-path', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--variant', choices=['agreement', 'safe', 'eligible'], required=True)
    parser.add_argument('--revision', choices=['v1', 'intent-v2'], default='v1')
    parser.add_argument('--bypass', action='store_true', help='Immediately route every task to fallback')
    parser.add_argument('--resume', action='store_true', help='Continue an existing incomplete output directory')
    parser.add_argument('--device', choices=['cuda', 'cpu'], default='cuda')
    parser.add_argument('--max-input-tokens', type=int, default=1536)
    parser.add_argument('--max-new-tokens', type=int, default=192)
    args = parser.parse_args()
    data = Path(args.data).resolve()
    output = Path(args.output).resolve()
    if output.exists() and not args.resume:
        raise SystemExit(f'Output exists: {output}; pass --resume only for an incomplete run')
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version') != 'selective-offload-v1':
        raise SystemExit('Not selective-offload-v1 data')
    tasks_path = data / f'{args.split}.jsonl'
    tasks = load_tasks(tasks_path)
    if len(tasks) != manifest['splits'][args.split]['tasks']:
        raise SystemExit('Manifest task count mismatch')
    existing_rows = []
    rows_path = output / 'rows.jsonl'
    summary_path = output / 'summary.json'
    if args.resume:
        if summary_path.exists() or not rows_path.exists():
            raise SystemExit('Resume requires an existing incomplete rows.jsonl without summary.json')
        existing_rows = [json.loads(line) for line in rows_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        known_ids = {row['task_id'] for row in existing_rows}
        if not known_ids.issubset({task['id'] for task in tasks}) or len(known_ids) != len(existing_rows):
            raise SystemExit('Existing rows do not match this split or contain duplicate task IDs')
    if args.bypass:
        executor = None
        model_source = {'source': 'operator_bypass', 'local_model_loaded': False}
    else:
        executor, model_source = load_executor(args_for_loader(args))
    output.mkdir(parents=True, exist_ok=True)
    rows = list(existing_rows)
    completed_ids = {row['task_id'] for row in existing_rows}
    mode = 'a' if args.resume else 'w'
    with rows_path.open(mode, encoding='utf-8') as handle:
        for index, task in enumerate(tasks, 1):
            if task['id'] in completed_ids:
                continue
            fixture_root = output / ('fixtures-resume' if args.resume else 'fixtures') / task['id']
            predictor = executor.predict if executor is not None else None
            row = evaluate_local_task(task, fixture_root, predictor, args.variant, args.revision, args.bypass)
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
            handle.flush()
            rows.append(row)
            print(f'[{index}/{len(tasks)}] accepted={row["local_accepted"]} success={row["local_success"]} reason={row["policy"]["reason"]}', flush=True)
    summary = summarize(rows)
    summary.update({
        'status': 'completed', 'data': str(data), 'split': args.split,
        'dataset_sha256': digest(tasks_path), 'manifest_sha256': digest(data / 'manifest.json'),
        'package': str(Path(args.package).resolve()),
        'package_manifest_sha256': digest(Path(args.package) / 'release_manifest.json'),
        'variant': args.variant, 'revision': args.revision, 'model_source': model_source,
        'device': args.device, 'max_input_tokens': args.max_input_tokens,
        'max_new_tokens': args.max_new_tokens,
        'policy_scope': 'public prompt and context only; no private labels or fixture contents',
    })
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
