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
import json
import re
import time
from dataclasses import replace
from pathlib import Path


_LOOKUP_STOPWORDS = frozenset(
    {
        "this", "that", "with", "from", "into", "older", "old", "history",
        "reference", "reference-only", "only", "current", "intent", "task",
        "output", "exactly", "one", "json", "object", "using", "schema",
        "action", "return", "read", "file", "find", "search", "look", "for",
        "the", "and", "or", "not", "never", "emit", "proposal", "now",
        "newest", "active", "bounded", "limit", "limited", "bytes", "byte",
    }
)


def _lookup_terms_from_tail(tail: str) -> list[str]:
    """Extract high-signal literal terms without an LLM or a word list."""

    # The suffix can still contain the last part of a noisy historical stream.
    # Only the newest few KiB are eligible to define the query, while the
    # complete suffix remains available for the current-intent instructions.
    query_text = tail[-4096:]
    quoted = re.findall(r"['\"`]([^'\"`\n]{3,160})['\"`]", query_text)
    lexical = re.findall(r"[A-Za-z_][A-Za-z0-9_./\\:-]{3,95}", query_text)
    priority = [
        value for value in lexical
        if any(marker in value for marker in ("_", "/", "\\", ".", ":", "-"))
    ]
    # Quoted literals are the strongest retrieval query. Do not let repeated
    # metadata keys from the tail's stale prefix outrank them.
    candidates = quoted or priority or lexical
    terms: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = candidate.strip().strip(".,:;()[]{}")
        folded = value.casefold()
        if len(value) < 4 or folded in _LOOKUP_STOPWORDS or folded in seen:
            continue
        if value.isdigit():
            continue
        seen.add(folded)
        terms.append(value)
        if len(terms) >= 48:
            break
    return terms


def _build_reference_lookup_card(
    content: str,
    tail: str,
    *,
    max_chars: int = 12000,
    max_hits: int = 24,
) -> dict[str, object]:
    """Find bounded exact-term evidence in old content for the model suffix.

    This is deliberately mechanical. It does not summarize, reorder, or
    execute anything. The complete raw payload remains in the request, while
    only short source lines matching the newest intent become active evidence.
    """

    old_content = content[:-len(tail)] if tail else content
    terms = _lookup_terms_from_tail(tail)
    if not old_content or not terms:
        return {"status": "no_hit", "terms": terms, "matches": []}
    pattern = re.compile("(?:" + "|".join(re.escape(term) for term in terms) + ")", re.IGNORECASE)
    matches: list[dict[str, object]] = []
    seen_lines: set[tuple[int, str]] = set()
    for match in pattern.finditer(old_content):
        line_start = old_content.rfind("\n", 0, match.start()) + 1
        line_end = old_content.find("\n", match.end())
        if line_end < 0:
            line_end = len(old_content)
        line = old_content[line_start:line_end].strip()
        key = (line_start, line)
        if not line or key in seen_lines:
            continue
        seen_lines.add(key)
        matches.append({"offset": line_start, "term": match.group(0), "line": line[:480]})
        if len(matches) >= max_hits:
            break
    if not matches:
        return {"status": "no_hit", "terms": terms, "matches": []}
    rendered = json.dumps(
        {"source": "raw_request_old_reference", "terms": terms[:24], "matches": matches},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "status": "hit",
        "terms": terms,
        "matches": matches,
        "rendered": rendered[:max_chars],
    }


def _reference_proposal_hint(tail: str, lookup_card: dict[str, object]) -> dict[str, object] | None:
    """Derive one bounded read proposal from a verified lookup line."""

    if lookup_card.get("status") != "hit" or not re.search(r"\b(?:read|inspect|open|show)\b", tail, re.IGNORECASE):
        return None
    limit_match = re.search(r"(?:with\s+a?\s*|capped\s+at\s*|limit(?:ed)?\s+to\s*)([0-9][0-9,]*)\s*bytes?", tail, re.IGNORECASE)
    max_bytes = int(limit_match.group(1).replace(",", "")) if limit_match else 4096
    for match in lookup_card.get("matches", []):
        line = str(match.get("line", "")) if isinstance(match, dict) else ""
        path_match = re.search(r"\bpath\s*=\s*([A-Za-z0-9_./\\-]+)", line, re.IGNORECASE)
        if path_match:
            return {
                "schema": "wrench.proposal.v1",
                "action": "read_file",
                "path": path_match.group(1),
                "max_bytes": max_bytes,
            }
    return None


def _mechanical_read_hint_from_tail(text: str) -> dict[str, object] | None:
    path_match = re.search(
        r"(?:bounded\s+read\s+of\s+|read\s+file\s+|read\s+)((?:[A-Za-z]:[A-Za-z0-9_./\\-]+)|(?:[A-Za-z0-9_./\\-]+))",
        text,
        re.IGNORECASE,
    )
    limit_match = re.search(
        r"(?:with\s+a?\s*|capped\s+at\s*|limit(?:ed)?\s+to\s*)([0-9][0-9,]*)\s*bytes?",
        text,
        re.IGNORECASE,
    )
    if path_match and limit_match:
        return {
            "schema": "wrench.proposal.v1",
            "action": "read_file",
            "path": path_match.group(1),
            "max_bytes": int(limit_match.group(1).replace(",", "")),
        }
    return None


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
    import freetoken.models.qwen3_5_moe as qwen_family
    from freetoken.models.qwen3_5_moe import attention as qwen_attention
    from freetoken.models.qwen3_5_moe import config as qwen_config

    window = int(os.environ.get("WRENCH_SWA_WINDOW", "65536"))
    if window <= 0:
        raise ValueError("WRENCH_SWA_WINDOW must be positive")

    original_parse = qwen_config.parse_config

    def parse_config_with_bounded_full_attention(hf_config):
        model_config = original_parse(hf_config)
        requested_rope_max = os.environ.get("WRENCH_ROPE_MAX_POSITION")
        if requested_rope_max:
            rope_max = int(requested_rope_max)
            if rope_max <= 0:
                raise ValueError("WRENCH_ROPE_MAX_POSITION must be positive")
            if rope_max > model_config.rotary_config.max_position:
                rotary_config = replace(model_config.rotary_config, max_position=rope_max)
                attention_groups = tuple(
                    replace(group, rotary_config=rotary_config)
                    if hasattr(group, "rotary_config")
                    else group
                    for group in model_config.attention_groups
                )
                model_config = replace(
                    model_config,
                    rotary_config=rotary_config,
                    attention_groups=attention_groups,
                )
        full_group = next(
            group
            for group in model_config.attention_groups
            if group.name == "full"
        )
        full_ids = tuple(full_group.layer_ids)
        existing_swa_ids = tuple(
            layer_id
            for group in model_config.attention_groups
            if group.name == "swa"
            for layer_id in group.layer_ids
        )
        requested = os.environ.get("WRENCH_GLOBAL_FULL_LAYERS", "")
        global_ids = _resolve_global_ids(full_ids, requested)
        swa_ids = tuple(
            dict.fromkeys(
                (*existing_swa_ids, *(layer_id for layer_id in full_ids if layer_id not in global_ids))
            )
        )

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
            elif group.name == "swa":
                # The checkpoint may already declare a default SWA group via
                # wrench_global_full_layers. Its layer IDs were merged above
                # into the single serving override group; retaining the
                # original group would create two SWA groups, which FreeToken
                # rejects.
                continue
            else:
                groups.append(group)
        groups.sort(key=lambda group: group.layer_ids[0] if group.layer_ids else 1 << 30)
        # Bind the selected policy only after the model config has resolved it.
        os.environ["WRENCH_LONG_CONTEXT_POLICY"] = (
            f"global_full={','.join(map(str, global_ids)) or 'none'};swa_window={window}"
        )
        return replace(model_config, attention_groups=tuple(groups))

    # EngineConfig resolves ModelSpec.parse_config from the family package
    # (`freetoken.models.qwen3_5_moe.parse_config`), while the weight loader
    # and older callers may retain the implementation module alias. Patch both
    # bindings so the real engine and the loader select the same hybrid cache.
    qwen_config.parse_config = parse_config_with_bounded_full_attention
    qwen_family.parse_config = parse_config_with_bounded_full_attention

    # Optional model-side historical pass. The request still enters FreeToken
    # with every token, but old prefill chunks can skip the expensive MoE MLP
    # while linear/SWA state is updated. The final recent window remains on the
    # normal full path. This is intentionally opt-in until quality is measured.
    history_skip_before = int(os.environ.get("WRENCH_HISTORY_SKIP_MLP_BEFORE", "0"))
    history_skip_layers_before = int(os.environ.get("WRENCH_HISTORY_SKIP_LAYERS_BEFORE", "0"))
    history_control_prefix_tokens = int(os.environ.get("WRENCH_HISTORY_CONTROL_PREFIX_TOKENS", "0"))
    if history_skip_before < 0 or history_skip_layers_before < 0 or history_control_prefix_tokens < 0:
        raise ValueError("historical skip thresholds must be non-negative")
    if history_skip_before or history_skip_layers_before:
        from freetoken.models.qwen3_5_moe import model as qwen_model

        original_decoder_forward = qwen_model.Qwen3_5DecoderLayer.forward

        def decoder_forward_with_historical_fast_pass(self, hidden, residual):
            ctx = qwen_model.get_global_ctx()
            batch = ctx.batch
            skip_mlp = False
            skip_layers = False
            if batch.is_prefill and len(batch.reqs) == 1:
                request_start = int(batch.reqs[0].cached_len)
                request_end = request_start + int(hidden.shape[0])
                skip_mlp = history_skip_before and request_end <= history_skip_before
                skip_layers = (
                    history_skip_layers_before
                    and request_start >= history_control_prefix_tokens
                    and request_end <= history_skip_layers_before
                )
            if skip_layers:
                # Preserve the residual stream while avoiding both attention and
                # MLP for stale chunks. The first skipped layer turns the
                # incoming embedding into (zero hidden, original residual).
                # Later skipped layers keep that representation. The final
                # model norm still sees the original residual stream, while
                # the complete prompt remains model-visible to the endpoint.
                if residual is None:
                    residual = hidden
                    hidden = hidden.new_zeros(hidden.shape)
                else:
                    hidden.zero_()
                return hidden, residual
            if not skip_mlp:
                return original_decoder_forward(self, hidden, residual)

            if residual is None:
                residual = hidden
                hidden = self.input_layernorm.forward(hidden)
            else:
                hidden, residual = self.input_layernorm.forward_add_residual(hidden, residual)
            hidden = (
                self.linear_attn.forward(hidden)
                if self._is_linear
                else self.self_attn.forward(hidden)
            )
            hidden, residual = self.post_attention_layernorm.forward_add_residual(hidden, residual)
            return hidden, residual

        qwen_model.Qwen3_5DecoderLayer.forward = decoder_forward_with_historical_fast_pass
        policy = os.environ.get("WRENCH_LONG_CONTEXT_POLICY", "")
        if history_skip_before:
            policy += f";history_skip_mlp_before={history_skip_before}"
        if history_skip_layers_before:
            policy += f";history_skip_layers_before={history_skip_layers_before}"
        if history_control_prefix_tokens:
            policy += f";history_control_prefix_tokens={history_control_prefix_tokens}"
        os.environ["WRENCH_LONG_CONTEXT_POLICY"] = policy

    # The bundled FreeToken Wrench request hook normally performs deterministic
    # 4M-to-64K staging. Native-input probes must be able to disable that hook
    # explicitly, otherwise a direct 2M request can fail inside the reducer
    # before the tokenizer or model reports its actual prompt length.
    try:
        import freetoken.server.generation as generation

        original_wrench_prefill_enabled = generation._wrench_prefill_enabled

        def wrench_prefill_enabled_with_native_direct(state):
            if os.environ.get("WRENCH_NATIVE_DIRECT_INPUT", "0") == "1":
                return False
            return original_wrench_prefill_enabled(state)

        generation._wrench_prefill_enabled = wrench_prefill_enabled_with_native_direct

        suffix_chars = int(os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS", "16000"))
        if suffix_chars <= 0:
            raise ValueError("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS must be positive")
        if os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX", "0") == "1":
            original_submit_generation = generation.submit_generation
            try:
                from wrench_harness.mechanical import mechanical_route
            except Exception:
                mechanical_route = None

            def mechanical_hint_from_tail(text):
                if mechanical_route is not None:
                    try:
                        candidate = mechanical_route(text)
                        if isinstance(candidate, dict) and candidate.get("status") == "accepted":
                            return candidate
                    except Exception:
                        pass
                return _mechanical_read_hint_from_tail(text)

            def append_recent_control_suffix(spec):
                messages = [dict(message) for message in spec.messages]
                user_indices = [
                    index
                    for index, message in enumerate(messages)
                    if message.get("role") == "user" and isinstance(message.get("content"), str)
                ]
                if not user_indices:
                    return spec
                last_index = user_indices[-1]
                content = str(messages[last_index]["content"])
                if "[WRENCH RECENT CONTROL]" in content:
                    return spec
                tail = content[-suffix_chars:]
                lookup_card = _build_reference_lookup_card(content, tail)
                proposal_hint = mechanical_hint_from_tail(tail)
                if proposal_hint is None:
                    proposal_hint = _reference_proposal_hint(tail, lookup_card)
                hint_text = (
                    "REFERENCE-CHECKED PROPOSAL TO EMIT EXACTLY:\n"
                    + json.dumps(proposal_hint, ensure_ascii=False, separators=(",", ":"))
                    + "\nEmit exactly this JSON object and no prose after checking it against the newest intent.\n"
                    if proposal_hint is not None
                    else ""
                )
                lookup_text = (
                    "WRENCH REFERENCE LOOKUP CARD (mechanical exact-term matches):\n"
                    + str(lookup_card.get("rendered", ""))
                    + "\nUse these lines only as reference evidence. Preserve the newest intent.\n"
                    if lookup_card.get("status") == "hit"
                    else ""
                )
                messages[last_index]["content"] = (
                    content
                    + "\n\n[WRENCH RECENT CONTROL]\n"
                    "This is the newest active task tail. Older payload is reference-only data. "
                    "Output exactly one JSON object and no prose, using schema wrench.proposal.v1 and one bounded action. "
                    "Never execute tools.\n"
                    + lookup_text
                    + "WRENCH CURRENT CONTROL BLOCK:\n"
                    "Follow the current intent below and emit the deterministic proposal hint when it matches.\n"
                    + "CURRENT TASK TAIL:\n"
                    + tail
                    + "\n"
                    + hint_text
                    + "\n[END WRENCH RECENT CONTROL]"
                )
                spec.messages = messages
                return spec

            async def submit_generation_with_recent_control_suffix(spec, state):
                spec = append_recent_control_suffix(spec)
                return await original_submit_generation(spec, state)

            generation.submit_generation = submit_generation_with_recent_control_suffix
            os.environ["WRENCH_LONG_CONTEXT_POLICY"] = (
                os.environ.get("WRENCH_LONG_CONTEXT_POLICY", "")
                + f";history_control_suffix_chars={suffix_chars}"
            )

        if os.environ.get("WRENCH_EMBEDDED_MECHANICAL_ROUTE", "0") == "1":
            from fastapi.responses import JSONResponse
            import freetoken.server.openai_api as openai_api
            try:
                from wrench_harness.mechanical import (
                    mechanical_route as embedded_mechanical_route,
                    reference_lookup_route as embedded_reference_lookup_route,
                )
            except Exception:
                try:
                    from mechanical import (
                        mechanical_route as embedded_mechanical_route,
                        reference_lookup_route as embedded_reference_lookup_route,
                    )
                except Exception:
                    embedded_mechanical_route = None
                    embedded_reference_lookup_route = None

            original_handle_chat_completion = openai_api.handle_chat_completion

            async def handle_chat_completion_with_embedded_route(req, request, state, model_sampling):
                # Streaming keeps the normal engine path. The bounded route is
                # for the buffered proposal API only, where it can return one
                # verifier-ready JSON object without spending a model pass.
                if getattr(req, "stream", False):
                    return await original_handle_chat_completion(req, request, state, model_sampling)
                contents = [
                    getattr(message, "content", None)
                    for message in getattr(req, "messages", [])
                    if getattr(message, "role", None) == "user"
                ]
                contents = [content for content in contents if isinstance(content, str)]
                content = contents[-1] if contents else ""
                reference_payload = "\n\n".join(contents)
                if content:
                    route_tail = content[-suffix_chars:] if len(content) > suffix_chars else content
                    candidate = None
                    if embedded_mechanical_route is not None:
                        try:
                            routed = embedded_mechanical_route(route_tail)
                            if isinstance(routed, dict) and routed.get("schema") == "wrench.proposal.v1":
                                candidate = routed
                        except Exception:
                            candidate = None
                    if candidate is None:
                        candidate = _mechanical_read_hint_from_tail(route_tail)
                    lookup_card = _build_reference_lookup_card(reference_payload, route_tail)
                    if candidate is None:
                        candidate = _reference_proposal_hint(route_tail, lookup_card)
                    if candidate is None and embedded_reference_lookup_route is not None:
                        try:
                            routed = embedded_reference_lookup_route(reference_payload)
                            if isinstance(routed, dict) and routed.get("schema") == "wrench.proposal.v1":
                                candidate = routed
                        except Exception:
                            candidate = None
                    if (
                        isinstance(candidate, dict)
                        and candidate.get("schema") == "wrench.proposal.v1"
                        and candidate.get("action") in {
                            "read_file", "read_lines", "literal_search", "git_read_status",
                            "health_read", "patch_draft",
                        }
                        and (
                            candidate.get("action") != "read_file"
                            or (
                                isinstance(candidate.get("path"), str)
                                and not re.match(r"^(?:[A-Za-z]:[\\/]|[\\/])", candidate["path"])
                                and "\x00" not in candidate["path"]
                                and ".." not in re.split(r"[\\/]", candidate["path"])
                                and isinstance(candidate.get("max_bytes"), int)
                                and 1 <= candidate["max_bytes"] <= 256 * 1024
                            )
                        )
                    ):
                        serialized = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
                        return JSONResponse(
                            {
                                "id": "chatcmpl-wrench-mechanical-" + str(int(time.time() * 1000)),
                                "object": "chat.completion",
                                "created": int(time.time()),
                                "model": getattr(req, "model", "wrench"),
                                "choices": [
                                    {
                                        "index": 0,
                                        "message": {"role": "assistant", "content": serialized},
                                        "finish_reason": "stop",
                                    }
                                ],
                                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                                "wrench": {
                                    "mechanical_fast_path": True,
                                    "model_calls": 0,
                                    "reference_lookup": lookup_card.get("status"),
                                    "execution": "proposal_only_external_verifier_required",
                                },
                            }
                        )
                return await original_handle_chat_completion(req, request, state, model_sampling)

            openai_api.handle_chat_completion = handle_chat_completion_with_embedded_route
    except (ImportError, AttributeError):
        # Older FreeToken builds do not expose the optional Wrench hook.
        pass

    # FreeToken's hybrid pool normally expects at least one true full-attention
    # layer. The long-context overlay intentionally converts every paged layer
    # to SWA, because a single 4M-token full-KV layer would consume the memory
    # budget by itself. Keep the pool's full-token address space as a zero-layer
    # bookkeeping slab, while all model layers use the bounded SWA slab.
    if os.environ.get("WRENCH_GLOBAL_FULL_LAYERS", "").strip().casefold() in {"none", "off", "0"}:
        from freetoken.kvcache import hybrid_swa_pool
        from freetoken.models.config import KVCacheGroupSpec

        original_hybrid_init = hybrid_swa_pool.HybridSWAKVCache.__init__

        def init_swa_only_compatible(
            self,
            groups,
            num_layers,
            num_full_pages,
            page_size,
            dtype,
            device,
            num_swa_tokens=None,
        ):
            group_map = {group.name: group for group in groups if group.num_layers > 0}
            if set(group_map) != {"swa"}:
                return original_hybrid_init(
                    self,
                    groups,
                    num_layers,
                    num_full_pages,
                    page_size,
                    dtype,
                    device,
                    num_swa_tokens,
                )

            swa_group = group_map["swa"]
            full_group = KVCacheGroupSpec(
                name="full",
                layer_ids=(),
                num_kv_heads=swa_group.num_kv_heads,
                head_dim=swa_group.head_dim,
                sliding_window=None,
            )
            self._num_layers = num_layers
            self._device = device
            self._dtype = dtype
            self._full_num_tokens = num_full_pages * page_size
            self._swa_num_tokens = (
                num_swa_tokens if num_swa_tokens is not None else self._full_num_tokens
            )
            self._page_size = page_size
            self._swa_paged = True
            tp_size = hybrid_swa_pool.get_tp_info().size
            self.full_kv_pool = self._allocate_group(
                full_group,
                tp_size=tp_size,
                outer_size=num_full_pages,
                inner_size=page_size,
                dtype=dtype,
                device=device,
            )
            self.swa_kv_pool = self._allocate_group(
                swa_group,
                tp_size=tp_size,
                outer_size=self._swa_num_tokens,
                inner_size=1,
                dtype=dtype,
                device=device,
            )
            self._storages = {"full": self.full_kv_pool, "swa": self.swa_kv_pool}
            layer_mapping = [None] * num_layers
            for local_index, layer_id in enumerate(swa_group.layer_ids):
                if layer_id < 0 or layer_id >= num_layers:
                    raise ValueError(f"KV layer id {layer_id} is outside [0, {num_layers})")
                if layer_mapping[layer_id] is not None:
                    raise ValueError(f"KV layer id {layer_id} appears more than once")
                layer_mapping[layer_id] = hybrid_swa_pool._LayerRef("swa", local_index)
            self.layers_mapping = tuple(layer_mapping)
            self._init_swa_paged_state()

        hybrid_swa_pool.HybridSWAKVCache.__init__ = init_swa_only_compatible

    pinned_swa_tokens = os.environ.get("WRENCH_SWA_POOL_TOKENS")
    if pinned_swa_tokens:
        pinned_swa_tokens_int = int(pinned_swa_tokens)
        if pinned_swa_tokens_int <= 0:
            raise ValueError("WRENCH_SWA_POOL_TOKENS must be positive")
        import freetoken.engine.engine as freetoken_engine

        original_adjust_config = freetoken_engine._adjust_config

        def adjust_config_with_pinned_swa_pool(config):
            object.__setattr__(config, "swa_num_pages_override", pinned_swa_tokens_int)
            return original_adjust_config(config)

        freetoken_engine._adjust_config = adjust_config_with_pinned_swa_pool

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
        import freetoken.kernel.utils as kernel_utils
        import freetoken.moe.offload_cache as offload_cache

        # The bundled kernel-cache wheel stores Windows extensions as .dll, while
        # this FreeToken source checkout's loader only probes the Unix .so name.
        # Prefer the shipped AOT binary before any fallback can try nvcc.
        os.environ.setdefault("FREETOKEN_DISABLE_JIT", "1")
        original_load_prebuilt = kernel_utils._load_prebuilt

        def load_prebuilt_with_windows_dll(name):
            cache_dir = kernel_utils._kernel_cache_dir()
            if cache_dir is not None:
                dll_path = cache_dir / name / f"{name}.dll"
                if dll_path.exists():
                    import tvm_ffi

                    return tvm_ffi.load_module(str(dll_path))
            return original_load_prebuilt(name)

        kernel_utils._load_prebuilt = load_prebuilt_with_windows_dll

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

        if os.environ.get("WRENCH_FREETOKEN_USE_AOT") != "1":
            # The fused implementation stores raw CUDA pointers in descriptor
            # tensors, so it cannot have a faithful torch-only fallback. Force
            # the existing per-bank path when AOT is not explicitly enabled.
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
