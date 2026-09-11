"""Run the frozen selective-offload A/B/C workflow.

This runner is separate from the historical V2 runner. It refuses to make
provider calls without an explicit token ceiling and an explicit authorization
flag, and it binds the run to the frozen revision-1 selection receipt.
"""

import argparse
import hashlib
import json
import platform
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from scripts.pilot_run import load_executor, package_versions  # noqa: E402
from wrench.pilot_environment import PilotEnvironment  # noqa: E402
from wrench.pilot_tasks import public_record  # noqa: E402
from wrench.pilot_workflow import CloudClient, run_episode  # noqa: E402


DATA_VERSION = 'selective-offload-v1'
SELECTIVE_ROOT = ROOT / 'artifacts/selective-offload-real-runtime-v2'
SELECTION_RECEIPT = ROOT / 'artifacts/selective-offload-real-runtime-v2/selection-eligible-v2.json'
PROTOCOL = ROOT / 'docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md'
POLICY_SOURCE = ROOT / 'wrench/selective_policy.py'
RUNTIME_SOURCE = ROOT / 'wrench/selective_runtime.py'
V21_MANIFEST_SHA256 = '219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_receipt():
    import subprocess

    result = subprocess.run(
        ['git', 'status', '--short'], cwd=ROOT, capture_output=True,
        text=True, encoding='utf-8', errors='replace', check=False,
    )
    return {
        'status_short': result.stdout.strip(),
    }


def read_tasks(data, split):
    data = Path(data).resolve()
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version') != DATA_VERSION:
        raise ValueError(f'Expected {DATA_VERSION} data')
    path = data / f'{split}.jsonl'
    if digest(path) != manifest['splits'][split]['sha256']:
        raise ValueError('Selective dataset checksum mismatch')
    tasks = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(tasks) != manifest['splits'][split]['tasks']:
        raise ValueError('Selective manifest count mismatch')
    if len({task['id'] for task in tasks}) != len(tasks):
        raise ValueError('Selective task IDs are not unique')
    for task in tasks:
        if set(public_record(task)) != {'prompt', 'context'}:
            raise ValueError('Invalid public record shape')
    return manifest, tasks, path


def verify_frozen_identity(data, manifest, split, variant, revision, package):
    if not SELECTION_RECEIPT.is_file():
        raise ValueError(f'Missing frozen selection receipt: {SELECTION_RECEIPT}')
    frozen = json.loads(SELECTION_RECEIPT.read_text(encoding='utf-8'))
    if frozen.get('status') != 'FROZEN_FOR_HELD_OUT_EVALUATION':
        raise ValueError('Selection receipt is not frozen')
    if frozen.get('policy') != variant or frozen.get('revision') != revision:
        raise ValueError('Requested policy does not match the frozen receipt')
    if frozen.get('protocol_sha256') != digest(PROTOCOL):
        raise ValueError('Protocol differs from the frozen receipt')
    if frozen.get('data_manifest_sha256') != digest(data / 'manifest.json'):
        raise ValueError('Data manifest differs from the frozen receipt')
    if frozen.get('evaluation_dataset_sha256') != digest(data / f'{split}.jsonl'):
        raise ValueError('Evaluation split differs from the frozen receipt')
    if frozen.get('policy_source_sha256') != digest(POLICY_SOURCE):
        raise ValueError('Policy source differs from the frozen receipt')
    if frozen.get('runtime_source_sha256') != digest(RUNTIME_SOURCE):
        raise ValueError('Runtime verifier source differs from the frozen receipt')
    package = Path(package).resolve()
    if digest(package / 'release_manifest.json') != V21_MANIFEST_SHA256:
        raise ValueError('Package is not the immutable V21 package')
    if frozen.get('package_manifest_sha256') != digest(package / 'release_manifest.json'):
        raise ValueError('Package differs from the frozen receipt')
    return frozen


def parse_args():
    parser = argparse.ArgumentParser(description='Run frozen selective-offload A/B/C workflow')
    parser.add_argument('--data', required=True, help='Selective data directory')
    parser.add_argument('--split', choices=['evaluation'], default='evaluation')
    parser.add_argument('--package', required=True)
    parser.add_argument('--base-path', required=True)
    parser.add_argument('--output', required=True, help='New directory under artifacts/selective-offload-real-runtime-v2')
    parser.add_argument('--variant', choices=['eligible'], default='eligible')
    parser.add_argument('--revision', choices=['intent-v2'], default='intent-v2')
    parser.add_argument('--endpoint', default='http://127.0.0.1:4000/v1/chat/completions')
    parser.add_argument('--model', default='minimax/minimax-m3')
    parser.add_argument('--seed', type=int, default=20260910)
    parser.add_argument('--device', choices=['cuda', 'cpu'], default='cuda')
    parser.add_argument('--max-input-tokens', type=int, default=1536)
    parser.add_argument('--max-new-tokens', type=int, default=192)
    parser.add_argument('--max-attempts', type=int, required=True)
    parser.add_argument('--max-cloud-tokens', type=int, required=True)
    parser.add_argument('--admission-input-tokens', type=int, default=32768)
    parser.add_argument('--max-cloud-output-tokens', type=int, default=384)
    parser.add_argument('--max-request-bytes', type=int, default=24000)
    parser.add_argument('--timeout-seconds', type=float, default=45)
    parser.add_argument('--authorize-paid-run', action='store_true',
                        help='Required before making provider calls')
    parser.add_argument('--bypass-local', action='store_true',
                        help='Skip local proposal/completion and route B/C directly to the stronger model')
    parser.add_argument('--dry-run', action='store_true',
                        help='Verify frozen identity and write preflight metadata without loading or calling models')
    return parser.parse_args()


def main():
    args = parse_args()
    data = Path(args.data).resolve()
    output = Path(args.output).resolve()
    if not output.is_relative_to(SELECTIVE_ROOT.resolve()):
        raise SystemExit(f'Output must be under {SELECTIVE_ROOT}')
    if output.exists():
        raise SystemExit(f'Output already exists: {output}')
    if args.max_attempts < 1 or args.max_attempts > 5400:
        raise SystemExit('--max-attempts must be between 1 and 5400')
    if args.max_cloud_tokens < 1:
        raise SystemExit('--max-cloud-tokens must be positive')
    if not args.dry_run and not args.authorize_paid_run:
        raise SystemExit('Provider calls require --authorize-paid-run after the token ceiling is reviewed')
    manifest, tasks, split_path = read_tasks(data, args.split)
    frozen = verify_frozen_identity(data, manifest, args.split, args.variant, args.revision, args.package)
    meta = {
        'status': 'preflight',
        'workflow': 'selective-offload-real-runtime-v2',
        'phase': 'evaluation',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'arguments': vars(args),
        'model': 'Qwen/Qwen2.5-0.5B-Instruct',
        'revision': '7ae557604adf67be50417f59c2c2f167def9a775',
        'policy_variant': args.variant,
        'policy_revision': args.revision,
        'selection_receipt': str(SELECTION_RECEIPT),
        'selection_receipt_sha256': digest(SELECTION_RECEIPT),
        'protocol_sha256': digest(PROTOCOL),
        'policy_source_sha256': digest(POLICY_SOURCE),
        'data_root': str(data),
        'dataset_manifest_sha256': digest(data / 'manifest.json'),
        'dataset_split': args.split,
        'dataset_split_sha256': digest(split_path),
        'dataset_tasks_assigned': len(tasks),
        'endpoint': args.endpoint,
        'requested_cloud_model': args.model,
        'attempt_budget': args.max_attempts,
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
        'frozen_identity': frozen,
        'scored_arms': ['A', 'B', 'C'],
        'scope': 'Selective authored Windows workflow; no deployment or production claim',
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    (output / 'protocol.md').write_bytes(PROTOCOL.read_bytes())
    if args.dry_run:
        meta['status'] = 'preflight_complete'
        (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        print(json.dumps(meta, indent=2))
        return
    started = time.perf_counter()
    meta['status'] = 'running'
    (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    rows = []
    try:
        loader_args = argparse.Namespace(
            package=args.package, base_path=args.base_path, checkpoint=None,
            device=args.device, max_input_tokens=args.max_input_tokens,
            max_new_tokens=args.max_new_tokens,
        )
        load_started = time.perf_counter()
        if args.bypass_local:
            executor = None
            meta['local_model_load_duration_s'] = 0.0
            meta['model_source'] = {'source': 'operator_bypass', 'local_model_loaded': False}
            meta['warmup'] = {'bypassed': True}
        else:
            executor, model_source = load_executor(loader_args)
            meta['local_model_load_duration_s'] = time.perf_counter() - load_started
            meta['model_source'] = model_source
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
            cloud, max_attempts=args.max_attempts, max_tokens=args.max_cloud_tokens,
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
                        result = run_episode(
                            env, arm, client, executor,
                            selective_variant=args.variant if arm in ['B', 'C'] else None,
                            selective_revision=args.revision,
                            bypass_local=args.bypass_local,
                        )
                        result['fixture_fingerprint'] = env.initial_fingerprint
                        handle.write(json.dumps(result, ensure_ascii=False) + '\n')
                        handle.flush()
                        rows.append(result)
                        print(
                            f'[{index + 1}/{len(tasks)} {arm}] success={result["success"]} '
                            f'local={result.get("local_completed", False)} '
                            f'time={result["duration_s"]:.2f}s requests={len(result["cloud_attempts"])}',
                            flush=True,
                        )
                        if result.get('accounting_stop'):
                            raise RuntimeError('Stopped on incomplete accounting or budget limit')
                        if not result['filesystem_unchanged']:
                            raise RuntimeError('Fixture state changed unexpectedly')
                finally:
                    env.close()
        meta.update(
            cloud_attempts=client.attempts,
            reported_cloud_tokens=client.tokens,
            observed_cloud_models=sorted({r.get('response', {}).get('model') for r in client.receipts if r.get('response')}),
            status='completed',
        )
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
