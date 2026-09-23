"""Binary System One readout over an already loaded, frozen Qwen backbone.

One text-backbone forward, no vocabulary projection and no generation. A
not_abstain decision never grants execution authority. This head is specific
to the checkpoint and tokenizer recorded in its artifact.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

SCHEMA = "wrench.qwen-binary-head.v1"
LABELS = ["abstain", "not_abstain"]
FEATURE = "qwen-text-last-token-l2-chat-no-thinking-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checkpoint_identity(directory: str | Path, check=None) -> dict[str, str]:
    """Hash actual weights and prompt serialization once at model startup."""
    root = Path(directory).resolve()
    paths = [root / "config.json", root / "tokenizer.json", root / "tokenizer_config.json"]
    index = root / "model.safetensors.index.json"
    if index.exists():
        paths.append(index)
        if index.stat().st_size > 2_000_000:
            raise ValueError("checkpoint index too large")
        shards = set(json.loads(index.read_text(encoding="utf-8"))["weight_map"].values())
        if len(shards) > 128:
            raise ValueError("too many checkpoint shards")
        for name in sorted(shards):
            path = (root / name).resolve()
            if path.parent != root or path.suffix != ".safetensors":
                raise ValueError("invalid checkpoint shard path")
            paths.append(path)
    else:
        paths.append(root / "model.safetensors")
    if (root / "chat_template.jinja").exists():
        paths.append(root / "chat_template.jinja")
    result = {}
    for path in paths:
        if check is not None:
            check()
        result[path.name] = sha256_file(path)
    return result


def text_backbone(model):
    backbone = getattr(getattr(model, "model", None), "language_model", None)
    if backbone is None or getattr(model.config, "model_type", None) != "qwen3_5_moe":
        raise ValueError("expected the existing Qwen3.5/3.6 MoE text backbone")
    return backbone


def encode_messages(tokenizer, messages, *, max_tokens: int, max_chars: int):
    if not isinstance(messages, list) or not 1 <= len(messages) <= 16:
        raise ValueError("input_invalid")
    characters = 0
    for message in messages:
        if (not isinstance(message, dict) or not isinstance(message.get("role"), str)
                or message["role"] not in {"system", "user", "assistant", "tool"}
                or not isinstance(message.get("content"), str)):
            raise ValueError("input_invalid")
        characters += len(message["content"])
    if characters > max_chars:
        raise ValueError("input_too_long")
    # This initial head was trained on complete single-turn tasks. Do not
    # silently discard a conversational dependency to make an input fit.
    users = [m for m in messages if m["role"] == "user"]
    if len(users) != 1 or not users[0]["content"].strip() or any(
        m["role"] in {"assistant", "tool"} for m in messages
    ):
        raise ValueError("context_requires_resolution")
    text = tokenizer.apply_chat_template(messages, tokenize=False,
                                         add_generation_prompt=True, enable_thinking=False)
    batch = tokenizer(text, return_tensors="pt", add_special_tokens=False, truncation=False)
    if not 1 <= batch["input_ids"].shape[-1] <= max_tokens:
        raise ValueError("input_too_long")
    # No vision input is supported. Special media tokens cannot be treated
    # as an ordinary text-only request.
    media_ids = {tokenizer.convert_tokens_to_ids(token) for token in ("<|image_pad|>", "<|video_pad|>")}
    media_ids.discard(None)
    media_ids.discard(tokenizer.unk_token_id)
    if media_ids.intersection(batch["input_ids"][0].tolist()):
        raise ValueError("media_requires_resolution")
    return batch


def embed(model, batch):
    backbone = text_backbone(model)
    if model.training:
        raise ValueError("binary classification requires model.eval()")
    device = next(backbone.parameters()).device
    batch = {key: value.to(device) for key, value in batch.items()}
    with torch.inference_mode():
        output = backbone(**batch, use_cache=False, output_hidden_states=False,
                          output_attentions=False, return_dict=True)
        # A single unpadded request. The final prompt token sees the whole input.
        pooled = F.normalize(output.last_hidden_state[:, -1, :].float(), dim=-1)
    return pooled


class QwenAbstainGate:
    @classmethod
    def from_artifact(cls, artifact, *, model, tokenizer, model_dir, identity=None):
        with Path(artifact).open("rb") as stream:
            raw = stream.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("binary head artifact too large")
        obj = json.loads(raw)
        if (not isinstance(obj, dict) or obj.get("schema") != SCHEMA or obj.get("labels") != LABELS
                or obj.get("feature") != FEATURE):
            raise ValueError("binary head schema mismatch")
        actual_identity = identity if identity is not None else checkpoint_identity(model_dir)
        if obj.get("checkpoint_sha256") != actual_identity:
            raise ValueError("binary head checkpoint/tokenizer mismatch")
        backbone = text_backbone(model)
        width = backbone.config.hidden_size
        if obj.get("width") != width:
            raise ValueError("binary head width mismatch")
        packed = base64.b64decode(obj["head_f32le_b64"], validate=True)
        if len(packed) != (width * 2 + 2) * 4 or hashlib.sha256(packed).hexdigest() != obj["head_sha256"]:
            raise ValueError("binary head checksum/length mismatch")
        values = torch.frombuffer(bytearray(packed), dtype=torch.float32).clone()
        if not torch.isfinite(values).all():
            raise ValueError("nonfinite binary head")
        threshold = obj.get("threshold")
        if type(threshold) not in (int, float) or not math.isfinite(threshold) or not .5 <= threshold <= 1:
            raise ValueError("invalid abstention threshold")
        for key, limit in (("max_tokens", 2048), ("max_chars", 16384)):
            if type(obj.get(key)) is not int or not 1 <= obj[key] <= limit:
                raise ValueError(f"invalid {key}")
        instance = cls()
        instance.model, instance.tokenizer = model, tokenizer
        device = next(backbone.parameters()).device
        instance.weight = values[:width * 2].reshape(2, width).to(device)
        instance.bias = values[width * 2:].to(device)
        instance.threshold = threshold
        instance.max_tokens, instance.max_chars = obj["max_tokens"], obj["max_chars"]
        instance.artifact_sha256 = hashlib.sha256(raw).hexdigest()
        return instance

    def check_messages(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        receipt = {"schema": "wrench.qwen-binary-decision.v1", "decision": "abstain",
                   "reason": "model_decision", "probabilities": None,
                   "threshold": self.threshold, "head_sha256": self.artifact_sha256,
                   "authority": "abstain_only", "model_forwards": 0, "generated_tokens": 0}
        try:
            batch = encode_messages(self.tokenizer, messages,
                                    max_tokens=self.max_tokens, max_chars=self.max_chars)
        except ValueError as exc:
            receipt["reason"] = str(exc)
            return receipt
        with torch.inference_mode():
            pooled = embed(self.model, batch)
            probabilities = F.linear(pooled, self.weight.to(pooled.device), self.bias.to(pooled.device)).softmax(-1)[0]
        if not torch.isfinite(probabilities).all():
            raise ValueError("nonfinite binary probabilities")
        probability = float(probabilities[1])
        receipt.update(decision="not_abstain" if probability >= self.threshold else "abstain",
                       probabilities={"abstain": float(probabilities[0]), "not_abstain": probability},
                       model_forwards=1, input_tokens=int(batch["input_ids"].shape[-1]))
        return receipt


def save_head(path, head, *, identity, threshold, max_tokens, metadata):
    values = torch.cat([head.weight.detach().cpu().flatten(), head.bias.detach().cpu()]).float()
    packed = values.numpy().astype("<f4").tobytes()
    obj = {"schema": SCHEMA, "labels": LABELS, "feature": FEATURE,
           "width": head.in_features, "threshold": float(threshold),
           "max_tokens": max_tokens, "max_chars": 8192,
           "checkpoint_sha256": identity, "head_sha256": hashlib.sha256(packed).hexdigest(),
           "head_f32le_b64": base64.b64encode(packed).decode("ascii"), "metadata": metadata}
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
        stream.write("\n")
