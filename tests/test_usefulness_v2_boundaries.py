import json

import pytest

from scripts.audit_usefulness_v2_data import audit_public_records
from scripts.pilot_analyze_v2 import (
    accounting,
    latency_tradeoffs,
    validate_complete,
    validate_quality_receipts,
)
from scripts.pilot_power_v2 import assess
from scripts.pilot_run import verify_v21_package
from wrench.pilot_tasks_v2 import make_task, public_record
from wrench.pilot_workflow import AccountingError, CloudClient


def test_wrong_package_is_rejected_before_model_load():
    with pytest.raises(ValueError, match='immutable V21 manifest'):
        verify_v21_package('artifacts/model-release/package-selected-v20')


def test_public_record_excludes_private_labels():
    task = make_task('config', 0, 0, 'evaluation')
    public = public_record(task)
    assert set(public) == {'prompt', 'context'}
    assert 'expected_answer' not in public
    assert 'fixture' not in public
    assert 'args' not in public
    assert 'tool' not in public
    assert task['expected_answer'] not in json.dumps(public, ensure_ascii=False)


def test_public_private_audit_rejects_private_key_in_context():
    task = make_task('config', 0, 0, 'evaluation')
    task['context']['expected_answer'] = 'leaked'
    failures = audit_public_records([task])
    assert failures[0]['reason'] == 'private_field_in_public_record'
    assert failures[0]['fields'] == ['expected_answer']


def test_incomplete_run_is_rejected_even_when_all_rows_are_present():
    rows = [
        {'task_id': 'one', 'family_id': 'family', 'arm': arm, 'usage_complete': True}
        for arm in ['A', 'B', 'C']
    ]
    rows[2]['usage_complete'] = False
    with pytest.raises(ValueError, match='Incomplete V2 experiment'):
        validate_complete({'status': 'completed', 'dataset_tasks_assigned': 1}, rows)


def test_accounting_rejects_model_mismatch_and_missing_usage(tmp_path):
    cloud = tmp_path / 'cloud'
    cloud.mkdir()
    (cloud / '00000.json').write_text(json.dumps({
        'request': {'model': 'expected'},
        'response': {'model': 'other', 'usage': {'prompt_tokens': 1, 'completion_tokens': 1}},
    }), encoding='utf-8')
    (cloud / '00001.json').write_text(json.dumps({
        'request': {'model': 'expected'},
        'response': {'model': 'expected'},
    }), encoding='utf-8')
    passed, receipts = accounting(tmp_path, 'expected')
    assert not passed
    assert len(receipts) == 2


def _quality_meta():
    return {
        'status': 'completed',
        'model': 'Qwen/Qwen2.5-0.5B-Instruct',
        'revision': 'revision',
        'dataset_split_sha256': 'dataset',
        'protocol_sha256': 'protocol',
        'model_source': {
            'adapter_sha256': 'adapter',
            'package_manifest_sha256': 'manifest',
            'base_weights_sha256': 'base',
        },
    }


def _write_quality_receipt(root, meta, passed):
    quality = root / 'quality'
    quality.mkdir()
    receipt = {
        'status': 'completed',
        'model': meta['model'],
        'revision': meta['revision'],
        'dataset_sha256': meta['dataset_split_sha256'],
        'protocol_sha256': meta['protocol_sha256'],
        **meta['model_source'],
    }
    (quality / 'run.json').write_text(json.dumps(receipt), encoding='utf-8')
    (quality / 'summary.json').write_text(json.dumps({
        'model_quality_passed': passed,
        'model_quality_gates': {'routine_exact': passed},
    }), encoding='utf-8')
    return quality


def test_quality_receipt_missing_is_inconclusive():
    result = validate_quality_receipts(_quality_meta(), [])
    assert result['state'] == 'missing'


def test_quality_receipt_failed_gate_is_no_go_state(tmp_path):
    meta = _quality_meta()
    quality = _write_quality_receipt(tmp_path, meta, False)
    result = validate_quality_receipts(meta, [quality])
    assert result['state'] == 'failed'


def test_quality_receipt_identity_mismatch_is_missing_state(tmp_path):
    meta = _quality_meta()
    quality = _write_quality_receipt(tmp_path, meta, True)
    receipt = json.loads((quality / 'run.json').read_text(encoding='utf-8'))
    receipt['protocol_sha256'] = 'wrong'
    (quality / 'run.json').write_text(json.dumps(receipt), encoding='utf-8')
    result = validate_quality_receipts(meta, [quality])
    assert result['state'] == 'missing'


def test_latency_regression_requires_qualification():
    result = latency_tradeoffs({'C_vs_A': {'latency_saving_fraction': -0.11}})
    assert result['C_vs_A']['material_regression']


def test_power_assessment_keeps_current_design_exploratory():
    result = assess(120, 2, 0.05, 0.02, 5, 11, 2)
    assert result['decision'] == 'EXPLORATORY_INCONCLUSIVE'
    assert result['minimum_design']['balanced_families'] == 198


def test_cloud_budget_stops_before_transport(tmp_path):
    client = CloudClient(tmp_path, max_attempts=0)
    with pytest.raises(AccountingError, match='budget exhausted'):
        client.call([])
