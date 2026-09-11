"""Deterministic public-context proposal helper."""

import json
import re

from .protocol import ROUTER_FALLBACK


def rules_predict(record):
    """Propose only from the public prompt and context."""
    prompt = record['prompt']
    lower = prompt.lower()
    prior = record['context'].get('prior_results', {})
    path = next((r['config'] for r in record['context'].get('resources', []) if r['service'] in prompt), None)
    path = path or prior.get('selected_file')
    call = None
    if 'region' in lower and path:
        call = {'tool': 'read_file', 'args': {'path': path}}
    match = re.search(r'(?:lines?|range)\s+(\d+)\s*(?:through|to|[-.]+)\s*(\d+)', lower)
    if match and path:
        call = {'tool': 'read_file', 'args': {'path': path, 'start_line': int(match[1]), 'end_line': int(match[2])}}
    marker = re.search(r'KEY_[a-f0-9]+', prompt)
    if marker and prior.get('selected_directory'):
        call = {'tool': 'exec_command', 'args': {'cmd': f"rg -l --fixed-strings -- {marker[0]} {prior['selected_directory']}"}}
    if any(word in lower for word in ['changed', 'dirty', 'working tree', 'untracked', 'modified']):
        call = {'tool': 'exec_command', 'args': {'cmd': 'git status --short'}}
    if any(word in lower for word in ['commit', 'head']) and any(word in lower for word in ['latest', 'recent', 'subject', 'title', 'head']):
        call = {'tool': 'exec_command', 'args': {'cmd': 'git log -1 --format=%s'}}
    if prior.get('health_url') and any(word in lower for word in ['health', 'status']):
        call = {'tool': 'exec_command', 'args': {'cmd': f"curl --silent --show-error --max-time 3 {prior['health_url']}"}}
    content = re.search(r'enabled=[a-f0-9]+', prompt)
    if content and path and any(word in lower for word in ['write', 'draft', 'propos']):
        call = {'tool': 'write_file', 'args': {'path': path, 'content': content[0]}}
    return json.dumps(call) if call else ROUTER_FALLBACK
