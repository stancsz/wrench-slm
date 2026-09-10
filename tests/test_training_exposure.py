import json

from scripts.training_exposure import audit


def test_partial_batch_replay_and_missing_category(tmp_path):
    path = tmp_path / 'train.jsonl'
    rows = [dict(id=str(i), kind=k, language='en', family_id=k)
            for i, k in enumerate(['invalid_range', 'invalid_range', 'lines'])]
    path.write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
    report = audit(path, [1, 3], 2, 1, ['invalid_range', 'lines'], ['en'])
    first, third = report['checkpoints']
    assert first['missing_kinds'] == ['lines']
    assert first['presentations'] == 2
    assert third['presentations'] == 5
    assert third['unique_rows'] == 3
    assert third['repeated_presentations'] == 2
    assert third['kinds'] == {'invalid_range': 4, 'lines': 1}
    assert not report['passed']
