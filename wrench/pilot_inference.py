"""Isolated Pro prediction with explicit raw-output and validation receipts.

This initial pilot path uses unconstrained decoding plus strict boundary
validation. Invalid output is recorded as invalid, even when it becomes a
runtime fallback. It does not claim grammar-constrained generation.
"""

from dataclasses import asdict, dataclass
import time

import torch

from .dataset import build_training_prompt
from .protocol import ROUTER_FALLBACK, parse_call


@dataclass
class PilotPrediction:
    raw: str
    action: str
    invalid_output: bool
    reason: str
    input_tokens: int
    output_tokens: int
    duration_s: float

    def to_dict(self):
        return asdict(self)


def validate_prediction(raw, tools):
    if raw == ROUTER_FALLBACK:
        return ROUTER_FALLBACK, False, 'model_abstention'
    call, result = parse_call(raw)
    if not result.valid:
        return ROUTER_FALLBACK, True, result.error
    schema = next((tool for tool in tools if tool['name'] == call['tool']), None)
    if schema is None:
        return ROUTER_FALLBACK, True, 'unknown_tool'
    # Pilot schemas deliberately restrict arguments to primitive types.
    # Reject unsupported schema constructs rather than silently accepting them.
    parameters = schema['parameters']
    if set(parameters) - {'type', 'properties', 'required', 'additionalProperties'}:
        raise ValueError('Unsupported pilot argument schema')
    if parameters.get('type') != 'object' or parameters.get('additionalProperties') is not False:
        raise ValueError('Pilot argument schemas must be closed objects')
    arguments = call['args']
    properties = parameters['properties']
    if set(arguments) - set(properties) or set(parameters.get('required', [])) - set(arguments):
        return ROUTER_FALLBACK, True, 'argument_keys'
    types = {'string': str, 'integer': int, 'boolean': bool}
    for key, value in arguments.items():
        spec = properties[key]
        if set(spec) - {'type', 'description', 'enum', 'minimum', 'maximum'} or spec.get('type') not in types:
            raise ValueError('Unsupported pilot property schema')
        if type(value) is not types[spec['type']]:
            return ROUTER_FALLBACK, True, 'argument_type'
        if 'enum' in spec and value not in spec['enum']:
            return ROUTER_FALLBACK, True, 'argument_enum'
        if 'minimum' in spec and value < spec['minimum']:
            return ROUTER_FALLBACK, True, 'argument_minimum'
        if 'maximum' in spec and value > spec['maximum']:
            return ROUTER_FALLBACK, True, 'argument_maximum'
    return raw, False, 'valid_call'


class PilotExecutor:
    def __init__(self, model, tokenizer, *, max_input_tokens=1536, max_new_tokens=256):
        self.model = model
        self.tokenizer = tokenizer
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens
        self.model.eval()

    @torch.inference_mode()
    def predict(self, record):
        started = time.perf_counter()
        text = build_training_prompt(record, self.tokenizer)
        inputs = self.tokenizer(text, return_tensors='pt', add_special_tokens=False).to(self.model.device)
        length = inputs['input_ids'].shape[1]
        if length > self.max_input_tokens:
            return PilotPrediction('', ROUTER_FALLBACK, False, 'input_budget', length, 0, time.perf_counter() - started)
        output = self.model.generate(
            **inputs, max_new_tokens=self.max_new_tokens, do_sample=False,
            pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id, use_cache=True,
        )
        generated = output[0, length:].tolist()
        raw = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
        action, invalid, reason = validate_prediction(raw, record['context']['tools'])
        return PilotPrediction(raw, action, invalid, reason, length, len(generated), time.perf_counter() - started)
