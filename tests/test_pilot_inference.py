import pytest

from wrench.pilot_inference import validate_prediction


TOOLS = [{'name': 'read_file', 'parameters': {
    'type': 'object', 'properties': {'path': {'type': 'string'}, 'start': {'type': 'integer', 'minimum': 1}},
    'required': ['path'], 'additionalProperties': False,
}}]


@pytest.mark.parametrize('raw', [
    '{"tool":"read_file","args":{"path":123}}',
    '{"tool":"read_file","args":{"path":"a","start":true}}',
    '{"tool":"read_file","args":{"path":"a","start":0}}',
    '{"tool":"read_file","args":{"path":"a","unknown":"b"}}',
    '{"tool":"read_file","args":{}}',
    '{"tool":"unknown","args":{}}',
    '```json\n{"tool":"read_file","args":{"path":"a"}}\n```',
    '{"tool":"read_file","args":{"path":"a"}} trailing prose',
])
def test_invalid_output_is_not_hidden_by_fallback(raw):
    action, invalid, reason = validate_prediction(raw, TOOLS)
    assert action == 'ROUTER_FALLBACK' and invalid and reason


def test_intentional_fallback_and_complete_call():
    assert validate_prediction('ROUTER_FALLBACK', TOOLS) == ('ROUTER_FALLBACK', False, 'model_abstention')
    raw = '{"tool":"read_file","args":{"path":"src/example.py","start":10}}'
    assert validate_prediction(raw, TOOLS) == (raw, False, 'valid_call')


def test_unsupported_schema_fails_closed():
    tools = [{'name': 'read_file', 'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': True}}]
    with pytest.raises(ValueError, match='closed objects'):
        validate_prediction('{"tool":"read_file","args":{}}', tools)
