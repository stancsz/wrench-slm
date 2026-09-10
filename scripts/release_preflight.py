"""Validate all release-data targets and lengths before spending training compute."""

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from transformers import AutoTokenizer  # noqa: E402
from wrench.dataset import build_training_prompt, format_completion  # noqa: E402
from wrench.pilot_inference import validate_prediction  # noqa: E402
from wrench.protocol import canonical_json  # noqa: E402
from wrench.pilot_tasks import public_record  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = Path(args.data)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    model = 'Qwen/Qwen2.5-0.5B-Instruct'
    revision = '7ae557604adf67be50417f59c2c2f167def9a775'
    tokenizer = AutoTokenizer.from_pretrained(model, revision=revision, local_files_only=True)
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    report = {'status': 'passed', 'model': model, 'revision': revision, 'splits': {},
              'packages': {p: importlib.metadata.version(p) for p in ['torch', 'transformers', 'peft', 'tokenizers', 'safetensors']},
              'formatter_sha256': hashlib.sha256((ROOT / 'wrench/dataset.py').read_bytes()).hexdigest()}
    input_sets, families = {}, {}
    for split in manifest['splits']:
        path = data / f'{split}.jsonl'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['splits'][split]['sha256']
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        lengths, completions, prompts = [], [], []
        input_sets[split], families[split] = set(), set()
        for row in rows:
            raw = format_completion(row)
            assert not validate_prediction(raw, row['context']['tools'])[1], row['id']
            prompt_length = len(tokenizer(build_training_prompt(row, tokenizer), add_special_tokens=False)['input_ids'])
            completion_length = len(tokenizer(raw, add_special_tokens=False)['input_ids']) + 1
            assert prompt_length + completion_length <= 1536, row['id']
            assert completion_length <= 192, row['id']
            lengths.append(prompt_length + completion_length)
            completions.append(completion_length)
            prompts.append(prompt_length)
            input_sets[split].add(canonical_json(public_record(row)))
            families[split].add(row['family_id'])
        report['splits'][split] = {'tasks': len(rows), 'max_training_tokens': max(lengths),
                                   'max_prompt_tokens': max(prompts), 'max_completion_tokens': max(completions),
                                   'kinds': dict(Counter(r['kind'] for r in rows)),
                                   'languages': dict(Counter(r['language'] for r in rows)),
                                   'sha256': manifest['splits'][split]['sha256']}
    for a in input_sets:
        for b in input_sets:
            if a != b:
                assert not input_sets[a] & input_sets[b]
                assert not families[a] & families[b]
    (output / 'preflight.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
