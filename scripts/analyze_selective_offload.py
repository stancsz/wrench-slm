"""Summarize selective local receipts with family-clustered bootstrap intervals."""

import argparse
import json
import random
from pathlib import Path


def percentile(values, fraction):
    values = sorted(values)
    index = (len(values) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def family_bootstrap(rows, samples=20_000, seed=20260910):
    families = {}
    for row in rows:
        families.setdefault(row['family_id'], []).append(row)
    blocks = list(families.values())
    rng = random.Random(seed)
    coverage = []
    useful = []
    precision = []
    for _ in range(samples):
        draw = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        drawn = [row for block in draw for row in block]
        accepted = sum(row['local_accepted'] for row in drawn)
        successful = sum(row['local_success'] for row in drawn)
        total = len(drawn)
        coverage.append(accepted / total if total else 0.0)
        useful.append(successful / total if total else 0.0)
        precision.append(successful / accepted if accepted else 0.0)
    return {
        'families': len(blocks),
        'instances': len(rows),
        'bootstrap_samples': samples,
        'seed': seed,
        'accepted_coverage_95pct': [percentile(coverage, 0.025), percentile(coverage, 0.975)],
        'useful_coverage_95pct': [percentile(useful, 0.025), percentile(useful, 0.975)],
        'accepted_precision_95pct': [percentile(precision, 0.025), percentile(precision, 0.975)],
        'note': 'Intervals resample family blocks, not individual instances; they are exploratory uncertainty summaries.',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.rows).read_text(encoding='utf-8').splitlines() if line.strip()]
    result = family_bootstrap(rows)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
