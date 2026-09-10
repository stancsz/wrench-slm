"""Build isolated authored data for model weight preparation."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.release_data import build_release_data  # noqa: E402


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--version', default='release-authoring-v1')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT / 'data' / 'pilots'):
        parser.error('Use a new directory under data/pilots')
    print(json.dumps(build_release_data(output, version=args.version), indent=2))
