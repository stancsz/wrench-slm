"""Model-package worker API for bounded Wrench proposals.

The worker keeps the deterministic toolbelt inside the downloaded model
directory. High-confidence mechanical requests do not spend a model pass.
Ambiguous requests use the standard Transformers model and still pass through
the same strict parser and verifier before a proposal is returned.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .mechanical import mechanical_route
from .core import execute_model_output
from .patching import add_patch_retry_instruction, add_patch_schema_examples, is_patch_prompt


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
        prompt = users[-1] if users and isinstance(users[-1], str) else ""
        if use_mechanical_route:
            mechanical = mechanical_route(prompt)
            if mechanical is not None:
                serialized = json.dumps(mechanical, ensure_ascii=False, separators=(",", ":"))
                if mechanical.get("status") == "abstain":
                    result = dict(mechanical)
                else:
                    result = execute_model_output(
                        serialized,
                        self.allowed_root,
                        request_prompt=prompt,
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
        patch_retry_count = 0
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
        result.update({"backend": "transformers", "mechanical_fast_path": False, "raw_model_output": content})
        if is_patch_prompt(prompt):
            result["patch_retry_count"] = patch_retry_count
        return result
