"""Freeze one selective policy only after its development gate passes."""

import argparse
import hashlib
import json
from pathlib import Path

INELIGIBLE_KINDS = {'ambiguous', 'unsupported', 'missing_tool', 'invalid_range', 'over_budget'}
ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True)
    parser.add_argument('--protocol', required=True)
    parser.add_argument('--data', required=True)
    parser.add_argument('--policy', required=True)
    parser.add_argument('--runtime', default='wrench/selective_runtime.py')
    parser.add_argument('--revision', default='v1')
    parser.add_argument('--package', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    summary_path = Path(args.summary).resolve()
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    if summary.get('status') != 'completed' or summary.get('split') != 'development':
        raise SystemExit('Only a completed development summary can be frozen')
    if summary.get('variant') != args.policy:
        raise SystemExit('Summary variant does not match selected policy')
    if summary.get('accepted', 0) <= 0:
        raise SystemExit('Development policy has no accepted local slice')
    if summary.get('accepted_error_rate') != 0.0 or summary.get('unexpected_mutations') != 0:
        raise SystemExit('Development policy failed local correctness or mutation gate')
    for kind in INELIGIBLE_KINDS:
        if summary.get('by_kind', {}).get(kind, {}).get('accepted', 0) != 0:
            raise SystemExit(f'Policy accepted an ineligible {kind} case')
    protocol = Path(args.protocol).resolve()
    runtime = Path(args.runtime).resolve()
    data = Path(args.data).resolve()
    package = Path(args.package).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f'Output exists: {output}')
    result = {
        'status': 'FROZEN_FOR_HELD_OUT_EVALUATION',
        'policy': args.policy,
        'revision': args.revision,
        'development_summary': str(summary_path),
        'development_summary_sha256': digest(summary_path),
        'development_dataset_sha256': summary['dataset_sha256'],
        'evaluation_dataset_sha256': digest(data / 'evaluation.jsonl'),
        'data_manifest_sha256': digest(data / 'manifest.json'),
        'protocol_sha256': digest(protocol),
        'policy_source_sha256': digest(ROOT / 'wrench/selective_policy.py'),
        'runtime_source_sha256': digest(runtime),
        'runtime_source': str(runtime),
        'package_manifest_sha256': digest(package / 'release_manifest.json'),
        'adapter_sha256': summary['model_source']['adapter_sha256'],
        'base_revision': summary['model_source']['base_revision'],
        'development_gate': {
            'accepted': summary['accepted'],
            'tasks': summary['tasks'],
            'accepted_precision': summary['accepted_precision'],
            'accepted_error_rate': summary['accepted_error_rate'],
            'unexpected_mutations': summary['unexpected_mutations'],
            'ineligible_kinds_accepted': 0,
        },
        'scope': 'Selective local policy only; no cloud or production authorization',
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
