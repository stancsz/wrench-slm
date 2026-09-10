"""Select among all predeclared completed checkpoints using development only."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.release_eval import quality_gates, summarize  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--training-run', required=True)
    parser.add_argument('--evaluations', nargs='+', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    training = Path(args.training_run).resolve()
    receipt = json.loads((training / 'run.json').read_text(encoding='utf-8'))
    if receipt['status'] != 'completed':
        raise ValueError('Training run is incomplete')
    final_step = receipt['training']['steps']
    interval = receipt['arguments']['checkpoint_every']
    expected_steps = set(range(interval, final_step, interval)) | {final_step}
    records = []
    for directory in args.evaluations:
        directory = Path(directory).resolve()
        meta = json.loads((directory / 'run.json').read_text(encoding='utf-8'))
        if meta['status'] != 'completed' or meta['arguments']['split'] != 'development':
            raise ValueError('Selection requires completed development evaluations')
        checkpoint = Path(meta['arguments']['checkpoint']).resolve()
        if checkpoint.parent != training or digest(checkpoint / 'adapter_model.safetensors') != meta['adapter_sha256']:
            raise ValueError('Checkpoint identity mismatch')
        metrics = json.loads((checkpoint / 'training_metrics.json').read_text(encoding='utf-8'))
        contract = json.loads((checkpoint / 'training_contract.json').read_text(encoding='utf-8'))
        if contract['val_sha256'] != meta['dataset_sha256']:
            raise ValueError('Selection dataset differs from declared development data')
        data = Path(meta['arguments']['data'])
        manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
        rows = [json.loads(line) for line in (directory / 'predictions.jsonl').read_text(encoding='utf-8').splitlines()]
        if len(rows) != manifest['splits']['development']['tasks'] or len({r['id'] for r in rows}) != len(rows):
            raise ValueError('Incomplete or duplicated predictions')
        summary = summarize(rows)
        gates = quality_gates(summary)
        records.append({'step': metrics['steps'], 'checkpoint': str(checkpoint),
                        'adapter_sha256': meta['adapter_sha256'], 'evaluation': str(directory),
                        'exact': summary['exact'], 'tasks': summary['tasks'], 'exact_rate': summary['exact_rate'],
                        'validation_loss': metrics['validation_loss'], 'quality_gates': gates,
                        'quality_passed': all(gates.values()),
                        'prediction_receipt_sha256': digest(directory / 'predictions.jsonl')})
    if {r['step'] for r in records} != expected_steps or len(records) != len(expected_steps):
        raise ValueError('Every predeclared checkpoint must be evaluated exactly once')
    selected = sorted(records, key=lambda r: (-r['exact_rate'], r['validation_loss'], r['step']))[0]
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    result = {'selection_rule': 'highest development exact rate, then lowest validation loss, then earliest step',
              'training_run_sha256': digest(training / 'run.json'), 'selected': selected, 'candidates': records,
              'status': 'TRAINED CANDIDATE' if selected['quality_passed'] else 'TRAINED CANDIDATE, QUALITY GATES FAILED',
              'release_approved': False}
    (output / 'selection.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Development checkpoint selection', '', f"Status: {result['status']}", '',
             '| Step | Exact predictions | Validation loss | Quality gates |', '| --- | --- | --- | --- |']
    lines += [f"| {r['step']} | {r['exact']}/{r['tasks']} | {r['validation_loss']:.6f} | {'PASS' if r['quality_passed'] else 'FAIL'} |" for r in records]
    lines += ['', f"Selected step {selected['step']} by the predeclared development rule.",
              'Independent release evaluation, challenge checks, and final package approval are still required.']
    (output / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
