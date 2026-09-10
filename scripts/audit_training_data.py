"""Audit semantic properties that structural token preflight cannot prove."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse


PORT_TOKEN = '__PORT__'
RANGE_NUMBERS = re.compile(r'-?\d+')


def _json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _public_text(row: dict) -> str:
    return row.get('prompt', '') + '\n' + _json_text(row.get('context', {}))


def _selected_resource(row: dict):
    prior = row.get('context', {}).get('prior_results', {})
    service = prior.get('selected_service')
    selected_file = prior.get('selected_file')
    resources = row.get('context', {}).get('resources', [])
    if not service or not selected_file:
        return None, 'selected resource is not declared'
    matches = [item for item in resources if item.get('service') == service and item.get('config') == selected_file]
    if len(matches) != 1:
        return None, f'selected resource identity has {len(matches)} matches'
    return matches[0], None


def _range_values(prompt: str):
    numbers = RANGE_NUMBERS.findall(prompt)
    if len(numbers) < 2:
        return None
    return int(numbers[-2]), int(numbers[-1])


def _line_count(row: dict, selected_file: str | None):
    files = row.get('fixture', {}).get('files', {})
    value = files.get(selected_file) if selected_file else None
    if not isinstance(value, str):
        return None
    return len(value.splitlines())


def _quoted_command_parts(command: str):
    parts = command.split("'")
    return [parts[index] for index in range(1, len(parts), 2)]


def audit_rows(rows: list[dict]) -> dict:
    errors = []
    warnings = []
    seen_ids = set()
    boundary = Counter()
    kind_counts = Counter()
    language_counts = Counter()
    for index, row in enumerate(rows, 1):
        row_id = row.get('id', f'<row-{index}>')
        prefix = f'{row_id}: '
        if row_id in seen_ids:
            errors.append(prefix + 'duplicate id')
        seen_ids.add(row_id)
        kind = row.get('kind')
        language_counts[row.get('language', '<missing>')] += 1
        kind_counts[kind or '<missing>'] += 1
        public = _public_text(row)
        if PORT_TOKEN in public or PORT_TOKEN in _json_text(row.get('args', {})):
            errors.append(prefix + 'unresolved __PORT__ appears in model input or target')

        resource, resource_error = _selected_resource(row)
        prior = row.get('context', {}).get('prior_results', {})
        selected_file = prior.get('selected_file')
        if kind not in {'ambiguous', 'unsupported'} and resource_error:
            errors.append(prefix + resource_error)
        if resource and selected_file != resource.get('config'):
            errors.append(prefix + 'selected_file disagrees with selected resource')

        if kind in {'config', 'lines', 'draft', 'invalid_range'} and selected_file:
            if selected_file not in public:
                errors.append(prefix + 'selected file is not visible in the model input')
        declared_line_count = prior.get('selected_file_line_count')
        if kind in {'lines', 'invalid_range'}:
            if not isinstance(declared_line_count, int) or isinstance(declared_line_count, bool) or declared_line_count <= 0:
                errors.append(prefix + 'selected file line count is not publicly disclosed')
            else:
                fixture_line_count = _line_count(row, selected_file)
                if fixture_line_count is not None and fixture_line_count != declared_line_count:
                    errors.append(prefix + f'declared line count {declared_line_count} disagrees with fixture count {fixture_line_count}')
        args = row.get('args', {})
        if kind in {'config', 'lines', 'draft'} and args.get('path') != selected_file:
            errors.append(prefix + 'target path disagrees with selected_file')
        if kind == 'lines':
            start = args.get('start_line')
            end = args.get('end_line')
            if not isinstance(start, int) or not isinstance(end, int) or isinstance(start, bool) or isinstance(end, bool):
                errors.append(prefix + 'line target does not provide integer bounds')
            elif not isinstance(declared_line_count, int) or start < 1 or end < start or end > declared_line_count:
                errors.append(prefix + 'line target is not a valid inclusive range within the disclosed file length')
        if kind == 'draft':
            content = args.get('content')
            if not isinstance(content, str):
                errors.append(prefix + 'draft target has no string content')
            elif content not in public and json.dumps(content, ensure_ascii=False) not in public:
                errors.append(prefix + 'draft content is hidden from the model input')
        if kind == 'health':
            command = args.get('cmd', '')
            url = prior.get('health_url')
            parsed = urlparse(url) if isinstance(url, str) else None
            if not parsed or parsed.scheme not in {'http', 'https'} or not parsed.netloc:
                errors.append(prefix + 'health URL is not a concrete URL')
            elif not re.search(r':\d+(?:/|$)', parsed.netloc):
                errors.append(prefix + 'health URL has no concrete port')
            if not isinstance(command, str) or url not in command:
                errors.append(prefix + 'health target command does not use the selected health URL')
        if kind == 'search':
            command = args.get('cmd', '')
            parts = _quoted_command_parts(command) if isinstance(command, str) else []
            directory = prior.get('selected_directory')
            if directory and directory not in command:
                errors.append(prefix + 'search command does not use selected_directory')
            if directory and directory not in public:
                errors.append(prefix + 'search directory is hidden from the model input')
            if parts and any(part not in public for part in parts):
                errors.append(prefix + 'search marker or directory is hidden from the model input')

        if kind == 'invalid_range':
            values = _range_values(row.get('prompt', ''))
            if values is None:
                errors.append(prefix + 'invalid-range prompt has no auditable numeric bounds')
            else:
                start, end = values
                line_count = declared_line_count if isinstance(declared_line_count, int) else _line_count(row, selected_file)
                if start <= 0 or end <= 0:
                    category = 'zero_or_negative'
                elif start > end:
                    category = 'reversed'
                elif line_count is not None and (start > line_count or end > line_count):
                    category = 'beyond_eof'
                else:
                    category = 'other_invalid_or_unproven'
                boundary[category] += 1
                if category == 'other_invalid_or_unproven':
                    warnings.append(prefix + f'bounds {start}..{end} are not visibly invalid for file length {line_count}')

    required_boundary = {'zero_or_negative', 'reversed', 'beyond_eof'}
    missing_boundary = sorted(required_boundary - boundary.keys())
    return {
        'status': 'passed' if not errors and not missing_boundary else 'failed',
        'rows': len(rows), 'ids': len(seen_ids), 'kinds': dict(kind_counts),
        'languages': dict(language_counts), 'invalid_range_categories': dict(boundary),
        'missing_invalid_range_categories': missing_boundary,
        'errors': errors, 'warnings': warnings,
        'error_count': len(errors), 'warning_count': len(warnings),
        'scope': 'Semantic audit of public-input visibility and authored fixture relationships; it does not prove model quality or licensing.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, help='Dataset directory containing train.jsonl')
    parser.add_argument('--split', default='train')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = Path(args.data)
    path = data / f'{args.split}.jsonl'
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    report = audit_rows(rows)
    report.update(dataset=str(data), split=args.split,
                  dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps({'status': report['status'], 'errors': report['error_count'],
                      'warnings': report['warning_count'], 'output': str(output)}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
