"""Train an isolated, bounded Pro LoRA candidate; never touch sidecar weights."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch  # noqa: E402
from peft import LoraConfig, PeftModel, get_peft_model  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

from wrench.sft import sft_train  # noqa: E402

MODEL = 'Qwen/Qwen2.5-0.5B-Instruct'
REVISION = '7ae557604adf67be50417f59c2c2f167def9a775'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', required=True)
    parser.add_argument('--val')
    parser.add_argument('--output', required=True)
    parser.add_argument('--steps', type=int, required=True)
    parser.add_argument('--max-length', type=int, default=1536)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--accumulation', type=int, default=4)
    parser.add_argument('--learning-rate', type=float, default=1e-4)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--checkpoint-every', type=int)
    parser.add_argument('--resume-from', help='Trusted local trainer_state.pt from this pipeline')
    parser.add_argument('--gpu-memory-fraction', type=float, default=1.0)
    parser.add_argument('--initialize-adapter', help='Warm-start trusted adapter weights with a fresh optimizer')
    args = parser.parse_args()
    if not 1 <= args.steps <= 1000:
        parser.error('Each run must have 1..1000 optimizer steps')
    if not 0 < args.gpu_memory_fraction <= 1:
        parser.error('GPU memory fraction must be greater than zero and at most one')
    if args.resume_from and args.initialize_adapter:
        parser.error('Choose either exact resume or adapter initialization, not both')
    output = Path(args.output).resolve()
    artifact_roots = [(ROOT / 'artifacts' / name).resolve() for name in ['usefulness-pilot', 'model-release']]
    if not any(output.is_relative_to(root) and output != root for root in artifact_roots):
        parser.error('Output must be a new subdirectory of artifacts/usefulness-pilot or artifacts/model-release')
    output.mkdir(parents=True, exist_ok=False)
    receipt = {
        'status': 'started', 'started_at': datetime.now(timezone.utc).isoformat(),
        'model_id': MODEL, 'revision': REVISION, 'arguments': vars(args),
        'packages': {name: importlib.metadata.version(name) for name in ['torch', 'transformers', 'peft']},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in ['wrench/sft.py', 'wrench/dataset.py', 'scripts/pilot_train.py']},
        'scope': 'isolated SFT candidate; no serving-model promotion',
    }
    receipt_path = output / 'run.json'
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    for name in receipt['source_sha256']:
        snapshot = output / 'source' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    started = time.perf_counter()
    try:
        torch.manual_seed(args.seed)
        if not torch.cuda.is_available():
            raise RuntimeError('This bounded Pro run requires the CUDA device')
        torch.cuda.set_per_process_memory_fraction(args.gpu_memory_fraction)
        torch.cuda.reset_peak_memory_stats()
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, local_files_only=True)
        base = AutoModelForCausalLM.from_pretrained(
            MODEL, revision=REVISION, local_files_only=True, dtype=torch.bfloat16,
            attn_implementation='sdpa',
        ).to('cuda')
        base.config.use_cache = False
        lora = LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05, task_type='CAUSAL_LM',
            revision=REVISION,
            target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
        )
        if args.initialize_adapter:
            initial = Path(args.initialize_adapter).resolve()
            config = json.loads((initial / 'adapter_config.json').read_text(encoding='utf-8'))
            contract = json.loads((initial / 'training_contract.json').read_text(encoding='utf-8'))
            if config['base_model_name_or_path'] != MODEL or config['revision'] != REVISION:
                raise ValueError('Initial adapter has a different base identity')
            if contract['formatter_sha256'] != receipt['source_sha256']['wrench/dataset.py']:
                raise ValueError('Initial adapter formatter differs from this run')
            vocab_hash = hashlib.sha256(json.dumps(tokenizer.get_vocab(), sort_keys=True).encode()).hexdigest()
            if contract['vocab_sha256'] != vocab_hash or contract['chat_template'] != tokenizer.chat_template:
                raise ValueError('Initial adapter tokenizer differs from this run')
            model = PeftModel.from_pretrained(base, initial, is_trainable=True)
            receipt.update(initial_adapter_sha256=hashlib.sha256((initial / 'adapter_model.safetensors').read_bytes()).hexdigest(),
                           optimizer_reset=True)
        else:
            model = get_peft_model(base, lora)
        receipt['lora'] = model.peft_config['default'].to_dict()
        receipt['trainable_parameters'] = sum(p.numel() for p in model.parameters() if p.requires_grad)
        metrics = sft_train(
            model, tokenizer, args.train, val_path=args.val,
            micro_batch_size=args.batch_size, grad_accum_steps=args.accumulation,
            learning_rate=args.learning_rate, max_steps=args.steps, seed=args.seed,
            max_length=args.max_length, log_every=5, checkpoint_dir=output / 'checkpoint',
            checkpoint_every=args.checkpoint_every, resume_from=args.resume_from,
        )
        receipt.update(status='completed', training=asdict(metrics))
    except Exception as exc:
        receipt.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        receipt['duration_s'] = time.perf_counter() - started
        receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
        if torch.cuda.is_available():
            receipt['peak_allocated_bytes'] = torch.cuda.max_memory_allocated()
        receipt_path.write_text(json.dumps(receipt, indent=2, default=lambda value: sorted(value) if isinstance(value, set) else str(value)), encoding='utf-8')


if __name__ == '__main__':
    main()
