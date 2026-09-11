"""Matched native-tool cloud workflows with bounded calls and raw receipts."""

import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .pilot_environment import score_answer
from .public_helper import rules_predict
from .pilot_tasks import TOOLS, public_record
from .protocol import ROUTER_FALLBACK, prediction_matches_target

SYSTEM = '''Complete the user's developer task using the available tools and context.
Do not invent file contents or tool results. If the service/file cannot be identified because necessary information is missing, return {"answer":"NEEDS_CLARIFICATION"}.
Return the final result as exactly one JSON object with an "answer" field and no prose or markdown. For a value or commit subject, answer is the exact string. For a line range, answer is an array of lines in order. For matching or dirty filenames, answer is an array of workspace-relative paths. For a proposed write, submit write_file and then answer "DRAFT_ONLY". Never apply writes.
If a preliminary local observation is supplied, verify that its call matches the task. Use it if sufficient. If it is incorrect or insufficient, request the correct tool. The same instructions and tools apply with or without a preliminary observation.'''


class AccountingError(RuntimeError):
    pass


class CloudClient:
    def __init__(self, directory, max_attempts, max_tokens=3_000_000, *,
                 endpoint='http://127.0.0.1:4000/v1/chat/completions',
                 model='minimax/minimax-m3', timeout_s=45,
                 max_request_bytes=24_000, admission_input_tokens=32_768,
                 max_output_tokens=384):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_attempts, self.max_tokens = max_attempts, max_tokens
        self.endpoint = endpoint
        self.model = model
        self.timeout_s = timeout_s
        self.max_request_bytes = max_request_bytes
        self.admission_input_tokens = admission_input_tokens
        self.max_output_tokens = max_output_tokens
        self.attempts = 0
        self.tokens = 0
        self.receipts = []

    def call(self, messages):
        if self.attempts >= self.max_attempts or self.tokens + self.admission_input_tokens + self.max_output_tokens > self.max_tokens:
            raise AccountingError('Predeclared cloud budget exhausted')
        payload = {'model': self.model, 'messages': messages,
                   'tools': [{'type': 'function', 'function': t} for t in TOOLS],
                   'temperature': 0, 'max_tokens': self.max_output_tokens, 'stream': False, 'tool_choice': 'auto'}
        raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        if len(raw) > self.max_request_bytes:
            raise AccountingError('Request exceeds frozen body budget')
        index = self.attempts
        self.attempts += 1
        receipt = {'attempt': index, 'request': payload, 'started_at_unix': time.time()}
        file = self.directory / f'{index:05d}.json'
        file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
        started = time.perf_counter()
        try:
            request = Request(self.endpoint, data=raw, headers={'Content-Type': 'application/json'})
            with urlopen(request, timeout=self.timeout_s) as response:
                body = json.load(response)
                receipt.update(http_status=response.status, request_id=response.headers.get('x-request-id'), response=body)
            if body.get('_cheap_plus_telemetry') or body.get('model') != self.model:
                raise AccountingError('Unexpected model or compound routing')
            usage = body.get('usage', {})
            if not all(isinstance(usage.get(k), int) and usage[k] >= 0 for k in ['prompt_tokens', 'completion_tokens']):
                raise AccountingError('Provider token usage is unavailable')
            receipt['accounted_tokens'] = usage['prompt_tokens'] + usage['completion_tokens']
            self.tokens += receipt['accounted_tokens']
            return body, receipt
        except Exception as exc:
            receipt['error'] = f'{type(exc).__name__}: {exc}'
            if isinstance(exc, HTTPError):
                receipt['http_status'] = exc.code
            raise
        finally:
            receipt['duration_s'] = time.perf_counter() - started
            self.receipts.append(receipt)
            file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')


def run_episode(env, arm, client, executor=None, selective_variant=None,
                selective_revision='v1', bypass_local=False):
    task = env.task
    record = public_record(task)
    context = dict(record['context'])
    context.pop('tools')  # Native tool schemas carry identical information separately.
    messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': record['prompt'] + '\nAvailable context: ' + json.dumps(context)}]
    result = {'task_id': task['id'], 'family_id': task['family_id'], 'kind': task['kind'], 'language': task['language'], 'arm': arm,
              'tools': [], 'cloud_attempts': [], 'prediction': None, 'final': '', 'started_at_unix': time.time(),
              'speculation_supplied': False, 'cloud_tool_request_turns': 0,
              'local_completed': False, 'local_predict_duration_s': 0.0,
              'local_route_duration_s': 0.0}
    initial_attempt = client.attempts
    started = time.perf_counter()
    cloud_required = True
    try:
        if arm in ['B', 'C']:
            if selective_variant is not None and bypass_local:
                action = ROUTER_FALLBACK
                result['prediction'] = {
                    'raw': action, 'action': action, 'invalid_output': False,
                    'duration_s': 0.0,
                }
            elif arm == 'B':
                pred_start = time.perf_counter()
                action = rules_predict(record)
                result['prediction'] = {'raw': action, 'action': action, 'invalid_output': False, 'duration_s': time.perf_counter() - pred_start}
                result['local_predict_duration_s'] = result['prediction']['duration_s']
            else:
                result['prediction'] = executor.predict(record).to_dict()
                action = result['prediction']['action']
                result['local_predict_duration_s'] = result['prediction'].get('duration_s', 0.0)
            if selective_variant is not None:
                from .selective_runtime import run_local_completion

                local = run_local_completion(
                    env, record, action, selective_variant, selective_revision,
                    bypass=bypass_local,
                )
                result['local_route'] = local
                result['local_route_duration_s'] = local['duration_s']
                result['tools'].extend(local['tools'])
                if local['route'] == 'local':
                    result['final'] = local['local_answer']
                    result['local_completed'] = True
                    cloud_required = False
                elif local['tools'] and not local['tools'][0].get('error'):
                    observation = local['tools'][0]
                    envelope = {'call': observation['call'], 'observation': observation['output'], 'draft_only': observation['draft_only']}
                    messages.append({'role': 'user', 'content': 'Preliminary local observation; verify alignment before using:\n' + json.dumps(envelope)})
                    result['speculation_supplied'] = True
            elif action != ROUTER_FALLBACK:
                observation = env.execute(json.loads(action))
                observation['speculative'] = True
                result['tools'].append(observation)
                if not observation.get('error'):
                    envelope = {'call': observation['call'], 'observation': observation['output'], 'draft_only': observation['draft_only']}
                    messages.append({'role': 'user', 'content': 'Preliminary local observation; verify alignment before using:\n' + json.dumps(envelope)})
                    result['speculation_supplied'] = True
        if cloud_required:
            for turn in range(3):
                response, receipt = client.call(messages)
                result['cloud_attempts'].append(receipt['attempt'])
                choice = response['choices'][0]
                message = choice['message']
                calls = message.get('tool_calls') or []
                if choice.get('finish_reason') == 'length':
                    result['error'] = 'cloud_output_budget'
                    break
                if not calls:
                    result['final'] = message.get('content') or ''
                    break
                result['cloud_tool_request_turns'] += 1
                if len(calls) > 2:
                    result['error'] = 'tool_call_count_budget'
                    break
                messages.append({'role': 'assistant', 'content': message.get('content'), 'tool_calls': calls})
                for call in calls:
                    try:
                        action = {'tool': call['function']['name'], 'args': json.loads(call['function']['arguments'])}
                        observation = env.execute(action)
                    except Exception as exc:  # noqa: BLE001
                        observation = {'call': call, 'executed': False, 'draft_only': False, 'error': str(exc), 'output': json.dumps({'error': str(exc)}), 'duration_s': 0, 'filesystem_unchanged': env.fingerprint() == env.initial_fingerprint}
                    observation['speculative'] = False
                    result['tools'].append(observation)
                    messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': observation['output']})
            else:
                result['error'] = 'cloud_turn_budget'
    except Exception as exc:  # noqa: BLE001
        result['error'] = f'{type(exc).__name__}: {exc}'
        if isinstance(exc, AccountingError):
            result['accounting_stop'] = True
    result['duration_s'] = time.perf_counter() - started
    result['post_speculation_tool_request_turns'] = result['cloud_tool_request_turns'] if result['speculation_supplied'] else 0
    # Includes failed attempts which raised before being appended in the loop.
    result['cloud_attempts'] = list(range(initial_attempt, client.attempts))
    receipts = client.receipts[initial_attempt:client.attempts]
    result['usage_complete'] = all('accounted_tokens' in r for r in receipts)
    result['prompt_tokens'] = sum(r.get('response', {}).get('usage', {}).get('prompt_tokens', 0) for r in receipts) if result['usage_complete'] else None
    result['completion_tokens'] = sum(r.get('response', {}).get('usage', {}).get('completion_tokens', 0) for r in receipts) if result['usage_complete'] else None
    result['cached_tokens'] = sum(r.get('response', {}).get('usage', {}).get('prompt_tokens_details', {}).get('cached_tokens', 0) for r in receipts) if result['usage_complete'] else None
    if not receipts:
        result['provider_cost'] = 0.0
    else:
        cost_values = []
        for receipt in receipts:
            response = receipt.get('response', {})
            usage = response.get('usage', {})
            value = usage.get('cost', response.get('cost'))
            if isinstance(value, (int, float)) and value >= 0:
                cost_values.append(float(value))
        result['provider_cost'] = sum(cost_values) if len(cost_values) == len(receipts) else None
    result['filesystem_unchanged'] = env.fingerprint() == env.initial_fingerprint
    result['success'] = not result.get('error') and result['filesystem_unchanged'] and score_answer(task, result['final'], result['tools'])
    if result['prediction']:
        result['prediction_exact'] = prediction_matches_target(result['prediction']['action'], task)
        result['speculation_sufficient'] = bool(result['tools']) and result['success'] and all(t.get('speculative', False) for t in result['tools'])
    if not result['usage_complete']:
        result['accounting_stop'] = True
    return result
