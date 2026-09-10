"""Stage an explicitly unapproved adapter package without promoting or publishing."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import TOOLS  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--license', required=True)
    args = parser.parse_args()
    checkpoint = Path(args.checkpoint).resolve()
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT / 'artifacts/model-release'):
        parser.error('Stage packages in artifacts/model-release')
    adapter = json.loads((checkpoint / 'adapter_config.json').read_text(encoding='utf-8'))
    model, revision = 'Qwen/Qwen2.5-0.5B-Instruct', '7ae557604adf67be50417f59c2c2f167def9a775'
    if adapter['base_model_name_or_path'] != model or adapter['revision'] != revision:
        raise ValueError('Unexpected adapter base identity')
    contract = json.loads((checkpoint / 'training_contract.json').read_text(encoding='utf-8'))
    if contract['formatter_sha256'] != digest(ROOT / 'wrench/dataset.py'):
        raise ValueError('Training formatter differs from packaged formatter')
    license_path = Path(args.license)
    if digest(license_path) != '832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e':
        raise ValueError('Expected the verified upstream license for the pinned base')
    output.mkdir(parents=True, exist_ok=False)
    weights = output / 'weights'
    weights.mkdir()
    names = ['adapter_model.safetensors', 'adapter_config.json', 'tokenizer.json', 'tokenizer_config.json',
             'special_tokens_map.json', 'vocab.json', 'merges.txt', 'added_tokens.json', 'chat_template.jinja',
             'training_contract.json', 'training_metrics.json']
    for name in names:
        shutil.copyfile(checkpoint / name, weights / name)
    training_receipt = checkpoint.parent / 'run.json'
    if training_receipt.is_file():
        shutil.copyfile(training_receipt, output / 'training_run.json')
    runtime = output / '_wrench_runtime'
    runtime.mkdir()
    (runtime / '__init__.py').write_text('"""Minimal Wrench weight inference runtime."""\n', encoding='utf-8')
    for name in ['dataset.py', 'protocol.py', 'pilot_inference.py', 'weight_inference.py']:
        shutil.copyfile(ROOT / 'wrench' / name, runtime / name)
    (output / 'inference.py').write_text('from _wrench_runtime.weight_inference import main\n\nif __name__ == "__main__":\n    main()\n', encoding='utf-8')
    shutil.copyfile(license_path, output / 'LICENSE-QWEN')
    shutil.copyfile(license_path, output / 'LICENSE')
    (output / 'NOTICE').write_text(
        f'Base model: {model}\nRevision: {revision}\nCopyright 2024 Alibaba Cloud.\n'
        'This package adds Wrench-Pro LoRA weights trained on authored developer tool-call scenarios.\n'
        'Base model weights are a separate dependency and are not included.\n'
        'The tokenizer is redistributed from the base model. See LICENSE-QWEN.\n'
        'The adapter and accompanying Wrench runtime are modifications, not an official Qwen release.\n', encoding='utf-8')
    (output / 'requirements.txt').write_text('transformers==4.57.1\npeft==0.20.0\ntokenizers==0.22.1\nsafetensors==0.6.2\n', encoding='utf-8')
    example = {'prompt': 'Read lines 3 through 5 of src/example.txt.',
               'context': {'os': 'Windows', 'shell': 'PowerShell', 'workdir': '.', 'tools': TOOLS,
                           'resources': [], 'prior_results': {'selected_file': 'src/example.txt'}}}
    (output / 'example.json').write_text(json.dumps(example, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'README.md').write_text(
        '# Wrench-Pro adapter candidate\n\n'
        '**TRAINED CANDIDATE. Release approval and independent evaluation are pending.**\n\n'
        'Proposed package license: Apache-2.0, with upstream attribution retained in NOTICE and LICENSE-QWEN.\n\n'
        'This is a LoRA adapter, not standalone model weights. It requires '
        f'{model} at revision `{revision}`. The first run downloads that exact base.\n\n'
        'Create a Python environment (training used Python 3.14). Install the CUDA build used for training, then the pinned inference dependencies:\n\n'
        '```powershell\npython -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128\n'
        'python -m pip install -r requirements.txt\npython inference.py --input example.json --device cuda\n```\n\n'
        'Input contains `prompt` and available `context`, including tool schemas. Output reports the raw prediction, '
        'validated action, explicit rejection/abstention reason, token counts, and elapsed prediction time. '
        'It returns a proposed tool call or `ROUTER_FALLBACK` and executes no tool.\n\n'
        'Use `--local-files-only` after fetching the base, or `--base-path` with a local copy of the exact pinned base. '
        'The runtime verifies the bundled file checksums before loading. '\
        'CPU mode is available explicitly but requires separate performance validation.\n\n'
        'Intended tasks include file/config reads, line ranges, literal searches, Git inspections, local health reads, '
        'and draft-only writes. Data is authored, not representative production traffic. '
        'No router savings, millisecond latency, or production-service readiness is claimed. '
        'Consult the eventual evaluation report before relying on this candidate.\n', encoding='utf-8')
    manifest = {'status': 'TRAINED CANDIDATE', 'format': 'peft_lora_adapter', 'base_model': model,
                'base_revision': revision, 'source_checkpoint': str(checkpoint.relative_to(ROOT)) if checkpoint.is_relative_to(ROOT) else checkpoint.name,
                'adapter_sha256': digest(weights / 'adapter_model.safetensors'),
                'base_weights_sha256': 'fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe',
                'max_input_tokens': 1536, 'max_new_tokens': 192,
                'sha256': {str(p.relative_to(output)).replace('\\', '/'): digest(p) for p in output.rglob('*') if p.is_file()}}
    (output / 'release_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(output), 'status': manifest['status'], 'adapter_sha256': manifest['adapter_sha256']}, indent=2))


if __name__ == '__main__':
    main()
