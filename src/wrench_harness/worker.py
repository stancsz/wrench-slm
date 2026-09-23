"""Model-package worker API for bounded Wrench proposals.

The worker keeps the deterministic toolbelt inside the downloaded model
directory. High-confidence mechanical requests do not spend a model pass.
Ambiguous requests use the standard Transformers model and still pass through
the same strict parser and verifier before a proposal is returned.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .mechanical import active_intent_suffix, mechanical_route, reference_lookup_route, reference_patch_route
from .core import execute_model_output
from .patching import (
    add_bounded_repair_instruction,
    add_patch_retry_instruction,
    add_patch_schema_examples,
    is_patch_prompt,
)
from .ttc import enforce_ttc
from .handoff import build_advisor_handoff
from .prefill import (
    FirstLayerContextGate,
    MechanicalPrefillIndex,
    _estimate_token_count,
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
    # Keep the worker and prefill index on the same bounded-sampling policy.
    return _estimate_token_count(value)


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
    # Adaptive policy only needs the active intent. Case-folding a complete
    # 4M payload here allocates and scans tens of megabytes before the actual
    # reducer starts, even though historical material is reference-only.
    latest = (
        active_intent_suffix(users[-1], suffix_chars=16_000).casefold()
        if users
        else ""
    )
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
    *,
    mechanical_index: MechanicalPrefillIndex | None = None,
    original_payload_sha256: str | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    """Keep monster payloads losslessly indexed but bounded for model work."""

    budget = int(os.environ.get("WRENCH_MODEL_PREFILL_BUDGET", "64000"))
    original_payload_sha256 = original_payload_sha256 or ordered_payload_sha256(messages)
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
    index = mechanical_index or MechanicalPrefillIndex()
    index.add_all(prepared_messages)
    context_gate = FirstLayerContextGate(
        working_context_tokens=budget,
        hot_context_tokens=hot_budget,
        reference_card_tokens=reference_budget,
    )
    source_payload_sha256 = index.payload_sha256(prepared_messages)
    try:
        staged, receipt = context_gate.compact(
            prepared_messages,
            mechanical_index=index,
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


def _mechanical_context_gate_receipt(
    messages: list[dict[str, str]],
    *,
    active_prompt: str,
    reference_payload: str,
    route_source: str,
    started: float,
) -> dict[str, Any]:
    """Record the first-layer reduction used by the no-model fast path.

    The mechanical lane keeps the newest intent as its hot span and scans
    historical content only for exact bounded lookup or patch evidence. The
    same hash-bound receipt family is used by the model prefill gate.
    """

    content_values = [
        message.get("content", "")
        for message in messages
        if isinstance(message, dict) and isinstance(message.get("content"), str)
    ]
    raw_input_tokens = sum(_estimated_tokens(value) for value in content_values)
    effective_tokens = _estimated_tokens(active_prompt)
    selected_reference_spans = 1 if route_source in {"reference_patch", "reference_lookup"} else 0
    return {
        "schema": "wrench.first-layer-context-gate.v1",
        "stage": "mechanical_fast_pruner_cherrypicker",
        "strategy": "latest_intent_plus_exact_lookup",
        "raw_context_limit_tokens": 4_000_000,
        "raw_input_tokens": raw_input_tokens,
        "effective_working_context_tokens": effective_tokens,
        "working_context_budget_tokens": 64_000,
        "selected_hot_spans": 1 if active_prompt else 0,
        "selected_reference_spans": selected_reference_spans,
        "omitted_reference_spans": max(0, len(content_values) - 1 - selected_reference_spans),
        "route_source": route_source,
        "raw_payload_sha256": ordered_payload_sha256(messages),
        "raw_payload_hash_bound": True,
        "native_input_claim": False,
        "gate_latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "reference_scan_tokens": _estimated_tokens(reference_payload),
    }


def _attach_advisor_handoff(
    result: dict[str, Any],
    messages: list[dict[str, str]],
    *,
    working_messages: list[dict[str, str]] | None = None,
    prefill_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach a bounded stronger-model packet to an abstention only."""

    if result.get("status") != "abstain":
        return result
    try:
        result["advisor_handoff"] = build_advisor_handoff(
            messages,
            result=result,
            working_messages=working_messages,
            prefill_receipt=prefill_receipt,
        )
    except Exception as exc:
        # The original fail-closed result remains authoritative. A handoff
        # packaging error must not turn into raw-payload forwarding or a new
        # execution path.
        result["advisor_handoff"] = {
            "schema": "wrench.advisor-handoff.v1",
            "handoff_required": True,
            "authority": "proposal_only_no_mutation",
            "frontier_policy": {
                "max_frontier_calls": 2,
                "return_each_result_to_wrench_verifier": True,
                "preserve_raw_payload_out_of_band": True,
            },
            "error": type(exc).__name__,
        }
    return result


@dataclass
class WrenchWorker:
    """A bounded proposal worker backed by a local model directory."""

    tokenizer: Any
    model: Any | None
    allowed_root: Path
    prefill_index: MechanicalPrefillIndex = field(default_factory=MechanicalPrefillIndex)
    intent_safety_gate: Any | None = None
    binary_abstain_gate: Any | None = None

    @classmethod
    def from_pretrained(
        cls,
        model_dir: str | Path,
        *,
        allowed_root: str | Path = ".",
        load_model: bool = True,
        prefill_cache_bytes: int | None = None,
        binary_abstain_artifact: str | Path | None = None,
        **model_kwargs: Any,
    ) -> "WrenchWorker":
        model_path = Path(model_dir)
        tokenizer = None
        model = None
        intent_safety_gate = None
        binary_abstain_gate = None
        if binary_abstain_artifact is not None and not load_model:
            raise ValueError("the Qwen binary head requires the existing Qwen model")
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
            # The portable worker must use the same device placement as the
            # verified standalone evaluator. Without this, load_model=True
            # silently leaves an 8 GB BF16 checkpoint on CPU and turns the
            # ambiguous-request path into a non-production fallback. A
            # caller can pin WRENCH_MODEL_DEVICE=cpu or an explicit CUDA
            # device. Respect a pre-existing device map because Accelerate
            # owns placement in that mode.
            if not getattr(model, "hf_device_map", None) and "device_map" not in model_kwargs:
                requested_device = os.environ.get("WRENCH_MODEL_DEVICE", "auto").strip()
                if requested_device.casefold() == "auto":
                    requested_device = "cuda" if torch.cuda.is_available() else "cpu"
                model.to(requested_device)
            model.eval()
            if binary_abstain_artifact is not None:
                from .qwen_abstain import QwenAbstainGate

                binary_abstain_gate = QwenAbstainGate.from_artifact(
                    binary_abstain_artifact, model=model, tokenizer=tokenizer,
                    model_dir=model_path,
                )
            if os.environ.get("WRENCH_INTENT_SAFETY_GATE", "0").casefold() in {"1", "true", "on", "yes"}:
                artifact = Path(
                    os.environ.get(
                        "WRENCH_INTENT_SAFETY_GATE_ARTIFACT",
                        str(model_path / "wrench-intent-router.pt"),
                    )
                )
                if not artifact.is_file():
                    raise ValueError(f"intent safety gate enabled but sidecar is missing: {artifact}")
                from .intent_safety_gate import IntentSafetyGate

                intent_safety_gate = IntentSafetyGate.from_artifact(
                    artifact,
                    model=model,
                    tokenizer=tokenizer,
                )
        root = Path(allowed_root).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"allowed_root is not a directory: {root}")
        return cls(
            tokenizer=tokenizer,
            model=model,
            allowed_root=root,
            prefill_index=MechanicalPrefillIndex(max_bytes=prefill_cache_bytes),
            intent_safety_gate=intent_safety_gate,
            binary_abstain_gate=binary_abstain_gate,
        )

    def classify_abstention(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Classify with the shared Qwen backbone, without proposing or executing."""
        if self.binary_abstain_gate is None:
            return {"decision": "abstain", "reason": "binary_head_not_loaded",
                    "authority": "abstain_only", "generated_tokens": 0}
        try:
            receipt = self.binary_abstain_gate.check_messages(messages)
            if not isinstance(receipt, dict) or receipt.get("decision") not in {"abstain", "not_abstain"}:
                raise ValueError("invalid binary head receipt")
            return receipt
        except Exception as exc:
            return {"decision": "abstain", "reason": "gate_error",
                    "error": type(exc).__name__, "authority": "abstain_only",
                    "generated_tokens": 0}

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
        binary_receipt = None
        if self.binary_abstain_gate is not None:
            binary_receipt = self.classify_abstention(messages)
            if binary_receipt["decision"] != "not_abstain":
                return _attach_advisor_handoff({
                    "status": "abstain", "fallback_reason": "binary_abstain_gate_rejected",
                    "binary_abstain_gate": binary_receipt,
                }, messages)
        def finish(result):
            if binary_receipt is not None:
                result["binary_abstain_gate"] = binary_receipt
            return _attach_advisor_handoff(result, messages)

        users = [item.get("content") for item in messages if item.get("role") == "user"]
        users = [content for content in users if isinstance(content, str)]
        prompt = users[-1] if users else ""
        reference_payload = "\n\n".join(users)
        try:
            verifier_suffix_chars = int(
                os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS", "16000")
            )
        except ValueError:
            verifier_suffix_chars = 16_000
        verifier_prompt = active_intent_suffix(
            prompt,
            suffix_chars=max(1, verifier_suffix_chars),
        )
        if use_mechanical_route:
            gate_started = time.perf_counter()
            # The latest user message owns the action. The complete user
            # payload remains available as reference evidence for multi-turn
            # conversations, including payloads whose old lookup lives in an
            # earlier message.
            route_suffix_chars = verifier_suffix_chars
            if route_suffix_chars < 1:
                return finish({"status": "abstain", "fallback_reason": "qwen_route_suffix_invalid"})
            # A monolithic user message may contain millions of tokens of old
            # lookup data. Only the newest suffix can define the active action.
            # The complete payload remains available to reference_lookup_route
            # for exact historical evidence.
            route_prompt = verifier_prompt
            mechanical = mechanical_route(route_prompt, allowed_root=self.allowed_root)
            route_source = "latest_intent"
            # Some native harnesses serialize one logical turn as several
            # consecutive user messages before the first assistant message.
            # If the newest wrapper message produces only an abstention, keep
            # the fail-closed default but look backward for an unambiguous
            # read/search intent from that same pre-assistant bundle. Normal
            # multi-turn conversations contain an assistant/tool boundary and
            # therefore retain strict newest-intent ownership.
            has_assistant_boundary = any(
                isinstance(item, dict) and item.get("role") in {"assistant", "tool"}
                for item in messages
            )
            if len(users) > 1 and not has_assistant_boundary:
                for bundle_prompt in users:
                    earlier_route_prompt = active_intent_suffix(
                        bundle_prompt,
                        suffix_chars=max(1, route_suffix_chars),
                    )
                    earlier_mechanical = mechanical_route(
                        earlier_route_prompt,
                        allowed_root=self.allowed_root,
                    )
                    if (
                        earlier_mechanical is not None
                        and earlier_mechanical.get("status") != "abstain"
                    ):
                        mechanical = earlier_mechanical
                        route_prompt = earlier_route_prompt
                        verifier_prompt = earlier_route_prompt
                        route_source = "pre_assistant_intent_bundle"
                        break
            if mechanical is None or mechanical.get("fallback_reason") == "patch_content_missing":
                reference_patch = reference_patch_route(reference_payload)
                if reference_patch is not None:
                    mechanical = reference_patch
                    route_source = "reference_patch"
            if mechanical is None:
                reference_lookup = reference_lookup_route(reference_payload)
                if reference_lookup is not None:
                    mechanical = reference_lookup
                    route_source = "reference_lookup"
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
                    if result.get("status") == "accepted":
                        result = enforce_ttc(
                            mechanical,
                            route_prompt,
                            result,
                            context_pressure=len(reference_payload) > 256_000,
                        )
                result.update(
                    {
                        "backend": "embedded-mechanical",
                        "mechanical_fast_path": True,
                        "raw_model_output": serialized,
                        "context_gate": _mechanical_context_gate_receipt(
                            messages,
                            active_prompt=route_prompt,
                            reference_payload=reference_payload,
                            route_source=route_source,
                            started=gate_started,
                        ),
                    }
                )
                _attach_advisor_handoff(result, messages)
                if binary_receipt is not None:
                    result["binary_abstain_gate"] = binary_receipt
                return result

        if self.model is None:
            return finish(
                {"status": "abstain", "fallback_reason": "model_not_loaded"},
            )
        if self.tokenizer is None:
            return finish(
                {"status": "abstain", "fallback_reason": "tokenizer_not_loaded"},
            )
        if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or not 1 <= max_tokens <= 512:
            return finish(
                {"status": "abstain", "fallback_reason": "qwen_token_limit_invalid"},
            )
        request_messages = add_patch_schema_examples(messages)
        request_messages, prefill_receipt = _dynamic_prefill_messages(
            request_messages,
            mechanical_index=self.prefill_index,
        )
        patch_retry_count = 0
        repair_pass_count = 0
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
            result = execute_model_output(
                content,
                self.allowed_root,
                request_prompt=verifier_prompt,
            )
            if result.get("status") == "accepted":
                try:
                    proposal = json.loads(content)
                except json.JSONDecodeError:
                    proposal = None
                result = enforce_ttc(
                    proposal,
                    verifier_prompt,
                    result,
                    context_pressure=prefill_receipt is not None,
                )
            if self.intent_safety_gate is not None:
                try:
                    gate_receipt = self.intent_safety_gate.check(request_messages, content)
                except Exception as exc:
                    gate_receipt = {
                        "schema": "wrench.intent-safety-gate.v1",
                        "gate_passed": False,
                        "authority": "abstain_only",
                        "error": type(exc).__name__,
                    }
                result["intent_safety_gate"] = gate_receipt
                if result.get("status") == "accepted" and not gate_receipt.get("gate_passed"):
                    result = {
                        "status": "abstain",
                        "fallback_reason": "intent_safety_gate_rejected",
                        "intent_safety_gate": gate_receipt,
                    }
            retryable = result.get("fallback_reason") in {
                "model_output_not_text",
                "model_output_invalid_json",
                "model_output_not_object",
            }
            if repair_pass_count > 0 or not retryable:
                break
            repair_pass_count = 1
            if is_patch_prompt(prompt):
                patch_retry_count = 1
                request_messages = add_patch_retry_instruction(request_messages)
            else:
                request_messages = add_bounded_repair_instruction(request_messages, str(result.get("fallback_reason")))
        result.update(
            {
                "backend": "transformers",
                "mechanical_fast_path": False,
                "raw_model_output": content,
                "model_calls": model_calls,
                "model_device": str(next(self.model.parameters()).device),
            }
        )
        if binary_receipt is not None:
            result["binary_abstain_gate"] = binary_receipt
        if prefill_receipt is not None:
            result["dynamic_prefill"] = prefill_receipt
            result["dynamic_prefill"]["cache"] = self.prefill_index.stats()
        if is_patch_prompt(prompt):
            result["patch_retry_count"] = patch_retry_count
        if repair_pass_count:
            result["repair_pass_count"] = repair_pass_count
        _attach_advisor_handoff(
            result,
            messages,
            working_messages=request_messages,
            prefill_receipt=prefill_receipt,
        )
        return result
