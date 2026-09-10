from scripts.pilot_analyze import comparisons


def test_identical_success_does_not_prove_tight_noninferiority():
    rows = []
    for family in range(24):
        for instance in range(5):
            for arm in ['A', 'B', 'C']:
                rows.append({'task_id': f'{family}-{instance}', 'family_id': str(family), 'arm': arm,
                             'success': True, 'duration_s': 1 if arm == 'C' else 2,
                             'prompt_tokens': 100, 'completion_tokens': 20})
    result = comparisons(rows)
    for value in result.values():
        assert value['success_difference'] == 0
        assert value['success_difference_conservative_lower_95'] < -.02
        assert value['duration_s_saving_fraction'] == .5
        assert value['tokens_saving_fraction'] == 0
