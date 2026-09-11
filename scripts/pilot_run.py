"""Run the V2 fixed-budget usefulness workflow.

The runner requires every experiment identity as an explicit argument. It has
no fallback to the historical V1 dataset or candidate.
"""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from wrench.pilot_environment import PilotEnvironment
from wrench.pilot_inference import PilotExecutor
from wrench.pilot_tasks_v2 import public_record
from wrench.pilot_workflow import CloudClient, run_episode

MODEL = 'Qwen/Qwen2.5-0.5B-Instruct'
REVISION = '7ae557604adf67be50417f59c2c2f167def9a775'
V21_MANIFEST_SHA256 = '219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7'
V21_ADAPTER_SHA256 = '6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348'
PROTOCOL = ROOT / 'docs/reference/USEFULNESS_PILOT_PROTOCOL_V2.md'
DATA_ROOT = ROOT / 'data/pilots'
OUTPUT_ROOT = ROOT / 'artifacts/usefulness-pilot/v21-v2'
SOURCE_FILES = [
    'scripts/pilot_run.py',
    'scripts/pilot_analyze_v2.py',
    'scripts/audit_usefulness_v2_data.py',
    'wrench/pilot_tasks_v2.py',
    'wrench/pilot_environment.py',
    'wrench/pilot_workflow.py',
    'wrench/pilot_inference.py',
    'wrench/dataset.py',
    'wrench/protocol.py',
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command_output(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)
    return result.stdout.strip()


def git_receipt():
    diff = subprocess.run(['git', 'diff', '--no-ext-diff', '--binary'], cwd=ROOT, capture_output=True, check=False).stdout
    return {
        'head': command_output(['git', 'rev-parse', 'HEAD']),
        'status_short': command_output(['git', 'status', '--short']),
        'diff_sha256': hashlib.sha256(diff).hexdigest(),
    }


def read_tasks(data, split):
    data = Path(data).resolve()
    if not data.is_relative_to(DATA_ROOT.resolve()):
        raise ValueError('V2 data must be under data/pilots')
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version') != 'usefulness-pilot-v2':
        raise ValueError('Refusing non-V2 pilot data')
    path = data / f'{split}.jsonl'
    if digest(path) != manifest['splits'][split]['sha256']:
        raise ValueError(f'{split} dataset checksum mismatch')
    tasks = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(tasks) != manifest['splits'][split]['tasks'] or len({task['id'] for task in tasks}) != len(tasks):
        raise ValueError(f'{split} manifest count or task ID mismatch')
    for task in tasks:
        if set(public_record(task)) != {'prompt', 'context'}:
            raise ValueError('Invalid public record shape')
    return manifest, tasks


def load_base(device):
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; choose --device cpu only for a local diagnostic')
    dtype = torch.bfloat16 if device == 'cuda' else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, revision=REVISION, local_files_only=True, dtype=dtype, attn_implementation='sdpa'
    ).to(device).eval()
    return model, tokenizer


def verify_v21_package(package):
    package = Path(package).resolve()
    manifest_path = package / 'release_manifest.json'
    if digest(manifest_path) != V21_MANIFEST_SHA256:
        raise ValueError('Package manifest is not the immutable V21 manifest')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('adapter_sha256') != V21_ADAPTER_SHA256 or manifest.get('base_revision') != REVISION:
        raise ValueError('Package identity does not match the V21 protocol')
    return manifest


def load_executor(args):
    if args.package:
        package = Path(args.package).resolve()
        if not args.base_path:
            raise ValueError('--base-path is required with --package for offline reproducibility')
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(package))
        from _wrench_runtime.weight_inference import (
            load_executor as load_packaged_executor,
        )
        from _wrench_runtime.weight_inference import verify_package

        manifest = verify_v21_package(package)
        verify_package(package)
        executor = load_packaged_executor(package, device=args.device, local_files_only=True, base_path=args.base_path)
        if executor.max_input_tokens != args.max_input_tokens or executor.max_new_tokens != args.max_new_tokens:
            raise ValueError('Requested local token limits differ from the packaged runtime')
        return executor, {
            'source': 'checksummed_package',
            'package': str(package),
            'package_manifest_sha256': digest(package / 'release_manifest.json'),
            'adapter_sha256': manifest['adapter_sha256'],
            'base_weights_sha256': manifest['base_weights_sha256'],
            'base_revision': manifest['base_revision'],
        }
    model, tokenizer = load_base(args.device)
    if args.checkpoint:
        checkpoint = Path(args.checkpoint).resolve()
        contract = json.loads((checkpoint / 'training_contract.json').read_text(encoding='utf-8'))
        if contract['formatter_sha256'] != digest(ROOT / 'wrench/dataset.py'):
            raise ValueError('Checkpoint formatter does not match the current source')
        model = PeftModel.from_pretrained(model, checkpoint).eval()
        return PilotExecutor(model, tokenizer, max_input_tokens=args.max_input_tokens, max_new_tokens=args.max_new_tokens), {
            'source': 'local_checkpoint',
            'checkpoint': str(checkpoint),
            'adapter_sha256': digest(checkpoint / 'adapter_model.safetensors'),
            'base_revision': REVISION,
        }
    return PilotExecutor(model, tokenizer, max_input_tokens=args.max_input_tokens, max_new_tokens=args.max_new_tokens), {
        'source': 'pinned_base',
        'base_revision': REVISION,
    }


def package_versions():
    names = ['torch', 'transformers', 'peft', 'numpy']
    return {name: importlib.metadata.version(name) for name in names}


def parse_args():
    parser = argparse.ArgumentParser(description='Run the explicit V2 Wrench usefulness workflow')
    parser.add_argument('--phase', choices=['smoke', 'evaluation'], required=True)
    parser.add_argument('--data', required=True, help='V2 data directory under data/pilots')
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--package', help='Immutable packaged adapter, required for workflow phases')
    source.add_argument('--checkpoint', help='Explicit local adapter checkpoint for diagnostics only')
    parser.add_argument('--base-path', help='Exact local pinned base directory for packaged inference')
    parser.add_argument('--output', required=True, help='New run directory under artifacts/usefulness-pilot/v21-v2')
    parser.add_argument('--protocol', default=str(PROTOCOL))
    parser.add_argument('--endpoint', default='http://127.0.0.1:4000/v1/chat/completions')
    parser.add_argument('--model', default='minimax/minimax-m3')
    parser.add_argument('--seed', type=int, default=20260910)
    parser.add_argument('--device', choices=['cuda', 'cpu'], default='cuda')
    parser.add_argument('--max-input-tokens', type=int, default=1536)
    parser.add_argument('--max-new-tokens', type=int, default=192)
    parser.add_argument('--max-attempts', type=int)
    parser.add_argument('--max-cloud-tokens', type=int, default=3_000_000)
    parser.add_argument('--admission-input-tokens', type=int, default=32_768)
    parser.add_argument('--max-cloud-output-tokens', type=int, default=384)
    parser.add_argument('--max-request-bytes', type=int, default=24_000)
    parser.add_argument('--timeout-seconds', type=float, default=45)
    parser.add_argument('--smoke-cases', type=int, default=4)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.package:
        raise SystemExit('V2 workflow requires the explicit --package V21 artifact')
    data = Path(args.data).resolve()
    output = Path(args.output).resolve()
    if not output.is_relative_to(OUTPUT_ROOT.resolve()):
        raise SystemExit('Output must be a new directory under artifacts/usefulness-pilot/v21-v2')
    if output.exists():
        raise SystemExit(f'Output already exists: {output}')
    protocol = Path(args.protocol).resolve()
    if protocol != PROTOCOL.resolve():
        raise SystemExit('This runner is frozen to USEFULNESS_PILOT_PROTOCOL_V2.md')
    manifest, tasks = read_tasks(data, 'development' if args.phase == 'smoke' else 'evaluation')
    if args.phase == 'smoke':
        if args.smoke_cases < 1 or args.smoke_cases > len(tasks):
            raise SystemExit('--smoke-cases must be within the development split')
        tasks = sorted(tasks, key=lambda task: task['id'])[:args.smoke_cases]
        default_attempts = 12
    else:
        default_attempts = 5400
    max_attempts = args.max_attempts if args.max_attempts is not None else default_attempts
    if max_attempts < 1:
        raise SystemExit('--max-attempts must be positive')
    if args.phase == 'evaluation' and max_attempts > 5400:
        raise SystemExit('V2 evaluation attempt budget cannot exceed 5400')
    if args.phase == 'smoke' and max_attempts > 12:
        raise SystemExit('V2 smoke attempt budget cannot exceed 12')
    output.mkdir(parents=True, exist_ok=False)
    source_hashes = {name: digest(ROOT / name) for name in SOURCE_FILES if (ROOT / name).is_file()}
    split = 'development' if args.phase == 'smoke' else 'evaluation'
    meta = {
        'status': 'running',
        'phase': args.phase,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'arguments': vars(args),
        'model': MODEL,
        'revision': REVISION,
        'model_source': None,
        'protocol_sha256': digest(protocol),
        'data_root': str(data),
        'dataset_manifest_sha256': digest(data / 'manifest.json'),
        'dataset_split': split,
        'dataset_split_sha256': manifest['splits'][split]['sha256'],
        'dataset_tasks_assigned': len(tasks),
        'seed': args.seed,
        'endpoint': args.endpoint,
        'requested_cloud_model': args.model,
        'attempt_budget': max_attempts,
        'cloud_token_budget': args.max_cloud_tokens,
        'cloud_admission_input_tokens': args.admission_input_tokens,
        'cloud_max_output_tokens': args.max_cloud_output_tokens,
        'cloud_request_body_bytes': args.max_request_bytes,
        'cloud_timeout_seconds': args.timeout_seconds,
        'local_token_limits': {'max_input_tokens': args.max_input_tokens, 'max_new_tokens': args.max_new_tokens},
        'platform': platform.platform(),
        'python': sys.version,
        'packages': package_versions(),
        'hardware': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu',
        'git': git_receipt(),
        'source_sha256': source_hashes,
        'scored_arms': ['A', 'B', 'C'],
        'scope': 'V2 matched authored Windows workflow; no deployment or production claim',
    }
    (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    (output / 'protocol.md').write_bytes(protocol.read_bytes())
    for name in source_hashes:
        snapshot = output / 'source' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    started = time.perf_counter()
    rows = []
    try:
        executor, model_source = load_executor(args)
        meta['model_source'] = model_source
        (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        warmup = executor.predict(public_record(tasks[0]))
        meta['warmup'] = warmup.to_dict()
        (output / 'warmup.json').write_text(json.dumps(meta['warmup'], indent=2), encoding='utf-8')
        rng = random.Random(args.seed)
        rng.shuffle(tasks)
        (output / 'schedule.json').write_text(json.dumps([task['id'] for task in tasks], indent=2), encoding='utf-8')
        cloud = output / 'cloud'
        fixtures = output / 'fixtures'
        fixtures.mkdir()
        client = CloudClient(
            cloud, max_attempts=max_attempts, max_tokens=args.max_cloud_tokens,
            endpoint=args.endpoint, model=args.model, timeout_s=args.timeout_seconds,
            max_request_bytes=args.max_request_bytes,
            admission_input_tokens=args.admission_input_tokens,
            max_output_tokens=args.max_cloud_output_tokens,
        )
        with (output / 'episodes.jsonl').open('w', encoding='utf-8') as handle:
            for index, source_task in enumerate(tasks):
                env = PilotEnvironment(source_task, fixtures / source_task['id'])
                arms = ['A', 'B', 'C']
                rng.shuffle(arms)
                try:
                    for arm in arms:
                        result = run_episode(env, arm, client, executor)
                        result['fixture_fingerprint'] = env.initial_fingerprint
                        handle.write(json.dumps(result, ensure_ascii=False) + '\n')
                        handle.flush()
                        rows.append(result)
                        print(f'[{index + 1}/{len(tasks)} {arm}] success={result["success"]} time={result["duration_s"]:.2f}s requests={len(result["cloud_attempts"])}', flush=True)
                        if result.get('accounting_stop'):
                            raise RuntimeError('Stopped on incomplete accounting or budget limit; inspect the retained receipts')
                        if not result['filesystem_unchanged']:
                            raise RuntimeError('Fixture state changed unexpectedly')
                finally:
                    env.close()
        meta.update(cloud_attempts=client.attempts, reported_cloud_tokens=client.tokens,
                    observed_cloud_models=sorted({r.get('response', {}).get('model') for r in client.receipts if r.get('response')}))
        meta['status'] = 'completed'
    except Exception as exc:
        meta.update(status='failed', error=f'{type(exc).__name__}: {exc}', tasks_completed=len(rows))
        raise
    finally:
        meta.update(
            duration_s=time.perf_counter() - started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            tasks_completed=len(rows),
            peak_allocated_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0,
            peak_reserved_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_available() else 0,
        )
        (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
