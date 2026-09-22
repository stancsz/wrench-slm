from __future__ import annotations

import json
from types import SimpleNamespace

import torch
from torch import nn


class FakeTokenizer:
    eos_token = "<eos>"
    pad_token_id = 0

    def apply_chat_template(self, messages, **kwargs):
        return messages[-1]["content"]

    def __call__(self, prompt, **kwargs):
        return {
            "input_ids": torch.tensor([[1]], dtype=torch.long),
            "attention_mask": torch.tensor([[1]], dtype=torch.long),
        }


class FakeModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.anchor = nn.Parameter(torch.zeros(1))

    def forward(self, **kwargs):
        return SimpleNamespace(hidden_states=(torch.tensor([[[1.0, 0.0]]]),))


def test_intent_safety_gate_can_only_pass_matching_action():
    from wrench_harness.intent_safety_gate import IntentSafetyGate, LABELS

    weight = torch.zeros((len(LABELS), 2))
    bias = torch.zeros(len(LABELS))
    weight[1, 0] = 4.0
    gate = IntentSafetyGate(
        model=FakeModel(),
        tokenizer=FakeTokenizer(),
        labels=list(LABELS),
        threshold=0.5,
        state_dict={"linear.weight": weight, "linear.bias": bias},
    )
    messages = [{"role": "user", "content": "Read README.md."}]
    passing = gate.check(
        messages,
        json.dumps({"schema": "wrench.proposal.v1", "action": "read_file"}),
    )
    rejecting = gate.check(
        messages,
        json.dumps({"schema": "wrench.proposal.v1", "action": "patch_draft"}),
    )
    assert passing["gate_passed"] is True
    assert rejecting["gate_passed"] is False
    assert passing["authority"] == "abstain_only"
