"""Minimal inference entry point copied into the standalone adapter package.

Returns predictions only. This module never executes a generated tool call.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from .pilot_inference import PilotExecutor


def verify_package(root):
    root = Path(root).resolve()
    manifest = json.loads((root / 'release_manifest.json').read_text(encoding='utf-8'))
    for relative, expected in manifest['sha256'].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'Missing or invalid package path: {relative}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Package checksum mismatch: {relative}')
    return manifest


def load_executor(root, *, device='cuda', local_files_only=False, base_path=None):
    root = Path(root).resolve()
    manifest = verify_package(root)
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable. Install the documented CUDA torch build or explicitly choose --device cpu.')
    tokenizer = AutoTokenizer.from_pretrained(root / 'weights', local_files_only=True)
    contract = json.loads((root / 'weights/training_contract.json').read_text(encoding='utf-8'))
    if tokenizer.chat_template != contract['chat_template'] or tokenizer.special_tokens_map != contract['special_tokens']:
        raise ValueError('Packaged tokenizer template or special tokens differ from training')
    if hashlib.sha256(json.dumps(tokenizer.get_vocab(), sort_keys=True).encode()).hexdigest() != contract['vocab_sha256']:
        raise ValueError('Packaged tokenizer vocabulary differs from training')
    if base_path and hashlib.sha256((Path(base_path) / 'model.safetensors').read_bytes()).hexdigest() != manifest['base_weights_sha256']:
        raise ValueError('Local base weights do not match the pinned upstream revision')
    base = AutoModelForCausalLM.from_pretrained(
        base_path or manifest['base_model'], revision=None if base_path else manifest['base_revision'],
        local_files_only=local_files_only, dtype=torch.bfloat16 if device == 'cuda' else torch.float32,
        attn_implementation='sdpa',
    ).to(device)
    model = PeftModel.from_pretrained(base, root / 'weights').eval()
    return PilotExecutor(model, tokenizer, max_input_tokens=manifest['max_input_tokens'], max_new_tokens=manifest['max_new_tokens'])


def main():
    parser = argparse.ArgumentParser(description='Wrench-Pro adapter inference. Produces a proposal; executes no tools.')
    parser.add_argument('--input', required=True, help='JSON file with prompt and context, or - for stdin')
    parser.add_argument('--device', choices=['cuda', 'cpu'], default='cuda')
    parser.add_argument('--local-files-only', action='store_true')
    parser.add_argument('--base-path', help='Optional local copy of the documented exact base revision')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    record = json.load(sys.stdin) if args.input == '-' else json.loads(Path(args.input).read_text(encoding='utf-8'))
    if not isinstance(record.get('prompt'), str) or not isinstance(record.get('context'), dict) or not isinstance(record['context'].get('tools'), list):
        parser.error('Input requires a string prompt and context.tools list')
    executor = load_executor(root, device=args.device, local_files_only=args.local_files_only, base_path=args.base_path)
    print(json.dumps(executor.predict(record).to_dict(), ensure_ascii=False))


if __name__ == '__main__':
    main()
