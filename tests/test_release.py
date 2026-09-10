import json

import pytest

from wrench.pilot_environment import PilotEnvironment
from wrench.pilot_inference import validate_prediction
from wrench.protocol import ROUTER_FALLBACK
from wrench.release_data import WORDING, build_release_data, make_release_task
from wrench.release_eval import outcome_matches, quality_gates, summarize


@pytest.mark.parametrize('kind', list(WORDING))
@pytest.mark.parametrize('template', [0, 2, 4, 5])
def test_release_labels_have_real_outcomes(kind, template, tmp_path):
    task = make_release_task(kind, template, 0, 'development', 'label-audit')
    with_env = PilotEnvironment(task, tmp_path / 'fixture')
    try:
        task = with_env.task
        if task['tool'] == 'fallback':
            assert outcome_matches(task, ROUTER_FALLBACK, None)
            return
        call = {'tool': task['tool'], 'args': task['args']}
        action = json.dumps(call)
        assert not validate_prediction(action, task['context']['tools'])[1]
        receipt = with_env.execute(call)
        assert outcome_matches(task, action, receipt), receipt
    finally:
        with_env.close()


def test_range_outcome_rejects_superset(tmp_path):
    task = make_release_task('lines', 0, 0, 'development', 'range-audit')
    env = PilotEnvironment(task, tmp_path / 'fixture')
    call = {'tool': 'read_file', 'args': {'path': task['args']['path']}}
    try:
        receipt = env.execute(call)
        assert receipt['executed']
        assert not outcome_matches(task, json.dumps(call), receipt)
    finally:
        env.close()


def test_release_split_isolation(tmp_path):
    manifest = build_release_data(tmp_path / 'dataset')
    assert manifest['cross_split_families'] == manifest['cross_split_exact_inputs'] == 0
    assert manifest['splits']['train']['tasks'] == 1408
    with pytest.raises(FileExistsError):
        build_release_data(tmp_path / 'dataset')


def test_summary_counts_invalid_fallback_and_failure():
    common = dict(family_id='a', kind='ambiguous', language='en', expected_fallback=True,
                  action=ROUTER_FALLBACK, duration_s=1.0, execution_checked=True, execution=None)
    rows = [{**common, 'exact': True, 'invalid_output': False, 'reason': 'model_abstention', 'outcome_correct': True},
            {**common, 'exact': False, 'invalid_output': True, 'reason': 'argument_type', 'outcome_correct': False}]
    result = summarize(rows)
    assert result['exact_rate'] == result['fallback_exact_rate'] == result['raw_protocol_valid_rate'] == .5
    assert result['families'] == 1
    assert not all(quality_gates(result).values())


def test_all_fallback_cannot_pass_release_gates():
    rows = []
    for kind in WORDING:
        expected_fallback = kind in {'ambiguous', 'unsupported', 'missing_tool', 'invalid_range'}
        rows.append(dict(family_id=kind, kind=kind, language='en', expected_fallback=expected_fallback,
                         action=ROUTER_FALLBACK, duration_s=1., execution_checked=True, execution=None,
                         exact=expected_fallback, invalid_output=False, reason='model_abstention',
                         outcome_correct=expected_fallback))
    gates = quality_gates(summarize(rows))
    assert gates['raw_protocol']
    assert not gates['routine_exact'] and not gates['useful_coverage'] and not gates['routine_outcomes']
