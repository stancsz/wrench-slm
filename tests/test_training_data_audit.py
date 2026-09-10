import copy

from scripts.audit_training_data import audit_rows


def base_row():
    return {
        'id': 'row-1', 'kind': 'draft', 'language': 'en',
        'prompt': 'Draft write to config.txt containing enabled=yes.',
        'context': {
            'resources': [{'service': 'svc', 'config': 'config.txt'}],
            'prior_results': {'selected_service': 'svc', 'selected_file': 'config.txt',
                              'selected_directory': 'src', 'selected_file_line_count': 2,
                              'health_url': 'http://127.0.0.1:18000/health'},
            'tools': [],
        },
        'args': {'path': 'config.txt', 'content': 'enabled=yes'},
        'fixture': {'files': {'config.txt': 'a\nb\n'}, 'git': False, 'health': None},
        'tool': 'write_file', 'expected_answer': 'DRAFT_ONLY',
    }


def test_hidden_draft_content_fails():
    row = base_row()
    row['prompt'] = 'Draft write to config.txt and do not execute it.'
    report = audit_rows([row])
    assert report['status'] == 'failed'
    assert any('draft content is hidden' in error for error in report['errors'])


def test_invalid_boundary_categories_and_visible_draft_pass():
    row = base_row()
    rows = []
    for index, bounds in enumerate([(0, 4), (5, 2), (3, 8)]):
        item = copy.deepcopy(row)
        item.update(id=f'row-{index}', kind='invalid_range', tool='fallback', args={})
        item['prompt'] = f'The range is invalid. Target path: config.txt. Requested bounds: {bounds[0]} through {bounds[1]}. Return ROUTER_FALLBACK.'
        rows.append(item)
    report = audit_rows(rows)
    assert report['status'] == 'passed'
    assert report['invalid_range_categories'] == {'zero_or_negative': 1, 'reversed': 1, 'beyond_eof': 1}
