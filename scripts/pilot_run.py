"""Run fixed-budget development diagnostics or the three-arm real pilot."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
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
from wrench.pilot_workflow import CloudClient, run_episode  # noqa: E402
from wrench.protocol import prediction_matches_target  # noqa: E402

MODEL = 'Qwen/Qwen2.5-0.5B-Instruct'
REVISION = '7ae557604adf67be50417f59c2c2f167def9a775'
DATA = ROOT / 'artifacts/archive/data/pilots/authored-developer-v1'
CANDIDATE = ROOT / 'artifacts/usefulness-pilot/pro-candidate-v1/checkpoint'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_tasks(split):
    manifest = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
    path = DATA / f'{split}.jsonl'
    if digest(path) != manifest['splits'][split]['sha256']:
        raise ValueError('Frozen dataset checksum mismatch')
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def load_base():
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, local_files_only=True, dtype=torch.bfloat16, attn_implementation='sdpa').to('cuda').eval()
    return model, tokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['development', 'smoke', 'evaluation'], required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT / 'artifacts/usefulness-pilot'):
        parser.error('Output must be inside artifacts/usefulness-pilot')
    output.mkdir(parents=True, exist_ok=False)
    sources = ['wrench/pilot_tasks.py', 'wrench/pilot_environment.py', 'wrench/pilot_workflow.py', 'wrench/pilot_inference.py', 'wrench/dataset.py', 'wrench/protocol.py', 'scripts/pilot_run.py']
    meta = {'status': 'running', 'phase': args.phase, 'started_at': datetime.now(timezone.utc).isoformat(),
            'model_id': MODEL, 'revision': REVISION, 'adapter_sha256': digest(CANDIDATE / 'adapter_model.safetensors'),
            'candidate_checkpoint': str(CANDIDATE), 'platform': platform.platform(), 'python': sys.version,
            'packages': {name: importlib.metadata.version(name) for name in ['torch', 'transformers', 'peft', 'numpy']},
            'protocol_sha256': digest(ROOT / 'docs/reference/USEFULNESS_PILOT_PROTOCOL_V1.md'),
            'source_sha256': {name: digest(ROOT / name) for name in sources},
            'dataset_manifest_sha256': digest(DATA / 'manifest.json'),
            'hardware': torch.cuda.get_device_name(0), 'max_input_tokens': 1536, 'max_new_tokens': 192, 'decoding': 'greedy_unconstrained_then_strict_validation'}
    (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    (output / 'protocol.md').write_bytes((ROOT / 'docs/reference/USEFULNESS_PILOT_PROTOCOL_V1.md').read_bytes())
    for name in sources:
        snapshot = output / 'source' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    started = time.perf_counter()
    try:
        base, tokenizer = load_base()
        if args.phase == 'development':
            batches = [('base', 'development'), ('candidate', 'development'), ('candidate', 'calibration')]
            executor = PilotExecutor(base, tokenizer, max_new_tokens=192)
            with (output / 'predictions.jsonl').open('w', encoding='utf-8') as file:
                for arm, split in batches:
                    if arm == 'candidate' and not isinstance(executor.model, PeftModel):
                        executor = PilotExecutor(PeftModel.from_pretrained(base, CANDIDATE).eval(), tokenizer, max_new_tokens=192)
                    for index, task in enumerate(read_tasks(split)):
                        prediction = executor.predict(public_record(task))
                        row = {'id': task['id'], 'family_id': task['family_id'], 'kind': task['kind'], 'arm': arm, 'split': split,
                               **prediction.to_dict(), 'exact': prediction_matches_target(prediction.action, task)}
                        file.write(json.dumps(row, ensure_ascii=False) + '\n')
                        file.flush()
                        if (index + 1) % 10 == 0:
                            print(f'[{arm}/{split}] {index + 1}/80', flush=True)
        else:
            executor = PilotExecutor(PeftModel.from_pretrained(base, CANDIDATE).eval(), tokenizer, max_new_tokens=192)
            tasks = read_tasks('development' if args.phase == 'smoke' else 'evaluation')
            if args.phase == 'smoke':
                tasks = [next(task for task in tasks if task['kind'] == 'config')]
            rng = random.Random(20260909)
            rng.shuffle(tasks)
            client = CloudClient(output / 'cloud', max_attempts=12 if args.phase == 'smoke' else 1080)
            (output / 'fixtures').mkdir()
            (output / 'schedule.json').write_text(json.dumps([t['id'] for t in tasks], indent=2), encoding='utf-8')
            # One unscored development input warms local inference before any timed episode.
            executor.predict(public_record(read_tasks('development')[0]))
            with (output / 'episodes.jsonl').open('w', encoding='utf-8') as file:
                for index, task in enumerate(tasks):
                    env = PilotEnvironment(task, output / 'fixtures' / task['id'])
                    arms = ['A', 'B', 'C']
                    rng.shuffle(arms)
                    try:
                        for arm in arms:
                            result = run_episode(env, arm, client, executor)
                            result['fixture_fingerprint'] = env.initial_fingerprint
                            file.write(json.dumps(result, ensure_ascii=False) + '\n')
                            file.flush()
                            print(f'[{index + 1}/{len(tasks)} {arm}] success={result["success"]} time={result["duration_s"]:.2f}s requests={len(result["cloud_attempts"])}', flush=True)
                            if result.get('accounting_stop'):
                                raise RuntimeError('Stopped on incomplete accounting or budget limit; inspect last episode')
                            if not result['filesystem_unchanged']:
                                raise RuntimeError('Fixture state changed unexpectedly')
                    finally:
                        env.close()
            meta.update(cloud_attempts=client.attempts, reported_cloud_tokens=client.tokens)
        meta['status'] = 'completed'
    except Exception as exc:
        meta.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        meta['duration_s'] = time.perf_counter() - started
        meta['finished_at'] = datetime.now(timezone.utc).isoformat()
        (output / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
