"""Verify the actual package using a separate interpreter and explicit base files."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import psutil


CHILD = r'''
import json, os, platform, sys, time
from pathlib import Path
import torch
from _wrench_runtime.weight_inference import load_executor, verify_package
started = time.perf_counter()
root = Path.cwd()
manifest = verify_package(root)
device = sys.argv[2]
if device == 'cuda':
    torch.cuda.reset_peak_memory_stats()
executor = load_executor(root, device=device, local_files_only=True, base_path=sys.argv[1])
load_s = time.perf_counter() - started
example = json.loads((root / 'example.json').read_text(encoding='utf-8'))
first = executor.predict(example)
warm = executor.predict(example)
expected = {'tool': 'read_file', 'args': {'path': 'src/example.txt', 'start_line': 3, 'end_line': 5}}
try:
    correct = not first.invalid_output and not warm.invalid_output and json.loads(first.action) == expected and json.loads(warm.action) == expected
except (ValueError, TypeError):
    correct = False
print(json.dumps({'status': 'passed' if correct else 'failed', 'python': sys.version, 'platform': platform.platform(),
                  'worker_pid': os.getpid(),
                  'sys_prefix': sys.prefix, 'sys_base_prefix': sys.base_prefix,
                  'adapter_sha256': manifest['adapter_sha256'], 'device': device,
                  'load_s': load_s, 'first_prediction': first.to_dict(), 'warm_prediction': warm.to_dict(),
                  'peak_cuda_allocated_bytes': torch.cuda.max_memory_allocated() if device == 'cuda' else None,
                  'peak_cuda_reserved_bytes': torch.cuda.max_memory_reserved() if device == 'cuda' else None,
                  'scope': 'Fresh interpreter, explicit pinned base, two quickstart predictions; no generated tools executed.'}))
sys.exit(0 if correct else 2)
'''


def process_tree_rss(process):
    """Windows venv launchers spawn the real interpreter as a child."""
    try:
        members = [process, *process.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0
    total = 0
    for member in members:
        try:
            total += member.memory_info().rss
        except psutil.NoSuchProcess:
            pass
    return total


def stop_process_tree(process):
    try:
        for descendant in process.children(recursive=True):
            try:
                descendant.kill()
            except psutil.NoSuchProcess:
                pass
        process.kill()
    except psutil.NoSuchProcess:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', required=True)
    parser.add_argument('--python', required=True)
    parser.add_argument('--base-path', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--device', choices=['cuda', 'cpu'], default='cuda')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'verifier_source.py').write_bytes(Path(__file__).read_bytes())
    package = Path(args.package).resolve()
    environment = os.environ.copy()
    environment.update(HF_HOME=str(output / 'empty-hf-cache'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                       PYTHONNOUSERSITE='1', PYTHONPATH='', OMP_NUM_THREADS='4')
    command = [str(Path(args.python).resolve()), '-B', '-X', 'utf8', '-c', CHILD, str(Path(args.base_path).resolve()), args.device]
    started = time.perf_counter()
    peak_rss = 0
    with (output / 'stdout.txt').open('w', encoding='utf-8') as stdout, (output / 'stderr.txt').open('w', encoding='utf-8') as stderr:
        child = subprocess.Popen(command, cwd=package, env=environment, stdout=stdout, stderr=stderr)
        process = psutil.Process(child.pid)
        timed_out = False
        while child.poll() is None:
            if time.perf_counter() - started > 180:
                stop_process_tree(process)
                timed_out = True
                break
            try:
                peak_rss = max(peak_rss, process_tree_rss(process))
            except psutil.NoSuchProcess:
                pass
            time.sleep(.1)
        code = child.wait()
    result = {'process_exit_code': code, 'timed_out': timed_out, 'peak_process_tree_rss_bytes': peak_rss,
              'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'launcher_pid': child.pid, 'rss_scope': 'Sum of launcher and descendant RSS, sampled every 100ms; shared pages may be counted more than once.',
              'wall_s': time.perf_counter() - started, 'package_manifest_sha256': hashlib.sha256((package / 'release_manifest.json').read_bytes()).hexdigest(),
              'environment': {k: environment[k] for k in ['HF_HOME', 'HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'PYTHONNOUSERSITE', 'PYTHONPATH', 'OMP_NUM_THREADS']}}
    lines = (output / 'stdout.txt').read_text(encoding='utf-8').splitlines()
    if lines:
        try:
            result['verification'] = json.loads(lines[-1])
        except ValueError:
            result['output_parse_error'] = True
    result['passed'] = code == 0 and result.get('verification', {}).get('status') == 'passed'
    (output / 'receipt.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['passed']:
        raise SystemExit('Package verification failed; inspect preserved stdout/stderr')


if __name__ == '__main__':
    main()
