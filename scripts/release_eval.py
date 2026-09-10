"""Evaluate a specified local adapter or base without cloud calls or a router."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch  # noqa: E402
from peft import PeftModel  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

from wrench.pilot_environment import PilotEnvironment  # noqa: E402
from wrench.pilot_inference import PilotExecutor  # noqa: E402
from wrench.pilot_tasks import public_record  # noqa: E402
from wrench.protocol import ROUTER_FALLBACK, prediction_matches_target  # noqa: E402
from wrench.release_eval import outcome_matches, quality_gates, summarize  # noqa: E402

MODEL = 'Qwen/Qwen2.5-0.5B-Instruct'
REVISION = '7ae557604adf67be50417f59c2c2f167def9a775'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--split', choices=['development', 'evaluation'], default='development')
    model_source = parser.add_mutually_exclusive_group()
    model_source.add_argument('--checkpoint', help='Omit both model sources for unchanged pretrained base')
    model_source.add_argument('--package', help='Evaluate the exact exported package and its bundled inference runtime')
    parser.add_argument('--base-path', help='Explicit local base dependency for packaged inference')
    parser.add_argument('--output', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--max-input-tokens', type=int, default=1536)
    parser.add_argument('--max-new-tokens', type=int, default=192)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT / 'artifacts/model-release'):
        parser.error('Output must be a new directory under artifacts/model-release')
    data = Path(args.data)
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    task_path = data / f'{args.split}.jsonl'
    if digest(task_path) != manifest['splits'][args.split]['sha256']:
        raise ValueError('Dataset checksum mismatch')
    tasks = [json.loads(line) for line in task_path.read_text(encoding='utf-8').splitlines()]
    if len(tasks) != manifest['splits'][args.split]['tasks'] or len({t['id'] for t in tasks}) != len(tasks):
        raise ValueError('Manifest count mismatch or duplicate task IDs')
    output.mkdir(parents=True, exist_ok=False)
    checkpoint = Path(args.checkpoint or args.package).resolve() if args.checkpoint or args.package else None
    started = time.perf_counter()
    meta = {'status': 'running', 'started_at': datetime.now(timezone.utc).isoformat(),
            'arguments': vars(args), 'model': MODEL, 'revision': REVISION,
            'adapter_sha256': digest(checkpoint / ('weights/adapter_model.safetensors' if args.package else 'adapter_model.safetensors')) if checkpoint else None,
            'dataset_sha256': digest(task_path), 'hardware': torch.cuda.get_device_name(0),
            'protocol_sha256': digest(ROOT / 'docs/reference/MODEL_RELEASE_PROTOCOL_V1.md'),
            'platform': platform.platform(), 'packages': {name: importlib.metadata.version(name) for name in ['torch', 'transformers', 'peft']},
            'source_sha256': {name: digest(ROOT / name) for name in ['scripts/release_eval.py', 'wrench/release_eval.py', 'wrench/pilot_inference.py', 'wrench/pilot_environment.py', 'wrench/dataset.py', 'wrench/protocol.py']},
            'scope': 'Direct model predictions; authored tasks; zero cloud requests; no serving promotion'}
    (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    for name in meta['source_sha256']:
        snapshot = output / 'source' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    (output / 'protocol.md').write_bytes((ROOT / 'docs/reference/MODEL_RELEASE_PROTOCOL_V1.md').read_bytes())
    rows = []
    try:
        torch.manual_seed(42)
        torch.cuda.reset_peak_memory_stats()
        if args.package:
            # Frozen historical packages checksum bytecode; importing must not rewrite it.
            sys.dont_write_bytecode = True
            sys.path.insert(0, str(checkpoint))
            from _wrench_runtime.weight_inference import load_executor, verify_package
            verify_package(checkpoint)
            executor = load_executor(checkpoint, device='cuda', local_files_only=True, base_path=args.base_path)
            if executor.max_input_tokens != args.max_input_tokens or executor.max_new_tokens != args.max_new_tokens:
                raise ValueError('Evaluation token limits differ from packaged inference')
            meta['package_manifest_sha256'] = digest(checkpoint / 'release_manifest.json')
            meta['inference_source'] = 'Checksummed packaged runtime'
        else:
            tokenizer = AutoTokenizer.from_pretrained(str(checkpoint) if checkpoint else MODEL, revision=None if checkpoint else REVISION, local_files_only=True)
            model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, local_files_only=True, dtype=torch.bfloat16, attn_implementation='sdpa').to('cuda')
            if checkpoint:
                contract = json.loads((checkpoint / 'training_contract.json').read_text(encoding='utf-8'))
                if contract['formatter_sha256'] != digest(ROOT / 'wrench/dataset.py'):
                    raise ValueError('Checkpoint formatter mismatch')
                vocab_hash = hashlib.sha256(json.dumps(tokenizer.get_vocab(), sort_keys=True).encode()).hexdigest()
                if vocab_hash != contract['vocab_sha256']:
                    raise ValueError('Checkpoint tokenizer mismatch')
                model = PeftModel.from_pretrained(model, checkpoint)
            executor = PilotExecutor(model, tokenizer, max_input_tokens=args.max_input_tokens, max_new_tokens=args.max_new_tokens)
        meta['load_duration_s'] = time.perf_counter() - started
        with (output / 'predictions.jsonl').open('w', encoding='utf-8') as handle:
            for index, source in enumerate(tasks):
                env = PilotEnvironment(source, output / 'fixtures' / source['id']) if args.execute else None
                task = env.task if env else source
                try:
                    prediction = executor.predict(public_record(task))
                    execution = None
                    if env and prediction.action != ROUTER_FALLBACK:
                        execution = env.execute(json.loads(prediction.action))
                    row = {'id': task['id'], 'family_id': task['family_id'], 'kind': task['kind'], 'language': task['language'],
                           'input': public_record(task), 'expected_call': {'tool': task['tool'], 'args': task['args']},
                           'expected_outcome': task['expected_answer'],
                           'expected_fallback': task['tool'] == 'fallback', **prediction.to_dict(),
                           'exact': prediction_matches_target(prediction.action, task) and not prediction.invalid_output and prediction.reason != 'input_budget',
                           'execution_checked': bool(env), 'execution': execution,
                           'outcome_correct': outcome_matches(task, prediction.action, execution) and not prediction.invalid_output and prediction.reason != 'input_budget' if env else None}
                    handle.write(json.dumps(row, ensure_ascii=False) + '\n')
                    handle.flush()
                    rows.append(row)
                    if (index + 1) % 20 == 0 or index + 1 == len(tasks):
                        print(f'[prediction] {index + 1}/{len(tasks)} exact={sum(r["exact"] for r in rows)}', flush=True)
                finally:
                    if env:
                        env.close()
        summary = summarize(rows)
        summary['model_quality_gates'] = quality_gates(summary)
        summary['model_quality_passed'] = all(summary['model_quality_gates'].values())
        (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        meta['status'] = 'completed'
        print(json.dumps(summary, indent=2), flush=True)
    except Exception as exc:
        meta.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        meta.update(finished_at=datetime.now(timezone.utc).isoformat(), duration_s=time.perf_counter() - started,
                    tasks_completed=len(rows), peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved())
        (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
