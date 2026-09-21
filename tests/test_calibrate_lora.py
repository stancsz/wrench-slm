import torch
from torch import nn

from tools.calibrate_qwen_router import (
    LoRALinear,
    _attach_attention_lora,
    _enable_gradient_checkpointing,
    _merge_lora_modules,
    _trainable_state_dict,
)


class _TinyAttention(nn.Module):
    def __init__(self):
        super().__init__()
        self.q_proj = nn.Linear(8, 8)
        self.k_proj = nn.Linear(8, 8)
        self.v_proj = nn.Linear(8, 8)
        self.o_proj = nn.Linear(8, 8)
        self.linear_attn = nn.Linear(8, 8)


class _TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.ModuleList([nn.ModuleDict({"self_attn": _TinyAttention()})])


def test_attention_lora_targets_only_full_attention_projections():
    model = _TinyModel()
    trainable, attached = _attach_attention_lora(model, rank=2, alpha=4)

    assert len(attached) == 4
    assert all(isinstance(model.layers[0]["self_attn"].__getattr__(name), LoRALinear) for name in ("q_proj", "k_proj", "v_proj", "o_proj"))
    assert not isinstance(model.layers[0]["self_attn"].linear_attn, LoRALinear)
    assert sum(parameter.numel() for parameter in trainable) > 0

    _merge_lora_modules(model)
    assert not any(isinstance(module, LoRALinear) for module in model.modules())


def test_gradient_checkpointing_reports_backend_support():
    class Checkpointable(nn.Module):
        def __init__(self):
            super().__init__()
            self.called = False

        def gradient_checkpointing_enable(self, **kwargs):
            self.called = bool(kwargs)

        def enable_input_require_grads(self):
            self.input_grads = True

    model = Checkpointable()
    assert _enable_gradient_checkpointing(model) is True
    assert model.called is True
    assert model.input_grads is True


def test_gradient_checkpointing_reports_unsupported_backend():
    assert _enable_gradient_checkpointing(nn.Linear(2, 2)) is False


def test_trainable_state_dict_excludes_frozen_backbone():
    model = nn.Sequential(nn.Linear(2, 2), nn.Linear(2, 2))
    for parameter in model[0].parameters():
        parameter.requires_grad_(False)
    state = _trainable_state_dict(model)
    assert state
    assert all(name.startswith("1.") for name in state)
