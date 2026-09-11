"""Build the fresh selective-offload development and evaluation data."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wrench.selective_tasks import build_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--campaign', default='selective-offload-v1')
    args = parser.parse_args()
    manifest = build_dataset(Path(args.output), campaign=args.campaign)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
