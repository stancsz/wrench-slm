"""Development-only counterfactuals after the step-100 quickstart failure.

No sealed evaluation inputs are read. Derivatives keep their parent family IDs.
"""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.pilot_tasks import TOOLS  # noqa: E402


def main():
    data = ROOT / 'data/pilots/release-authoring-v1'
    rows = [json.loads(line) for line in (data / 'development.jsonl').read_text(encoding='utf-8').splitlines()]
    probes = []
    for kind in ['lines', 'draft', 'search', 'git_status', 'git_log', 'health']:
        for language in ['en', 'zh']:
            row = next(r for r in rows if r['kind'] == kind and r['language'] == language)
            for variant in ['empty_resources', 'minimal_context', 'reordered_tools']:
                probe = json.loads(json.dumps(row))
                probe['id'] += '-probe-' + variant
                probe['source'] = 'development_counterfactual_of_' + row['id']
                if variant == 'empty_resources':
                    probe['context']['resources'] = []
                elif variant == 'minimal_context':
                    probe['context'] = {k: v for k, v in probe['context'].items() if k in ['tools', 'prior_results']}
                else:
                    probe['context']['tools'].reverse()
                probes.append(probe)
    probes.append({
        'id': 'documented-quickstart-v1', 'family_id': 'documented-quickstart', 'kind': 'lines', 'language': 'en',
        'source': 'documented_development_example', 'prompt': 'Read lines 3 through 5 of src/example.txt.',
        'context': {'os': 'Windows', 'shell': 'PowerShell', 'workdir': '.', 'tools': TOOLS, 'resources': [],
                    'prior_results': {'selected_file': 'src/example.txt'}},
        'tool': 'read_file', 'args': {'path': 'src/example.txt', 'start_line': 3, 'end_line': 5},
        'fixture': {'files': {'src/example.txt': 'one\ntwo\nthree\nfour\nfive\nsix\n'}, 'git': False, 'health': None},
        'expected_answer': ['three', 'four', 'five'],
    })
    output = ROOT / 'data/pilots/context-development-v1'
    output.mkdir(parents=True, exist_ok=False)
    path = output / 'development.jsonl'
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in probes), encoding='utf-8')
    manifest = {'version': 'context-development-v1', 'purpose': 'Additional development diagnostics, not a sealed test.',
                'parent_data': str(data), 'splits': {'development': {'tasks': len(probes),
                'families': len({r['family_id'] for r in probes}), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
