"""Assess the prespecified family-level uncertainty design before a paid pilot."""

import argparse
import json
import math
from pathlib import Path


def all_success_lower(alpha, families):
    """Conservative lower bound for C-minus-comparator with both rates at one."""
    return alpha ** (1 / families) - 1


def assess(families, comparisons, familywise_alpha, margin, instances, kinds, languages):
    per_comparison_alpha = familywise_alpha / comparisons
    minimum_families = math.ceil(math.log(per_comparison_alpha) / math.log(1 - margin))
    balanced_block = math.lcm(kinds, languages)
    balanced_families = math.ceil(minimum_families / balanced_block) * balanced_block
    return {
        'method': 'Bonferroni family-wise coverage plus the declared all-success exact fallback',
        'input': {
            'families': families,
            'comparisons': comparisons,
            'familywise_alpha': familywise_alpha,
            'margin': margin,
            'instances_per_family': instances,
            'kinds': kinds,
            'languages': languages,
        },
        'current_design': {
            'implemented_per_comparison_alpha': familywise_alpha,
            'implemented_all_success_lower_bound': all_success_lower(familywise_alpha, families),
            'per_comparison_alpha': per_comparison_alpha,
            'familywise_coverage_lower_bound': 1 - comparisons * per_comparison_alpha,
            'all_success_lower_bound': all_success_lower(per_comparison_alpha, families),
            'cases': families * instances,
            'supports_margin': all_success_lower(per_comparison_alpha, families) >= -margin,
        },
        'minimum_design': {
            'minimum_families_without_balance_constraint': minimum_families,
            'balanced_families': balanced_families,
            'cases': balanced_families * instances,
            'all_success_lower_bound': all_success_lower(per_comparison_alpha, balanced_families),
            'balanced_family_block': balanced_block,
            'balanced_families_per_language': balanced_families // languages,
            'balanced_families_per_kind': balanced_families // kinds,
            'familywise_coverage_lower_bound': 1 - comparisons * per_comparison_alpha,
        },
        'decision': 'EXPLORATORY_INCONCLUSIVE' if all_success_lower(per_comparison_alpha, families) < -margin else 'DESIGN_SUPPORTS_DECLARED_MARGIN',
        'limitations': [
            'This is an all-success boundary calculation, not power for a nonzero effect size.',
            'Families are the uncertainty unit; five instances do not create five independent families.',
            'The current 120-family result must not be upgraded by changing the rule after scoring.',
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--families', type=int, default=120)
    parser.add_argument('--comparisons', type=int, default=2)
    parser.add_argument('--familywise-alpha', type=float, default=0.05)
    parser.add_argument('--margin', type=float, default=0.02)
    parser.add_argument('--instances', type=int, default=5)
    parser.add_argument('--kinds', type=int, default=11)
    parser.add_argument('--languages', type=int, default=2)
    parser.add_argument('--output')
    args = parser.parse_args()
    if min(args.families, args.comparisons, args.instances, args.kinds, args.languages) < 1:
        parser.error('counts must be positive')
    if not 0 < args.familywise_alpha < 1 or not 0 < args.margin < 1:
        parser.error('alpha and margin must be between zero and one')
    result = assess(args.families, args.comparisons, args.familywise_alpha, args.margin, args.instances, args.kinds, args.languages)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
