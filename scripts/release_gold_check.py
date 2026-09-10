"""Check golden tool calls against real fixtures without invoking any model."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_environment import PilotEnvironment  # noqa: E402
from wrench.release_eval import outcome_matches  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--split', default='evaluation')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = Path(args.data)
    path = data / f'{args.split}.jsonl'
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['splits'][args.split]['sha256']:
        raise ValueError('Dataset checksum mismatch')
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT / 'artifacts/model-release'):
        parser.error('Use artifacts/model-release for disposable fixtures')
    output.mkdir(parents=True, exist_ok=False)
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    count = passed = fallback = 0
    with (output / 'gold_outcomes.jsonl').open('w', encoding='utf-8') as file:
        for source in rows:
            if source['tool'] == 'fallback':
                fallback += 1
                continue
            env = PilotEnvironment(source, output / 'fixtures' / source['id'])
            try:
                task = env.task
                call = {'tool': task['tool'], 'args': task['args']}
                receipt = env.execute(call)
                correct = outcome_matches(task, json.dumps(call), receipt)
                file.write(json.dumps({'id': task['id'], 'correct': correct, 'receipt': receipt}, ensure_ascii=False) + '\n')
                count += 1
                passed += correct
            finally:
                env.close()
    result = {'model_invocations': 0, 'gold_calls_checked': count, 'gold_outcomes_passed': passed,
              'fallback_cases_requiring_semantic_label_review': fallback, 'dataset_sha256': manifest['splits'][args.split]['sha256'],
              'scope': 'Checks executable gold outcomes only; does not measure model predictions or prove fallback label semantics.'}
    (output / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if passed != count:
        raise SystemExit('Some gold outcomes failed')


if __name__ == '__main__':
    main()
