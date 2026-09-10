import json

import pytest

from scripts.release_context_data import change_range, derive
from wrench.pilot_environment import PilotEnvironment
from wrench.release_data import make_release_task
from wrench.release_eval import outcome_matches


@pytest.mark.parametrize('kind', ['lines', 'invalid_range', 'config', 'ambiguous'])
@pytest.mark.parametrize('template', range(4))
def test_contrast_pairs_preserve_family_and_valid_effects(kind, template, tmp_path):
    source = make_release_task(kind, template, 1, 'train', 'contrast-test')
    rows = derive(source)
    for index, task in enumerate(rows):
        assert task['family_id'] == source['family_id']
        env = PilotEnvironment(task, tmp_path / str(index))
        try:
            if task['tool'] == 'fallback':
                if task['kind'] == 'ambiguous':
                    assert not task['context']['prior_results']
                continue
            call = {'tool': task['tool'], 'args': task['args']}
            assert outcome_matches(env.task, json.dumps(call), env.execute(call))
            if task['kind'] == 'config' and task['context']['prior_results'].get('selected_service'):
                selected = next(r for r in task['context']['resources'] if r['service'] == task['context']['prior_results']['selected_service'])
                assert task['args']['path'] == selected['config']
        finally:
            env.close()


def test_range_pair_replaces_both_identical_bounds_and_keeps_path():
    row = {'id': 'test', 'prompt': 'Read configs/0123456789.txt, inclusive lines 12 through 12.'}
    change_range(row, 0, 12)
    assert row['prompt'] == 'Read configs/0123456789.txt, inclusive lines 0 through 12.'
