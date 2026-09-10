"""Real disposable OS fixtures and a strictly bounded pilot tool executor."""

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import threading
import time
from urllib.parse import urlparse

from .pilot_inference import validate_prediction
from .pilot_tasks import TOOLS


class PilotEnvironment:
    def __init__(self, task, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        self.task = json.loads(json.dumps(task))
        self.server = None
        fixture = task['fixture']
        for path, content in fixture['files'].items():
            target = self.path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        if fixture['git']:
            self._run(['git', 'init', '-q'])
            dirty = fixture.get('dirty', [])
            if dirty:
                self.path(dirty[0]).write_text('original\n', encoding='utf-8')
            # Add only the fixture-generated paths, never the parent workspace.
            for name in [*fixture['files'], *dirty[:1]]:
                self._run(['git', 'add', '--', name])
            self._run(['git', '-c', 'user.name=Wrench Pilot', '-c', 'user.email=pilot@example.invalid',
                       '-c', 'commit.gpgsign=false', 'commit', '-q', '-m', fixture.get('subject', 'Initial fixture')])
            if dirty:
                self.path(dirty[0]).write_text('modified\n', encoding='utf-8')
                self.path(dirty[1]).write_text('untracked\n', encoding='utf-8')
        if fixture['health']:
            body = json.dumps(fixture['health']).encode()

            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200 if self.path == '/health' else 404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(body if self.path == '/health' else b'{}')

                def log_message(self, *args):
                    pass

            self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            old = self.task['context']['prior_results']['health_url']
            new = f'http://127.0.0.1:{self.server.server_port}/health'
            self.task = json.loads(json.dumps(self.task).replace(old, new))
        self.initial_fingerprint = self.fingerprint()

    def path(self, relative):
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError('Path outside fixture')
        if '.git' in target.relative_to(self.root).parts:
            raise ValueError('Direct Git metadata access is not permitted')
        return target

    def _run(self, argv):
        result = subprocess.run(argv, cwd=self.root, capture_output=True, encoding='utf-8', errors='replace', timeout=10)
        if result.returncode:
            raise RuntimeError(f'{argv[0]} exited {result.returncode}: {result.stderr[:300]}')
        return result.stdout

    def fingerprint(self):
        return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts}

    def execute(self, call):
        started = time.perf_counter()
        receipt = {'call': call, 'executed': False, 'draft_only': False}
        try:
            _, invalid, reason = validate_prediction(json.dumps(call), TOOLS)
            if invalid:
                raise ValueError(reason)
            args = call['args']
            if call['tool'] == 'read_file':
                text = self.path(args['path']).read_text(encoding='utf-8')
                if 'start_line' in args or 'end_line' in args:
                    start = args.get('start_line', 1)
                    end = args.get('end_line', len(text.splitlines()))
                    if end < start:
                        raise ValueError('Reversed line range')
                    text = '\n'.join(text.splitlines()[start - 1:end])
                receipt.update(executed=True, output=text)
            elif call['tool'] == 'write_file':
                self.path(args['path'])
                receipt.update(draft_only=True, output=json.dumps({'status': 'DRAFT_ONLY', 'draft': args}))
            else:
                argv = shlex.split(args['cmd'])
                if argv in (['git', 'status', '--short'], ['git', 'log', '-1', '--format=%s']):
                    # Avoid optional index refresh writes during read-only inspection.
                    argv = ['git', '--no-optional-locks', *argv[1:]]
                elif len(argv) == 6 and argv[:4] == ['rg', '-l', '--fixed-strings', '--']:
                    self.path(argv[5])
                elif len(argv) == 6 and argv[:5] == ['curl', '--silent', '--show-error', '--max-time', '3']:
                    parsed = urlparse(argv[5])
                    if self.server is None or parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.port != self.server.server_port or parsed.path != '/health' or parsed.query:
                        raise ValueError('Health URL does not belong to fixture')
                else:
                    raise ValueError('Command outside read-only pilot contract')
                executable = shutil.which(argv[0])
                if not executable:
                    raise RuntimeError(f'Missing executable: {argv[0]}')
                receipt.update(executed=True, output=self._run([executable, *argv[1:]]).replace('\\', '/'))
            if len(receipt.get('output', '')) > 8192:
                receipt['output'] = receipt['output'][:8192]
                receipt['truncated'] = True
        except Exception as exc:
            receipt['error'] = f'{type(exc).__name__}: {exc}'
            receipt['output'] = json.dumps({'error': receipt['error']})
        receipt['duration_s'] = time.perf_counter() - started
        receipt['filesystem_unchanged'] = self.fingerprint() == self.initial_fingerprint
        return receipt

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


def score_answer(task, text, tool_receipts):
    """Outcome checking is independent of exact command/teacher agreement."""
    try:
        answer = json.loads(text)['answer']
    except (ValueError, TypeError, KeyError):
        return False
    expected = task['expected_answer']
    if isinstance(expected, list):
        if not isinstance(answer, list) or not all(isinstance(x, str) for x in answer):
            return False
        if task['kind'] == 'lines':
            correct = answer == expected
        else:
            correct = sorted(x.replace('\\', '/') for x in answer) == sorted(expected)
    else:
        correct = answer == expected
    if task['kind'] == 'draft':
        correct = correct and any(r.get('draft_only') and r['call']['args'] == task['args'] for r in tool_receipts)
    elif task['kind'] != 'ambiguous':
        evidence = '\n'.join(r.get('output', '').replace('\\', '/') for r in tool_receipts
                             if r.get('executed') and not r.get('error'))
        values = expected if isinstance(expected, list) else [expected]
        correct = correct and all(value in evidence for value in values)
    return correct and all(r['filesystem_unchanged'] for r in tool_receipts)
