import json
from types import SimpleNamespace

from wrench.pilot_environment import PilotEnvironment
from wrench.pilot_tasks import make_task, public_record
from wrench.pilot_workflow import run_episode, rules_predict


class FakeCloud:
    """Harness-only test double. It is never used by scripts/pilot_run.py."""
    def __init__(self, task):
        self.attempts = 0
        self.receipts = []
        self.task = task
        self.messages = []

    def call(self, messages):
        self.messages.append(json.loads(json.dumps(messages)))
        if any(m['role'] == 'tool' or 'Preliminary local observation;' in str(m.get('content')) for m in messages):
            message = {'role': 'assistant', 'content': json.dumps({'answer': self.task['expected_answer']})}
            reason = 'stop'
        else:
            message = {'role': 'assistant', 'tool_calls': [{'id': 'test-call', 'type': 'function', 'function': {'name': self.task['tool'], 'arguments': json.dumps(self.task['args'])}}]}
            reason = 'tool_calls'
        body = {'choices': [{'message': message, 'finish_reason': reason}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 5}}
        receipt = {'attempt': self.attempts, 'accounted_tokens': 15, 'response': body}
        self.receipts.append(receipt)
        self.attempts += 1
        return body, receipt


def test_matched_real_tools_and_all_usage_counted(tmp_path):
    task = make_task('config', 0, 1, 'harness')
    env = PilotEnvironment(task, tmp_path / 'fixture')
    try:
        for arm, count in [('A', 2), ('B', 1), ('C', 1)]:
            client = FakeCloud(task)
            raw = json.dumps({'tool': task['tool'], 'args': task['args']})
            executor = SimpleNamespace(predict=lambda record: SimpleNamespace(to_dict=lambda: {'action': raw, 'raw': raw, 'invalid_output': False, 'duration_s': 0.0}))
            result = run_episode(env, arm, client, executor)
            assert result['success'] and len(result['cloud_attempts']) == count
            assert result['prompt_tokens'] == count * 10
            assert result['completion_tokens'] == count * 5
            assert task['expected_answer'] not in json.dumps(client.messages[0][:2])
            assert all('fixture' not in m.get('content', '') for m in client.messages[0][:2])
        assert env.fingerprint() == env.initial_fingerprint
    finally:
        env.close()


def test_rules_do_not_use_private_labels():
    task = make_task('config', 0, 1, 'harness')
    record = public_record(task)
    first = rules_predict(record)
    task.update(kind='git_log', tool='exec_command', args={'cmd': 'git log -1 --format=%s'}, expected_answer='bad')
    assert rules_predict(public_record(task)) == first


def test_failed_transport_keeps_episode_and_unknown_usage(tmp_path):
    task = make_task('config', 0, 1, 'harness')
    env = PilotEnvironment(task, tmp_path / 'fixture')
    client = FakeCloud(task)

    def fail(messages):
        client.attempts += 1
        client.receipts.append({'error': 'timeout'})
        raise TimeoutError('timeout')

    client.call = fail
    try:
        result = run_episode(env, 'A', client)
        assert not result['success']
        assert result['cloud_attempts'] == [0]
        assert result['prompt_tokens'] is None and result['accounting_stop']
    finally:
        env.close()
