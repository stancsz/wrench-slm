import json

from wrench.selective_eval import evaluate_local_task
from wrench.selective_policy import decide, format_local_answer, validate_public_action
from wrench.selective_tasks import build_dataset, make_task, public_record
from wrench.pilot_environment import PilotEnvironment
from wrench.pilot_workflow import run_episode
from wrench.selective_runtime import run_local_completion, verify_runtime_observation
from scripts.analyze_selective_workflow import summarize as summarize_workflow


def _gold_predictor(task):
    def predict(record):
        args = dict(task['args'])
        if task['tool'] == 'exec_command' and '__PORT__' in args.get('cmd', ''):
            args['cmd'] = args['cmd'].replace('__PORT__', record['context']['prior_results']['health_url'].split(':')[2].split('/')[0])
        action = json.dumps({'tool': task['tool'], 'args': args})
        return {'action': action, 'raw': action, 'invalid_output': False, 'duration_s': 0.0}
    return predict


def test_selective_dataset_has_fresh_disjoint_families(tmp_path):
    manifest = build_dataset(tmp_path / 'data')
    assert manifest['family_counts'] == {'development': 24, 'evaluation': 120}
    dev = [json.loads(line) for line in (tmp_path / 'data' / 'development.jsonl').read_text(encoding='utf-8').splitlines()]
    evaluation = [json.loads(line) for line in (tmp_path / 'data' / 'evaluation.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(dev) == 120 and len(evaluation) == 600
    assert {row['family_id'] for row in dev}.isdisjoint({row['family_id'] for row in evaluation})
    assert {row['language'] for row in evaluation} == {'en', 'zh'}
    for row in evaluation:
        public = public_record(row)
        assert set(public) == {'prompt', 'context'}
        assert all(key not in json.dumps(public, ensure_ascii=False) for key in ['expected_answer', 'fixture'])


def test_public_policy_rejects_hidden_or_unsafe_actions():
    task = make_task('config', 0, 0, 'test')
    record = public_record(task)
    safe = json.dumps({'tool': 'read_file', 'args': {'path': task['context']['prior_results']['selected_file']}})
    unsafe = json.dumps({'tool': 'read_file', 'args': {'path': '../outside'}})
    command = json.dumps({'tool': 'exec_command', 'args': {'cmd': 'git reset --hard'}})
    assert validate_public_action(record, safe)[0] > 0
    assert validate_public_action(record, unsafe) == (0.0, 'path_not_visible')
    assert validate_public_action(record, command) == (0.0, 'command_outside_contract')
    assert not decide(record, unsafe, 'eligible').accepted


def test_intent_revision_rejects_safe_but_irrelevant_actions():
    task = make_task('git_log', 0, 0, 'test')
    record = public_record(task)
    status = json.dumps({'tool': 'exec_command', 'args': {'cmd': 'git status --short'}})
    assert validate_public_action(record, status)[0] > 0
    assert validate_public_action(record, status, 'intent-v2') == (0.0, 'request_intent_mismatch')
    assert not decide(record, status, 'eligible', 'intent-v2').accepted


def test_runtime_read_shapes_complete_and_other_actions_fallback(tmp_path):
    for kind in ['config', 'lines']:
        task = make_task(kind, 0, 0, 'test')
        row = evaluate_local_task(task, tmp_path / kind, _gold_predictor(task), 'eligible')
        assert row['local_accepted'], (kind, row)
        assert row['local_success'], (kind, row)
        assert row['filesystem_unchanged']
        assert row['runtime_verifier_passed']
    for kind in ['search', 'git_status', 'git_log', 'health', 'draft']:
        task = make_task(kind, 0, 0, 'test')
        row = evaluate_local_task(task, tmp_path / kind, _gold_predictor(task), 'eligible')
        assert row['local_proposal_accepted'], (kind, row)
        assert not row['local_accepted'], (kind, row)
        assert not row['local_success'], (kind, row)
        assert row['fallback_reason'] == 'runtime_action_unsupported', (kind, row)
        assert row['tools'] == []
    for kind in ['ambiguous', 'unsupported', 'missing_tool', 'invalid_range', 'over_budget']:
        task = make_task(kind, 0, 0, 'test')
        row = evaluate_local_task(task, tmp_path / kind, _gold_predictor(task), 'eligible')
        assert not row['local_accepted'], (kind, row)
        assert row['filesystem_unchanged']


def test_local_formatter_only_uses_observation():
    task = make_task('health', 0, 0, 'test')
    record = public_record(task)
    observation = {'call': task, 'executed': True, 'draft_only': False,
                   'output': '{"status":"healthy"}', 'filesystem_unchanged': True}
    answer, reason = format_local_answer(record, observation)
    assert json.loads(answer) == {'answer': 'healthy'}
    assert reason == 'health_answer'


def test_runtime_verifier_has_no_oracle_dependency_and_accepts_gold_free_env():
    source = __import__('wrench.selective_runtime', fromlist=['__file__']).__file__
    source_text = open(source, encoding='utf-8').read()
    assert 'score_answer' not in source_text
    assert 'env.task' not in source_text
    assert 'expected_answer' not in source_text

    task = make_task('config', 0, 0, 'oracle-free')
    record = public_record(task)
    action = json.dumps({'tool': 'read_file', 'args': {'path': task['context']['prior_results']['selected_file']}})

    class GoldFreeEnvironment:
        initial_fingerprint = {'config.json': 'stable'}

        def execute(self, call):
            return {
                'call': call, 'executed': True, 'output': '{"region":"runtime-region"}',
                'filesystem_unchanged': True,
            }

        def fingerprint(self):
            return self.initial_fingerprint

    route = run_local_completion(GoldFreeEnvironment(), record, action, 'eligible', 'intent-v2')
    assert route['route'] == 'local'
    assert json.loads(route['local_answer']) == {'answer': 'runtime-region'}
    assert route['runtime_verifier_passed'] is True


def test_runtime_verifier_rejects_insufficient_observations():
    task = make_task('config', 0, 0, 'verifier')
    record = public_record(task)
    action = json.dumps({'tool': 'read_file', 'args': {'path': task['context']['prior_results']['selected_file']}})
    answer, reason = verify_runtime_observation(
        record, action, {'call': json.loads(action), 'executed': True, 'output': '{"not_region": true}', 'filesystem_unchanged': True},
    )
    assert answer is None
    assert reason == 'verifier_region_field_missing'


def test_runtime_bypass_timeout_and_tool_error_have_explicit_routes(tmp_path):
    task = make_task('config', 0, 0, 'm1')
    record = public_record(task)
    action = json.dumps({'tool': 'read_file', 'args': {'path': task['context']['prior_results']['selected_file']}})

    env = PilotEnvironment(task, tmp_path / 'bypass')
    try:
        bypass = run_local_completion(env, record, action, 'eligible', 'intent-v2', bypass=True)
        assert bypass['route'] == 'fallback'
        assert bypass['fallback_reason'] == 'bypass_operator_switch'
    finally:
        env.close()

    bypass_row = evaluate_local_task(
        task, tmp_path / 'bypass-eval',
        lambda record: (_ for _ in ()).throw(AssertionError('predictor must not run under bypass')),
        'eligible', 'intent-v2', bypass=True,
    )
    assert bypass_row['fallback_reason'] == 'bypass_operator_switch'

    class TimeoutEnvironment:
        initial_fingerprint = {}

        def execute(self, call):
            raise TimeoutError('synthetic local timeout')

        def fingerprint(self):
            return self.initial_fingerprint

    timeout_env = TimeoutEnvironment()
    timeout_env.task = task
    timeout = run_local_completion(timeout_env, record, action, 'eligible', 'intent-v2')
    assert timeout['route'] == 'fallback'
    assert timeout['fallback_reason'] == 'local_timeout'

    class ToolErrorEnvironment(TimeoutEnvironment):
        def execute(self, call):
            return {'call': call, 'executed': False, 'error': 'synthetic tool failure', 'output': '{}'}

    tool_error_env = ToolErrorEnvironment()
    tool_error_env.task = task
    tool_error = run_local_completion(tool_error_env, record, action, 'eligible', 'intent-v2')
    assert tool_error['route'] == 'fallback'
    assert tool_error['fallback_reason'] == 'local_tool_error'


def test_matched_episode_can_finish_locally_without_cloud_call(tmp_path):
    task = make_task('config', 0, 0, 'm1')
    env = PilotEnvironment(task, tmp_path / 'episode')

    class Prediction:
        def to_dict(self):
            action = json.dumps({'tool': 'read_file', 'args': {'path': task['context']['prior_results']['selected_file']}})
            return {'action': action, 'raw': action, 'invalid_output': False, 'duration_s': 0.0}

    class Executor:
        def predict(self, record):
            return Prediction()

    class NoCloud:
        attempts = 0
        tokens = 0
        receipts = []

        def call(self, messages):
            raise AssertionError('cloud must not be called for a verified local completion')

    try:
        result = run_episode(
            env, 'C', NoCloud(), Executor(),
            selective_variant='eligible', selective_revision='intent-v2',
        )
    finally:
        env.close()
    assert result['local_completed'] is True
    assert result['cloud_attempts'] == []
    assert result['success'] is True
    assert result['local_route']['fallback_reason'] is None


def test_workflow_summary_counts_local_runtime_and_zero_provider_cost():
    row = {
        'success': True,
        'filesystem_unchanged': True,
        'usage_complete': True,
        'duration_s': 1.0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'cached_tokens': 0,
        'cloud_attempts': [],
        'tools': [],
        'local_completed': True,
        'local_predict_duration_s': 0.2,
        'local_route_duration_s': 0.3,
        'provider_cost': 0.0,
        'local_route': {
            'local_attempted': True,
            'local_accepted': True,
            'fallback_reason': None,
            'policy_duration_s': 0.01,
            'execution_duration_s': 0.02,
            'format_duration_s': 0.01,
        },
    }
    summary = summarize_workflow([row])
    assert summary['local_successful_coverage'] == 1.0
    assert summary['cloud_tokens_total'] == 0
    assert summary['cost_available'] is True
    assert summary['cost_total'] == 0.0
