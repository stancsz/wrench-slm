"""Native NanoWrench Transformer architecture built from scratch.

Implemented natively in PyTorch with zero external pre-trained model dependencies.
Features:
- Rotary Position Embeddings (RoPE)
- Pre-RMSNorm
- SwiGLU Feed-Forward Network
- Causal Self-Attention with KV cache support
- Weight initialization from scratch (Random normal init)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class WrenchPi135MConfig:
    """Tier 1: Raspberry Pi / Low-Power CPU Gateway Architecture (Wrench-Pi).
    
    ~135M-150M parameters. Designed to run on Raspberry Pi 4/5 (ARM64) or low-power CPUs
    via GGUF/llama.cpp/NEON in < 80MB RAM footprint, enabling 24/7 silent hardware token gateways.
    """
    vocab_size: int = 32000
    dim: int = 768
    n_layers: int = 12
    n_heads: int = 12
    intermediate_dim: int = 2048
    max_seq_len: int = 2048
    norm_eps: float = 1e-6
    rope_theta: float = 10000.0
    tie_embeddings: bool = True
    initializer_range: float = 0.02


@dataclass
class Wrench05BConfig:
    """Tier 2: Workstation / GPU Pro Architecture (Wrench-Pro).
    
    ~490M-500M parameters. Designed for RTX 5070 Ti / consumer GPUs in ~1GB VRAM,
    delivering 15ms ultra-low latency speculative tool prediction and slot extraction.
    """
    vocab_size: int = 32000
    dim: int = 1024
    n_layers: int = 24
    n_heads: int = 16
    intermediate_dim: int = 2816
    max_seq_len: int = 2048
    norm_eps: float = 1e-6
    rope_theta: float = 10000.0
    tie_embeddings: bool = True
    initializer_range: float = 0.02


@dataclass
class NanoWrenchConfig:
    """DEPRECATED: 28M Nano prototype config. Superseded by WrenchPi135MConfig and Wrench05BConfig."""
    vocab_size: int = 4096
    dim: int = 512
    n_layers: int = 8
    n_heads: int = 8
    intermediate_dim: int = 1408
    max_seq_len: int = 1024
    norm_eps: float = 1e-6
    rope_theta: float = 10000.0
    tie_embeddings: bool = True
    initializer_range: float = 0.02


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6) -> None:
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        variance = x.pow(2).mean(-1, keepdim=True)
        return x * torch.rsqrt(variance + self.eps) * self.weight


class RotaryEmbedding(nn.Module):
    def __init__(self, dim: int, max_seq_len: int = 2048, theta: float = 10000.0) -> None:
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        inv_freq = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

    def forward(self, x: torch.Tensor, seq_len: int) -> Tuple[torch.Tensor, torch.Tensor]:
        t = torch.arange(seq_len, device=x.device, dtype=self.inv_freq.dtype)
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos()[:seq_len], emb.sin()[:seq_len]


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    cos = cos.unsqueeze(0).unsqueeze(2)
    sin = sin.unsqueeze(0).unsqueeze(2)
    q_embed = (q * cos) + (_rotate_half(q) * sin)
    k_embed = (k * cos) + (_rotate_half(k) * sin)
    return q_embed, k_embed


class SwiGLU(nn.Module):
    def __init__(self, dim: int, intermediate_dim: int) -> None:
        super().__init__()
        self.gate_proj = nn.Linear(dim, intermediate_dim, bias=False)
        self.up_proj = nn.Linear(dim, intermediate_dim, bias=False)
        self.down_proj = nn.Linear(intermediate_dim, dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class CausalSelfAttention(nn.Module):
    def __init__(self, config: NanoWrenchConfig) -> None:
        super().__init__()
        self.n_heads = config.n_heads
        self.dim = config.dim
        self.head_dim = config.dim // config.n_heads
        assert config.dim % config.n_heads == 0

        self.q_proj = nn.Linear(config.dim, config.dim, bias=False)
        self.k_proj = nn.Linear(config.dim, config.dim, bias=False)
        self.v_proj = nn.Linear(config.dim, config.dim, bias=False)
        self.o_proj = nn.Linear(config.dim, config.dim, bias=False)
        self.rotary_emb = RotaryEmbedding(self.head_dim, max_seq_len=config.max_seq_len, theta=config.rope_theta)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        bsz, seq_len, _ = x.shape

        q = self.q_proj(x).view(bsz, seq_len, self.n_heads, self.head_dim)
        k = self.k_proj(x).view(bsz, seq_len, self.n_heads, self.head_dim)
        v = self.v_proj(x).view(bsz, seq_len, self.n_heads, self.head_dim)

        cos, sin = self.rotary_emb(q, seq_len)
        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        out = F.scaled_dot_product_attention(
            q, k, v,
            attn_mask=mask,
            dropout_p=0.0,
            is_causal=(mask is None and seq_len > 1),
        )
        out = out.transpose(1, 2).contiguous().view(bsz, seq_len, self.dim)
        return self.o_proj(out)


class TransformerBlock(nn.Module):
    def __init__(self, config: NanoWrenchConfig) -> None:
        super().__init__()
        self.attn_norm = RMSNorm(config.dim, eps=config.norm_eps)
        self.attn = CausalSelfAttention(config)
        self.ffn_norm = RMSNorm(config.dim, eps=config.norm_eps)
        self.ffn = SwiGLU(config.dim, config.intermediate_dim)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        h = x + self.attn(self.attn_norm(x), mask=mask)
        out = h + self.ffn(self.ffn_norm(h))
        return out


class NanoWrench(nn.Module):
    """Native from-scratch Nano Transformer for Wrench-SLM."""

    def __init__(self, config: Optional[NanoWrenchConfig] = None) -> None:
        super().__init__()
        self.config = config or NanoWrenchConfig()
        self.embed_tokens = nn.Embedding(self.config.vocab_size, self.config.dim)
        self.layers = nn.ModuleList([TransformerBlock(self.config) for _ in range(self.config.n_layers)])
        self.norm = RMSNorm(self.config.dim, eps=self.config.norm_eps)
        self.lm_head = nn.Linear(self.config.dim, self.config.vocab_size, bias=False)

        if self.config.tie_embeddings:
            self.lm_head.weight = self.embed_tokens.weight

        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, RMSNorm):
            nn.init.ones_(module.weight)

    @property
    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def forward(
        self,
        input_ids: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        h = self.embed_tokens(input_ids)
        for layer in self.layers:
            h = layer(h, mask=mask)
        h = self.norm(h)
        logits = self.lm_head(h)

        loss: Optional[torch.Tensor] = None
        if labels is not None:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, self.config.vocab_size),
                shift_labels.view(-1),
                ignore_index=-100,
            )
        return logits, loss

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 128,
        temperature: float = 0.0,
        top_p: float = 1.0,
        eos_token_id: Optional[int] = None,
        logits_processor: Optional[Callable[[list[int], torch.Tensor], torch.Tensor]] = None,
    ) -> torch.Tensor:
        self.eval()
        if eos_token_id is None:
            eos_token_id = 258  # WrenchTokenizer default eos token

        # If prompt exceeds available context space, preserve the rightmost prompt tokens
        max_prompt_len = max(16, self.config.max_seq_len - max_new_tokens)
        if input_ids.shape[-1] > max_prompt_len:
            curr_ids = input_ids[:, -max_prompt_len:].clone()
        else:
            curr_ids = input_ids.clone()

        start_len = curr_ids.shape[-1]

        for _ in range(max_new_tokens):
            if curr_ids.shape[-1] >= self.config.max_seq_len:
                break
            logits, _ = self.forward(curr_ids)
            next_token_logits = logits[:, -1, :]

            if logits_processor is not None:
                generated_so_far = curr_ids[0, start_len:].tolist()
                next_token_logits = logits_processor(generated_so_far, next_token_logits)

            if temperature > 0.0:
                scaled_logits = next_token_logits / temperature
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(scaled_logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = False
                    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                    scaled_logits[indices_to_remove] = -float("Inf")
                probs = F.softmax(scaled_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)

            curr_ids = torch.cat([curr_ids, next_token], dim=1)
            if next_token.item() == eos_token_id:
                break
        return curr_ids
