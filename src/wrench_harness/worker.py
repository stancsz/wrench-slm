"""Model-package worker API for bounded Wrench proposals.

The worker keeps the deterministic toolbelt inside the downloaded model
directory. High-confidence mechanical requests do not spend a model pass.
Ambiguous requests use the standard Transformers model and still pass through
the same strict parser and verifier before a proposal is returned.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .mechanical import active_intent_suffix, mechanical_route, reference_lookup_route, reference_patch_route
from .core import execute_model_output
from .patching import add_patch_retry_instruction, add_patch_schema_examples, is_patch_prompt
from .prefill import (
    MechanicalPrefillIndex,
    build_dynamic_prefill,
    ordered_payload_sha256,
    split_monolithic_current_message,
)


_ADAPTIVE_CONTEXT_MARKERS = (
    "debug",
    "compare",
    "trace",
    "reproduce",
    "root cause",
    "test failure",
    "review-only",
    "review only",
    "multi-file",
    "across several files",
)


def _estimated_tokens(value: str) -> int:
    # Spaces and newlines dominate the cheap estimate. Avoid a third full
    # scan for tabs on monster payloads; the exact tokenizer remains the
    # authority once the bounded staged prompt reaches the model.
    return max(1, value.count(" ") + value.count("\n") + 1)


def _adaptive_prefill_budget(
    messages: list[dict[str, str]],
    *,
    base_budget: int,
    raw_chars: int,
) -> tuple[int, dict[str, Any] | None]:
    """Select a bounded working-context tier without invoking another model.

    The default remains 64K.  A larger tier is only selected when the newest
    intent explicitly looks like a context-sensitive investigation and the
    payload is materially larger than the base tier.  The policy is
    deterministic, configurable, and never allows the reducer to exceed the
    caller's hard maximum.
    """

    if not isinstance(base_budget, int) or base_budget < 1:
        raise ValueError("base_budget must be positive")
    if raw_chars <= base_budget * 4:
        return base_budget, None
    if os.environ.get("WRENCH_DYNAMIC_PREFILL_ADAPTIVE", "1").casefold() in {"0", "false", "off", "no"}:
        return base_budget, None
    users = [
        item.get("content", "")
        for item in messages
        if isinstance(item, dict) and item.get("role") == "user" and isinstance(item.get("content"), str)
    ]
    latest = users[-1].casefold() if users else ""
    marker = next((value for value in _ADAPTIVE_CONTEXT_MARKERS if value in latest), None)
    if marker is None:
        return base_budget, None
    try:
        hard_max = int(os.environ.get("WRENCH_MODEL_PREFILL_MAX_BUDGET", "128000"))
    except ValueError:
        hard_max = base_budget
    hard_max = max(base_budget, hard_max)
    selected = min(hard_max, max(base_budget, 128_000))
    if selected == base_budget:
        return base_budget, None
    return selected, {
        "policy": "adaptive_complexity_tier",
        "marker": marker,
        "base_budget": base_budget,
        "selected_budget": selected,
        "hard_max_budget": hard_max,
        "raw_chars": raw_chars,
    }


def _dynamic_prefill_messages(
    messages: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    """Keep monster payloads losslessly indexed but bounded for model work."""

    budget = int(os.environ.get("WRENCH_MODEL_PREFILL_BUDGET", "64000"))
    original_payload_sha256 = ordered_payload_sha256(messages)
    content_values = [
        message["content"]
        for message in messages
        if isinstance(message, dict) and isinstance(message.get("content"), str)
    ]
    raw_chars = sum(len(value) for value in content_values)
    large_by_chars = raw_chars > budget * 4
    estimated_raw_tokens = (
        budget + 1
        if large_by_chars
        else sum(_estimated_tokens(value) for value in content_values)
    )
    if not large_by_chars and estimated_raw_tokens <= budget:
        return messages, None
    budget, adaptive_selection = _adaptive_prefill_budget(
        messages,
        base_budget=budget,
        raw_chars=raw_chars,
    )
    suffix_chars = int(os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS", "16000"))
    prepared_messages, split_current_message = split_monolithic_current_message(
        messages,
        model_prefill_budget=budget,
        suffix_chars=suffix_chars,
    )
    hot_budget = min(48_000, max(1, budget - 1))
    reference_budget = max(1, budget - hot_budget)
    mechanical_index = MechanicalPrefillIndex()
    mechanical_index.add_all(prepared_messages)
    source_payload_sha256 = mechanical_index.payload_sha256(prepared_messages)
    try:
        staged, receipt = build_dynamic_prefill(
            prepared_messages,
            model_prefill_budget=budget,
            hot_token_budget=hot_budget,
            reference_index_budget=reference_budget,
            mechanical_index=mechanical_index,
        )
    except (TypeError, ValueError):
        # Never turn a reducer failure into silent data loss. The caller can
        # still use the original model path and the verifier remains in force.
        return messages, {
            "schema": "wrench.dynamic-prefill-receipt.v1",
            "mode": "fallback_original_messages",
            "raw_token_count_estimate": estimated_raw_tokens,
            "error": "dynamic_prefill_failed",
            "native_input_claim": False,
        }
    receipt["source_payload_sha256"] = original_payload_sha256
    receipt["prepared_payload_sha256"] = source_payload_sha256
    receipt["payload_hash_mode"] = "ordered_original_plus_content_addressed_prepared"
    receipt["split_current_message"] = split_current_message
    receipt["adaptive_selection"] = adaptive_selection
    receipt["suffix_chars"] = (
        int(os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS", "16000"))
        if split_current_message
        else None
    )
    return staged, receipt


@dataclass
class WrenchWorker:
    """A bounded proposal worker backed by a local model directory."""

    tokenizer: Any
    model: Any | None
    allowed_root: Path

    @classmethod
    def from_pretrained(
        cls,
        model_dir: str | Path,
        *,
        allowed_root: str | Path = ".",
        load_model: bool = True,
        **model_kwargs: Any,
    ) -> "WrenchWorker":
        model_path = Path(model_dir)
        tokenizer = None
        model = None
        if load_model:
            from transformers import AutoModelForImageTextToText, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True,
            )
            import torch

            model_kwargs.setdefault("dtype", torch.bfloat16)
            model = AutoModelForImageTextToText.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True,
                **model_kwargs,
            )
            model.eval()
        root = Path(allowed_root).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"allowed_root is not a directory: {root}")
        return cls(tokenizer=tokenizer, model=model, allowed_root=root)

    def propose(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 256,
        use_mechanical_route: bool = True,
    ) -> dict[str, Any]:
        """Return an accepted proposal or a fail-closed abstention receipt."""

        if not isinstance(messages, list) or not messages:
            return {"status": "abstain", "fallback_reason": "qwen_request_invalid"}
        users = [item.get("content") for item in messages if item.get("role") == "user"]
        users = [content for content in users if isinstance(content, str)]
        prompt = users[-1] if users else ""
        reference_payload = "\n\n".join(users)
        if use_mechanical_route:
            # The latest user message owns the action. The complete user
            # payload remains available as reference evidence for multi-turn
            # conversations, including payloads whose old lookup lives in an
            # earlier message.
            route_suffix_chars = int(os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS", "16000"))
            if route_suffix_chars < 1:
                return {"status": "abstain", "fallback_reason": "qwen_route_suffix_invalid"}
            # A monolithic user message may contain millions of tokens of old
            # lookup data. Only the newest suffix can define the active action.
            # The complete payload remains available to reference_lookup_route
            # for exact historical evidence.
            route_prompt = active_intent_suffix(prompt, suffix_chars=route_suffix_chars)
            mechanical = mechanical_route(route_prompt, allowed_root=self.allowed_root)
            if mechanical is None or mechanical.get("fallback_reason") == "patch_content_missing":
                mechanical = reference_patch_route(reference_payload) or mechanical
            if mechanical is None:
                mechanical = reference_lookup_route(reference_payload)
            if mechanical is not None:
                serialized = json.dumps(mechanical, ensure_ascii=False, separators=(",", ":"))
                if mechanical.get("status") == "abstain":
                    result = dict(mechanical)
                else:
                    result = execute_model_output(
                        serialized,
                        self.allowed_root,
                        request_prompt=route_prompt,
                    )
                result.update(
                    {
                        "backend": "embedded-mechanical",
                        "mechanical_fast_path": True,
                        "raw_model_output": serialized,
                    }
                )
                return result

        if self.model is None:
            return {"status": "abstain", "fallback_reason": "model_not_loaded"}
        if self.tokenizer is None:
            return {"status": "abstain", "fallback_reason": "tokenizer_not_loaded"}
        if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or not 1 <= max_tokens <= 512:
            return {"status": "abstain", "fallback_reason": "qwen_token_limit_invalid"}
        request_messages = add_patch_schema_examples(messages)
        request_messages, prefill_receipt = _dynamic_prefill_messages(request_messages)
        patch_retry_count = 0
        model_calls = 0
        while True:
            prompt_text = self.tokenizer.apply_chat_template(
                request_messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            batch = self.tokenizer(prompt_text, return_tensors="pt", add_special_tokens=False)
            try:
                input_device = next(self.model.parameters()).device
                batch = {key: value.to(input_device) for key, value in batch.items()}
            except StopIteration:
                pass
            model_calls += 1
            output = self.model.generate(
                **batch,
                max_new_tokens=max_tokens,
                do_sample=False,
                use_cache=True,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            )
            generated = output[0, batch["input_ids"].shape[-1] :]
            content = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
            result = execute_model_output(content, self.allowed_root, request_prompt=prompt)
            retryable = result.get("fallback_reason") in {
                "model_output_not_text",
                "model_output_invalid_json",
                "model_output_not_object",
            }
            if not (is_patch_prompt(prompt) and patch_retry_count == 0 and retryable):
                break
            patch_retry_count = 1
            request_messages = add_patch_retry_instruction(request_messages)
        result.update(
            {
                "backend": "transformers",
                "mechanical_fast_path": False,
                "raw_model_output": content,
                "model_calls": model_calls,
            }
        )
        if prefill_receipt is not None:
            result["dynamic_prefill"] = prefill_receipt
        if is_patch_prompt(prompt):
            result["patch_retry_count"] = patch_retry_count
        return result
