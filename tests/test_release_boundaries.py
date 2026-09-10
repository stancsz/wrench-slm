import json

import pytest

from scripts.release_boundary_data import additions
from wrench.pilot_environment import PilotEnvironment
from wrench.release_data import make_release_task
from wrench.release_eval import outcome_matches


@pytest.mark.parametrize('style', range(12))
def test_new_boundary_labels_execute_exact_inclusive_range(style, tmp_path):
    parents = [make_release_task('lines', 0, 0, 'train', 'boundary-label-test'),
               make_release_task('unsupported', 0, 0, 'train', 'boundary-label-test')]
    candidates = additions(parents)
    group = [r for r in candidates if r['family_id'] == f'boundary-v4-range-style-{style}']
    valid = next(r for r in group if r['kind'] == 'lines')
    env = PilotEnvironment(valid, tmp_path / 'fixture')
    try:
        task = env.task
        call = {'tool': task['tool'], 'args': task['args']}
        assert outcome_matches(task, json.dumps(call), env.execute(call))
        # A full-file call is syntactically valid but must fail the exact range outcome.
        overbroad = {'tool': 'read_file', 'args': {'path': task['args']['path']}}
        assert not outcome_matches(task, json.dumps(overbroad), env.execute(overbroad))
    finally:
        env.close()
    assert sum(r['tool'] == 'fallback' for r in group) == 48
