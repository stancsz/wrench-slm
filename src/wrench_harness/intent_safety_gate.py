"""Optional learned intent/action safety gate.

The gate is deliberately fail-closed. It can turn a generated proposal into
an abstention when the frozen sidecar disagrees with the proposal's action
family, but it cannot create, repair, or authorize a proposal.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F


ABSTAIN = "abstain"
FAMILIES = ("read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft")
LABELS = (ABSTAIN, *FAMILIES)


class IntentSafetyGate:
    def __init__(self, *, model: Any, tokenizer: Any, labels: list[str], threshold: float, state_dict: dict[str, Any]) -> None:
        if labels != list(LABELS):
            raise ValueError("intent sidecar labels do not match the current allowlist")
        self.model = model
        self.tokenizer = tokenizer
        self.labels = labels
        self.threshold = threshold
        self.state_dict = state_dict
        width = int(state_dict["linear.weight"].shape[-1])
        classes = int(state_dict["linear.weight"].shape[0])
        if width < 1 or classes != len(labels):
            raise ValueError("intent sidecar head geometry is invalid")
        self.weight = state_dict["linear.weight"].to(next(model.parameters()).device)
        self.bias = state_dict["linear.bias"].to(next(model.parameters()).device)

    @classmethod
    def from_artifact(cls, artifact: str | Path, *, model: Any, tokenizer: Any) -> "IntentSafetyGate":
        bundle = torch.load(Path(artifact), map_location="cpu", weights_only=False)
        if not isinstance(bundle, dict) or bundle.get("schema") != "wrench.intent-router-sidecar.v1":
            raise ValueError(f"unsupported intent router sidecar: {artifact}")
        state_dict = bundle.get("state_dict")
        labels = bundle.get("labels")
        if not isinstance(state_dict, dict) or not isinstance(labels, list):
            raise ValueError("intent router sidecar is incomplete")
        threshold = float(bundle.get("confidence_threshold", 1.0))
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("intent router sidecar threshold is invalid")
        return cls(
            model=model,
            tokenizer=tokenizer,
            labels=labels,
            threshold=threshold,
            state_dict=state_dict,
        )

    def check(self, messages: list[dict[str, str]], generated: str) -> dict[str, Any]:
        """Return an observable gate receipt without granting authority."""

        try:
            proposal = json.loads(generated)
        except json.JSONDecodeError:
            proposal = None
        action = proposal.get("action") if isinstance(proposal, dict) else None
        prompt_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        batch = self.tokenizer(prompt_text, return_tensors="pt", add_special_tokens=False)
        device = next(self.model.parameters()).device
        batch = {key: value.to(device) for key, value in batch.items()}
        with torch.inference_mode():
            output = self.model(**batch, output_hidden_states=True, use_cache=False)
        hidden = output.hidden_states[-1].float()
        mask = batch["attention_mask"].unsqueeze(-1).float()
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
        pooled = F.normalize(pooled, dim=-1)
        logits = torch.matmul(pooled, self.weight.t()) + self.bias
        probabilities = logits.softmax(dim=-1)[0]
        confidence, index = probabilities.max(dim=-1)
        predicted_family = self.labels[int(index)]
        score = float(confidence)
        gate_passed = predicted_family != ABSTAIN and score >= self.threshold and action == predicted_family
        return {
            "schema": "wrench.intent-safety-gate.v1",
            "predicted_family": predicted_family,
            "generated_action": action,
            "confidence": round(score, 6),
            "threshold": self.threshold,
            "gate_passed": gate_passed,
            "authority": "abstain_only",
        }
