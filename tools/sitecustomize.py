"""Optional FreeToken router telemetry, enabled only by an explicit env var."""

from __future__ import annotations

import atexit
import json
import os
import sys
import tempfile
import threading
from pathlib import Path


if os.environ.get("WRENCH_ROUTER_PROFILE_PATH"):
    try:
        # FreeToken's HF NVFP4 expert-bank loader calls this POSIX page-cache
        # hint unconditionally. Windows has no equivalent, so make it a safe
        # no-op for profiling and bounded runtime smoke tests.
        if os.name == "nt" and not hasattr(os, "posix_fadvise"):
            os.posix_fadvise = lambda fd, offset, length, advice: None
            os.POSIX_FADV_DONTNEED = 0
        if os.name == "nt":
            import asyncio

            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            import uvicorn.loops.asyncio as _uvicorn_asyncio

            _uvicorn_asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
        import torch

        # The profiler intentionally imports FreeToken source code so the
        # current model path is used.  Its compiled Windows extensions remain
        # installed in the venv site-packages tree, though.  Extend the
        # namespace package path so the source package can see those .pyd
        # modules without copying or mutating the FreeToken checkout.
        import freetoken.kernel as _kernel_package

        _installed_kernel = Path(sys.prefix) / "Lib" / "site-packages" / "freetoken" / "kernel"
        if _installed_kernel.is_dir() and str(_installed_kernel) not in _kernel_package.__path__:
            _kernel_package.__path__.append(str(_installed_kernel))

        from freetoken.models.qwen3_5_moe.moe import Qwen3_5MoE

        _path = Path(os.environ["WRENCH_ROUTER_PROFILE_PATH"]).resolve()

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

        if os.name == "nt":
            import mmap
            from freetoken.checkpoint.ftw import FTWReader

            def _windows_map(self, file):
                entry = self._maps.get(file)
                if entry is None:
                    with self._lock:
                        entry = self._maps.get(file)
                        if entry is None:
                            fd = os.open(os.path.join(self.dir, file), os.O_RDONLY)
                            try:
                                mapped = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
                            finally:
                                os.close(fd)
                            entry = (mapped, memoryview(mapped))
                            self._maps[file] = entry
                return entry[1]

            FTWReader._map = _windows_map

        # The installed FreeToken wheel has prebuilt serving kernels but this
        # source checkout may still route embedding lookup through its JIT
        # index helper.  The profiling run does not need that optimization,
        # and the host has no CUDA toolkit for runtime compilation, so use the
        # equivalent torch gather path for the small embedding/head lookups.
        if os.environ.get("WRENCH_ROUTER_PROFILE_NO_JIT") == "1":
            import freetoken.kernel as _kernel

            def _torch_indexing(weights, indices, *, output=None, vocab_range=None):
                selected = weights.index_select(0, indices.to(device=weights.device, dtype=torch.long))
                if output is not None:
                    output.copy_(selected)
                    return output
                return selected

            _kernel.indexing = _torch_indexing

            def _torch_store_cache(k_cache, v_cache, indices, k, v):
                locations = indices.to(device=k_cache.device, dtype=torch.long)
                _k_cache = k_cache.reshape(k_cache.shape[0], -1)
                _v_cache = v_cache.reshape(v_cache.shape[0], -1)
                _k = k.reshape(k.shape[0], -1).to(device=_k_cache.device, dtype=_k_cache.dtype)
                _v = v.reshape(v.shape[0], -1).to(device=_v_cache.device, dtype=_v_cache.dtype)
                _k_cache.index_copy_(0, locations, _k)
                _v_cache.index_copy_(0, locations, _v)

            _kernel.store_cache = _torch_store_cache

            def _torch_fast_index_copy(dst, dst_indices, src, src_indices, num_indices=None, **kwargs):
                count = int(num_indices.reshape(-1)[0].item()) if num_indices is not None else int(dst_indices.numel())
                if count <= 0:
                    return
                destinations = dst_indices[:count].to(device=dst.device, dtype=torch.long)
                sources = src_indices[:count].to(device=src.device, dtype=torch.long)
                # Float8 expert banks do not implement index_copy_ directly.
                # Copy their raw bytes instead, preserving the exact packed row.
                dst_bytes = dst.view(torch.uint8).reshape(dst.shape[0], -1)
                src_bytes = src.view(torch.uint8).reshape(src.shape[0], -1)
                rows = src_bytes.index_select(0, sources).to(device=dst.device)
                dst_bytes.index_copy_(0, destinations, rows)

            _kernel.fast_index_copy_jit = _torch_fast_index_copy

            def _torch_fast_compare_key(x, y):
                left = x.detach().to(device="cpu", dtype=torch.int64).reshape(-1)
                right = y.detach().to(device="cpu", dtype=torch.int64).reshape(-1)
                limit = min(left.numel(), right.numel())
                if limit:
                    mismatch = torch.nonzero(left[:limit] != right[:limit], as_tuple=False)
                    if mismatch.numel():
                        return int(mismatch[0, 0].item())
                return limit

            _kernel.fast_compare_key = _torch_fast_compare_key
        _path.parent.mkdir(parents=True, exist_ok=True)
        _lock = threading.Lock()
        _stats: dict[str, dict] = {}
        _call_count = 0

        def _write() -> None:
            payload = {
                "schema": "wrench.qwen-router-activation-profile.v1",
                "source": "FreeToken Qwen3_5MoE gate.forward hook",
                "status": "CAPTURING",
                "layers": _stats,
            }
            fd, temp_name = tempfile.mkstemp(prefix=".router-profile-", suffix=".json", dir=_path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, indent=2)
                    handle.write("\n")
                os.replace(temp_name, _path)
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)

        def _capture(key: str, logits: torch.Tensor, top_k: int) -> None:
            global _call_count
            values = logits.detach().float()
            width = int(values.shape[-1])
            k = min(top_k, width)
            ids = values.topk(k, dim=-1).indices.reshape(-1).to("cpu")
            counts = torch.bincount(ids, minlength=width).tolist()
            probabilities = torch.softmax(values, dim=-1)
            entropy = float((-(probabilities * probabilities.clamp_min(1e-12).log()).sum(dim=-1)).sum().item())
            tokens = int(values.shape[0])
            with _lock:
                row = _stats.setdefault(
                    key,
                    {
                        "expert_count": width,
                        "top_k": k,
                        "token_count": 0,
                        "top_k_assignments": 0,
                        "expert_activation_counts": [0] * width,
                        "router_entropy_sum": 0.0,
                        "router_call_count": 0,
                    },
                )
                row["token_count"] += tokens
                row["top_k_assignments"] += tokens * k
                row["expert_activation_counts"] = [a + b for a, b in zip(row["expert_activation_counts"], counts)]
                row["router_entropy_sum"] += entropy
                row["router_call_count"] += 1
                _call_count += 1
                if _call_count % 4 == 0:
                    _write()

        _original_init = Qwen3_5MoE.__init__

        def _patched_init(self, config, layer_id=None, *, prefix=""):
            _original_init(self, config, layer_id, prefix=prefix)
            route_key = prefix or f"layer_{layer_id}"
            original_forward = self.gate.forward
            top_k = int(config.num_experts_per_tok)

            def _wrapped_gate(hidden_states, *args, **kwargs):
                logits = original_forward(hidden_states, *args, **kwargs)
                _capture(route_key, logits, top_k)
                return logits

            self.gate.forward = _wrapped_gate

        Qwen3_5MoE.__init__ = _patched_init
        atexit.register(_write)
        _write()
    except Exception as exc:  # pragma: no cover - runtime-only hook
        print(f"[wrench-router-profile] disabled: {type(exc).__name__}: {exc}", flush=True)
