"""Optional FreeToken overlay for Wrench native long-context experiments.

This module is loaded through ``PYTHONPATH`` and deliberately patches only the
Qwen3.5-MoE serving path. It does not alter model weights. The overlay keeps a
small, explicit set of full-attention layers for global memory and serves the
remaining Qwen full-attention layers with a bounded sliding-window KV pool.

The model still receives the complete input sequence. This is a serving
architecture experiment, not a claim that the unchanged checkpoint has been
quality-trained for 4M tokens.
"""

from __future__ import annotations

import os
import sys
import asyncio
from dataclasses import replace
from pathlib import Path


if os.name == "nt" and not hasattr(os, "posix_fadvise"):
    # FreeToken's expert-bank loader calls this POSIX page-cache hint while
    # streaming packed shards. Windows has no equivalent, so the safe
    # portable behavior is a no-op.
    os.posix_fadvise = lambda fd, offset, length, advice: None
    os.POSIX_FADV_DONTNEED = 0

if os.name == "nt":
    # pyzmq requires selector-style add_reader support on Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import uvicorn.loops.asyncio as uvicorn_asyncio

        uvicorn_asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    except Exception:
        pass


def _csv_ints(value: str) -> tuple[int, ...]:
    result: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if item:
            result.append(int(item))
    return tuple(result)


def _resolve_global_ids(full_ids: tuple[int, ...], requested: str) -> tuple[int, ...]:
    """Resolve the bounded global-attention policy without importing FreeToken."""

    if requested.strip().casefold() in {"none", "off", "0"}:
        return ()
    selected = _csv_ints(requested) if requested else (full_ids[-1],)
    return tuple(layer_id for layer_id in selected if layer_id in full_ids)


def _install_qwen_long_context_overlay() -> None:
    if os.environ.get("WRENCH_LONG_CONTEXT_OVERLAY", "0") != "1":
        return

    # The editable FreeToken checkout supplies Python sources while the venv
    # supplies compiled CUDA extensions. Make the namespace package see both.
    import freetoken.kernel as kernel_package

    installed_kernel = Path(sys.prefix) / "Lib" / "site-packages" / "freetoken" / "kernel"
    if installed_kernel.is_dir() and str(installed_kernel) not in kernel_package.__path__:
        kernel_package.__path__.append(str(installed_kernel))

    if os.environ.get("WRENCH_FREETOKEN_TCP_ZMQ") == "1":
        from freetoken.scheduler.config import SchedulerConfig
        from freetoken.server.args import ServerArgs

        SchedulerConfig.zmq_backend_addr = property(lambda self: f"tcp://127.0.0.1:{self.server_port + 10}")
        SchedulerConfig.zmq_detokenizer_addr = property(lambda self: f"tcp://127.0.0.1:{self.server_port + 11}")
        SchedulerConfig.zmq_scheduler_broadcast_addr = property(lambda self: f"tcp://127.0.0.1:{self.server_port + 12}")
        ServerArgs.zmq_frontend_addr = property(lambda self: f"tcp://127.0.0.1:{self.server_port + 13}")
        ServerArgs.zmq_tokenizer_addr = property(
            lambda self: f"tcp://127.0.0.1:{self.server_port + 11 if self.share_tokenizer else self.server_port + 14}"
        )

    from freetoken.attention import AttentionSpec
    from freetoken.models.config import SWAAttentionGroupConfig
    from freetoken.models.qwen3_5_moe import attention as qwen_attention
    from freetoken.models.qwen3_5_moe import config as qwen_config

    window = int(os.environ.get("WRENCH_SWA_WINDOW", "65536"))
    if window <= 0:
        raise ValueError("WRENCH_SWA_WINDOW must be positive")

    original_parse = qwen_config.parse_config

    def parse_config_with_bounded_full_attention(hf_config):
        model_config = original_parse(hf_config)
        full_group = next(
            group
            for group in model_config.attention_groups
            if group.name == "full"
        )
        full_ids = tuple(full_group.layer_ids)
        requested = os.environ.get("WRENCH_GLOBAL_FULL_LAYERS", "")
        global_ids = _resolve_global_ids(full_ids, requested)
        swa_ids = tuple(layer_id for layer_id in full_ids if layer_id not in global_ids)

        groups = []
        for group in model_config.attention_groups:
            if group.name == "full":
                if global_ids:
                    groups.append(replace(group, layer_ids=global_ids))
                if swa_ids:
                    groups.append(
                        SWAAttentionGroupConfig(
                            name="swa",
                            layer_ids=swa_ids,
                            num_kv_heads=group.num_kv_heads,
                            head_dim=group.head_dim,
                            rotary_config=group.rotary_config,
                            sliding_window=window,
                        )
                    )
            else:
                groups.append(group)
        groups.sort(key=lambda group: group.layer_ids[0] if group.layer_ids else 1 << 30)
        # Bind the selected policy only after the model config has resolved it.
        os.environ["WRENCH_LONG_CONTEXT_POLICY"] = (
            f"global_full={','.join(map(str, global_ids)) or 'none'};swa_window={window}"
        )
        return replace(model_config, attention_groups=tuple(groups))

    qwen_config.parse_config = parse_config_with_bounded_full_attention

    original_init = qwen_attention.Qwen3_5Attention.__init__
    original_forward = qwen_attention.Qwen3_5Attention.forward

    def init_with_attention_spec(self, config, layer_id: int, *, prefix: str = ""):
        original_init(self, config, layer_id, prefix=prefix)
        group = config.attention_group_for_layer(layer_id)
        self.attn_spec = AttentionSpec(
            sliding_window=(group.sliding_window if isinstance(group, SWAAttentionGroupConfig) else None),
        )

    def forward_with_attention_spec(self, x):
        ctx = qwen_attention.get_global_ctx()
        q, k, v, gate = self._project(x)
        output = ctx.attn_backend.forward(
            q,
            k,
            v,
            self.layer_id,
            ctx.batch,
            attn_spec=self.attn_spec,
        )
        return self._combine(output, gate)

    qwen_attention.Qwen3_5Attention.__init__ = init_with_attention_spec
    qwen_attention.Qwen3_5Attention.forward = forward_with_attention_spec

    if os.environ.get("WRENCH_FREETOKEN_NO_JIT") == "1":
        import torch
        import freetoken.kernel as kernel
        import freetoken.kernel.fast_index_copy as fast_index_copy
        import freetoken.moe.offload_cache as offload_cache

        def torch_indexing(weights, indices, *, output=None, vocab_range=None):
            selected = weights.index_select(0, indices.to(device=weights.device, dtype=torch.long))
            if output is not None:
                output.copy_(selected)
                return output
            return selected

        kernel.indexing = torch_indexing

        def torch_store_cache(k_cache, v_cache, indices, k, v):
            locations = indices.to(device=k_cache.device, dtype=torch.long)
            k_cache.reshape(k_cache.shape[0], -1).index_copy_(
                0, locations, k.reshape(k.shape[0], -1).to(device=k_cache.device, dtype=k_cache.dtype)
            )
            v_cache.reshape(v_cache.shape[0], -1).index_copy_(
                0, locations, v.reshape(v.shape[0], -1).to(device=v_cache.device, dtype=v_cache.dtype)
            )

        kernel.store_cache = torch_store_cache

        def torch_fast_index_copy(dst, dst_indices, src, src_indices, num_indices=None, **kwargs):
            count = int(num_indices.reshape(-1)[0].item()) if num_indices is not None else int(dst_indices.numel())
            if count <= 0:
                return
            destinations = dst_indices[:count].to(device=dst.device, dtype=torch.long)
            sources = src_indices[:count].to(device=src.device, dtype=torch.long)
            # Expert banks may use float8 storage, so copy raw bytes rather than
            # relying on index_copy_ supporting the storage dtype directly.
            dst_bytes = dst.view(torch.uint8).reshape(dst.shape[0], -1)
            src_bytes = src.view(torch.uint8).reshape(src.shape[0], -1)
            rows = src_bytes.index_select(0, sources).to(device=dst.device)
            dst_bytes.index_copy_(0, destinations, rows)

        kernel.fast_index_copy_jit = torch_fast_index_copy
        fast_index_copy.fast_index_copy_jit = torch_fast_index_copy

        # The fused implementation stores raw CUDA pointers in descriptor tensors,
        # so it cannot have a faithful torch-only fallback. Force the existing
        # per-bank path, which is slower but does not require a CUDA toolkit or JIT.
        original_build_fused_copy_plan = offload_cache.OffloadMoeCache._build_fused_copy_plan

        def build_fused_copy_plan_without_jit(self, *args, **kwargs):
            original_build_fused_copy_plan(self, *args, **kwargs)
            self._copy_fused_ok = False
            self._gather_dst_ptrs = None
            self._gather_feat_bytes = None

        offload_cache.OffloadMoeCache._build_fused_copy_plan = build_fused_copy_plan_without_jit

        def torch_fast_compare_key(x, y):
            left = x.detach().to(device="cpu", dtype=torch.int64).reshape(-1)
            right = y.detach().to(device="cpu", dtype=torch.int64).reshape(-1)
            limit = min(left.numel(), right.numel())
            if limit:
                mismatch = torch.nonzero(left[:limit] != right[:limit], as_tuple=False)
                if mismatch.numel():
                    return int(mismatch[0, 0].item())
            return limit

        kernel.fast_compare_key = torch_fast_compare_key

_install_qwen_long_context_overlay()
