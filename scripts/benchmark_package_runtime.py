"""Measure bounded cold, warm, memory, and queue behavior of V21 inference."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import BoundedSemaphore

import psutil
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.pilot_run import verify_v21_package


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_tasks(data, cases):
    path = data / 'development.jsonl'
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if digest(path) != manifest['splits']['development']['sha256']:
        raise ValueError('Development dataset checksum mismatch')
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    selected = []
    for language in ['en', 'zh']:
        for kind in sorted({row['kind'] for row in rows}):
            match = next((row for row in rows if row['language'] == language and row['kind'] == kind), None)
            if match:
                selected.append(match)
    return selected[:cases], digest(path)


def load_executor(package, base_path, device):
    verify_v21_package(package)
    sys.path.insert(0, str(package))
    from _wrench_runtime.weight_inference import load_executor as load_packaged_executor
    from _wrench_runtime.weight_inference import verify_package

    verify_package(package)
    return load_packaged_executor(package, device=device, local_files_only=True, base_path=base_path)


def predict(executor, task):
    started = time.perf_counter()
    try:
        result = executor.predict({'prompt': task['prompt'], 'context': task['context']})
        return {
            'id': task['id'], 'duration_s': time.perf_counter() - started,
            'input_tokens': result.input_tokens, 'output_tokens': result.output_tokens,
            'reason': result.reason, 'error': None,
        }
    except Exception as exc:  # noqa: BLE001
        return {'id': task['id'], 'duration_s': time.perf_counter() - started,
                'input_tokens': None, 'output_tokens': None, 'reason': None,
                'error': f'{type(exc).__name__}: {exc}'}


def percentiles(values):
    values = sorted(values)
    if not values:
        return {'p50': None, 'p95': None, 'p99': None}
    def at(percent):
        index = min(len(values) - 1, round((percent / 100) * (len(values) - 1)))
        return values[index]
    return {'p50': at(50), 'p95': at(95), 'p99': at(99)}


def run_worker(args):
    data = Path(args.data).resolve()
    package = Path(args.package).resolve()
    base_path = Path(args.base_path).resolve()
    tasks, _ = load_tasks(data, args.cases)
    started = time.perf_counter()
    executor = load_executor(package, base_path, args.device)
    load_duration = time.perf_counter() - started
    record = predict(executor, tasks[args.worker_index])
    record['load_duration_s'] = load_duration
    record['rss_after_load_bytes'] = psutil.Process().memory_info().rss
    if torch.cuda.is_available():
        record['cuda_allocated_bytes'] = torch.cuda.memory_allocated()
        record['cuda_reserved_bytes'] = torch.cuda.memory_reserved()
        record['cuda_peak_allocated_bytes'] = torch.cuda.max_memory_allocated()
    print(json.dumps(record))


def bounded_queue(executor, task, capacity):
    semaphore = BoundedSemaphore(capacity)
    admitted = []
    rejected = 0
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=1) as pool:
        futures = []
        for _ in range(capacity * 2):
            if semaphore.acquire(blocking=False):
                submitted = time.perf_counter()
                futures.append(pool.submit(lambda submitted=submitted: {
                    'queue_wait_s': time.perf_counter() - submitted,
                    'prediction': predict(executor, task),
                }))
            else:
                rejected += 1
        for future in futures:
            admitted.append(future.result())
            semaphore.release()
    return {
        'capacity': capacity, 'submitted': len(admitted), 'rejected': rejected,
        'elapsed_s': time.perf_counter() - started,
        'queue_wait_s': percentiles([row['queue_wait_s'] for row in admitted]),
        'prediction_latency_s': percentiles([row['prediction']['duration_s'] for row in admitted]),
        'errors': sum(row['prediction']['error'] is not None for row in admitted),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--package', required=True)
    parser.add_argument('--base-path', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--device', choices=['cuda', 'cpu'], default='cuda')
    parser.add_argument('--cases', type=int, default=22)
    parser.add_argument('--worker-index', type=int)
    args = parser.parse_args()
    data = Path(args.data).resolve()
    package = Path(args.package).resolve()
    base_path = Path(args.base_path).resolve()
    output = Path(args.output).resolve()
    if args.worker_index is not None:
        run_worker(args)
        return
    if not data.is_relative_to(ROOT / 'data/pilots') or not output.is_relative_to(ROOT / 'artifacts/model-release'):
        raise SystemExit('Data must be under data/pilots and output under artifacts/model-release')
    if output.exists():
        raise SystemExit(f'Output already exists: {output}')
    if args.cases < 2:
        raise SystemExit('--cases must be at least 2')
    tasks, dataset_sha256 = load_tasks(data, args.cases)
    output.mkdir(parents=True)
    verify_v21_package(package)
    cold = []
    for index in range(5):
        started = time.perf_counter()
        result = subprocess.run([
            sys.executable, __file__, '--worker-index', str(index % len(tasks)), '--data', str(data),
            '--package', str(package), '--base-path', str(base_path), '--device', args.device, '--cases', str(args.cases),
            '--output', str(output),
        ], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)
        elapsed = time.perf_counter() - started
        record = {'repeat': index + 1, 'process_elapsed_s': elapsed, 'returncode': result.returncode,
                  'stderr': result.stderr[-2000:]}
        if result.returncode == 0:
            record['worker'] = json.loads(result.stdout.strip().splitlines()[-1])
        cold.append(record)
    process = psutil.Process()
    rss_before_load = process.memory_info().rss
    started = time.perf_counter()
    executor = load_executor(package, base_path, args.device)
    load_duration = time.perf_counter() - started
    rss_peak = process.memory_info().rss
    warm_rows = []
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    warm_started = time.perf_counter()
    for repeat in range(3):
        for task in tasks:
            row = predict(executor, task)
            row['repeat'] = repeat + 1
            warm_rows.append(row)
            rss_peak = max(rss_peak, process.memory_info().rss)
    warm_elapsed = time.perf_counter() - warm_started
    queue = [bounded_queue(executor, tasks[0], capacity) for capacity in [2, 4]]
    rss_after_load = process.memory_info().rss
    cold_failures = sum(record['returncode'] != 0 for record in cold)
    warm_errors = sum(row['error'] is not None for row in warm_rows)
    benchmark_status = 'MEASURED' if cold_failures == 0 and warm_errors == 0 else 'INCOMPLETE'
    summary = {
        'status': benchmark_status,
        'package_manifest_sha256': digest(package / 'release_manifest.json'),
        'dataset_sha256': dataset_sha256,
        'cases': len(tasks),
        'cold_starts': cold,
        'cold_failures': cold_failures,
        'warm': {
            'passes': 3, 'predictions': len(warm_rows), 'elapsed_s': warm_elapsed,
            'completions_per_second': len(warm_rows) / warm_elapsed,
            'prediction_latency_s': percentiles([row['duration_s'] for row in warm_rows]),
            'errors': warm_errors,
        },
        'model_load_duration_s': load_duration,
        'rss_before_load_bytes': rss_before_load,
        'rss_after_load_bytes': rss_after_load,
        'rss_peak_bytes': max(rss_peak, rss_after_load),
        'queue': queue,
        'cuda_allocated_bytes': torch.cuda.memory_allocated() if torch.cuda.is_available() else None,
        'cuda_reserved_bytes': torch.cuda.memory_reserved() if torch.cuda.is_available() else None,
        'cuda_peak_allocated_bytes': torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None,
        'no_tool_execution': True,
        'limitations': ['22-case development slice, not the sealed evaluation.', 'Queue test serializes one shared model handle; it is not parallel throughput.'],
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (output / 'warm_predictions.jsonl').write_text('\n'.join(json.dumps(row) for row in warm_rows) + '\n', encoding='utf-8')
    (output / 'run.json').write_text(json.dumps({
        'status': 'completed' if benchmark_status == 'MEASURED' else 'failed',
        'finished_at': datetime.now(timezone.utc).isoformat(),
        'arguments': vars(args), 'dataset_sha256': dataset_sha256,
        'package_manifest_sha256': summary['package_manifest_sha256'],
        'protocol_sha256': digest(ROOT / 'docs/reference/USEFULNESS_V2_RUNTIME_BENCHMARK.md'),
    }, indent=2), encoding='utf-8')
    (output / 'protocol.md').write_bytes((ROOT / 'docs/reference/USEFULNESS_V2_RUNTIME_BENCHMARK.md').read_bytes())
    print(json.dumps(summary, indent=2))
    if benchmark_status != 'MEASURED':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
