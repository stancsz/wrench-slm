"""Create a fresh context guard after context-development-v1 is retired."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.release_data import make_release_task  # noqa: E402


def main():
    probes = []
    for kind in ['lines', 'draft', 'search', 'git_status', 'git_log', 'health']:
        for language, template in [('en', 0), ('zh', 2)]:
            row = make_release_task(kind, template, 50 + len(probes), 'development', 'context-guard-v2')
            for variant in ['empty_resources', 'minimal_context', 'reordered_tools']:
                probe = json.loads(json.dumps(row))
                probe['id'] = f"context-guard-v2-{kind}-{language}-{variant}"
                probe['family_id'] = f"context-guard-v2-{kind}-{language}"
                probe['source'] = 'fresh_context_guard_v2'
                if variant == 'empty_resources':
                    probe['context']['resources'] = []
                elif variant == 'minimal_context':
                    probe['context'] = {key: value for key, value in probe['context'].items()
                                        if key in {'tools', 'prior_results'}}
                else:
                    probe['context']['tools'].reverse()
                probes.append(probe)
    quickstart = make_release_task('lines', 0, 99, 'development', 'context-guard-v2')
    quickstart['id'] = 'context-guard-v2-documentation-example'
    quickstart['family_id'] = 'context-guard-v2-documentation-example'
    quickstart['source'] = 'fresh_context_guard_v2'
    quickstart['prompt'] = 'Read lines 2 through 4 of docs/context-example.txt.'
    quickstart['args'] = {'path': 'docs/context-example.txt', 'start_line': 2, 'end_line': 4}
    quickstart['fixture']['files'] = {'docs/context-example.txt': 'zero\none\ntwo\nthree\nfour\n'}
    quickstart['expected_answer'] = ['one', 'two', 'three']
    quickstart['context']['resources'] = []
    quickstart['context']['prior_results'] = {'selected_file': 'docs/context-example.txt'}
    probes.append(quickstart)
    output = ROOT / 'data/pilots/context-development-v2'
    output.mkdir(parents=True, exist_ok=False)
    path = output / 'development.jsonl'
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in probes), encoding='utf-8')
    manifest = {
        'version': 'context-development-v2',
        'purpose': 'Fresh context guard after context-development-v1 was used to guide training; not a sealed test.',
        'source': 'Independently generated values and prompts; no V1 probe rows imported.',
        'splits': {'development': {
            'tasks': len(probes), 'families': len({row['family_id'] for row in probes}),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        }},
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'generator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
