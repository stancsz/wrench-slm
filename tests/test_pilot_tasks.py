import json

import pytest

from wrench.pilot_environment import PilotEnvironment, score_answer
from wrench.pilot_tasks import TEMPLATES, build_dataset, make_task, public_record


def test_partition_and_private_context(tmp_path):
    path = tmp_path / 'dataset'
    manifest = build_dataset(path)
    assert {k: v['tasks'] for k, v in manifest['splits'].items()} == {'train': 640, 'development': 80, 'calibration': 80, 'evaluation': 120}
    all_families = set()
    for split in manifest['splits']:
        records = [json.loads(line) for line in (path / f'{split}.jsonl').read_text(encoding='utf-8').splitlines()]
        families = {r['family_id'] for r in records}
        assert not all_families & families
        all_families |= families
        for task in records:
            public = public_record(task)
            assert set(public) == {'prompt', 'context'}
            if task['kind'] == 'config':
                assert task['expected_answer'] not in json.dumps(public)


@pytest.mark.parametrize('kind', list(TEMPLATES))
def test_real_fixture_target_operations(kind, tmp_path):
    task = make_task(kind, 0, 0, 'test')
    env = PilotEnvironment(task, tmp_path / kind)
    try:
        receipts = [] if kind == 'ambiguous' else [env.execute({'tool': env.task['tool'], 'args': env.task['args']})]
        assert all(not r.get('error') for r in receipts), receipts
        assert score_answer(env.task, json.dumps({'answer': task['expected_answer']}), receipts)
        assert not score_answer(env.task, json.dumps({'answer': 'wrong'}), receipts)
        assert env.fingerprint() == env.initial_fingerprint
    finally:
        env.close()


def test_escape_and_mutation_are_not_executed(tmp_path):
    env = PilotEnvironment(make_task('config', 0, 1, 'test'), tmp_path / 'fixture')
    try:
        for call in [
            {'tool': 'read_file', 'args': {'path': '../outside'}},
            {'tool': 'exec_command', 'args': {'cmd': 'git reset --hard'}},
            {'tool': 'exec_command', 'args': {'cmd': 'git status --short; rm -rf .'}},
            {'tool': 'exec_command', 'args': {'cmd': 'rg -l --fixed-strings -- x ../'}},
            {'tool': 'exec_command', 'args': {'cmd': 'curl --silent --show-error --max-time 3 https://example.com/health'}},
        ]:
            result = env.execute(call)
            assert not result['executed'] and result.get('error')
        assert env.fingerprint() == env.initial_fingerprint
    finally:
        env.close()


def test_correct_guess_without_supporting_observation_fails(tmp_path):
    task = make_task('config', 0, 2, 'test')
    env = PilotEnvironment(task, tmp_path / 'fixture')
    try:
        wrong_read = env.execute({'tool': 'read_file', 'args': {'path': 'configs/other.json'}})
        assert not score_answer(task, json.dumps({'answer': task['expected_answer']}), [wrong_read])
    finally:
        env.close()
