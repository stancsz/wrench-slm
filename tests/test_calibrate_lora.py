import torch
from torch import nn

from tools.calibrate_qwen_router import LoRALinear, _attach_attention_lora, _merge_lora_modules


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
