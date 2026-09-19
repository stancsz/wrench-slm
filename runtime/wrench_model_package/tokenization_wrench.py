"""HF tokenizer entrypoint that stages long chat payloads inside the model package.

This keeps the public API model-shaped: callers invoke the normal tokenizer
chat-template path, while the package performs deterministic mechanical
prefill before tokenization. It is not a substitute for a backend-native
attention implementation and it never calls an LLM.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from transformers import PreTrainedTokenizerFast

try:
    # Transformers dynamic modules preserve this relative dependency when the
    # model directory is downloaded from the Hub.
    from .wrench_prefill import MechanicalPrefillIndex, build_dynamic_prefill
    from .wrench_mechanical import mechanical_route
except ImportError:
    _SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src"
    if str(_SOURCE_ROOT) not in sys.path:
        sys.path.insert(0, str(_SOURCE_ROOT))
    from wrench_harness.prefill import MechanicalPrefillIndex, build_dynamic_prefill
    from wrench_harness.mechanical import mechanical_route


class WrenchTokenizer(PreTrainedTokenizerFast):
    """A normal HF tokenizer with bundled Wrench long-context staging."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._wrench_mechanical_index = MechanicalPrefillIndex()
        self.last_wrench_prefill_receipt: dict[str, Any] | None = None

    def apply_chat_template(self, conversation: Any, *args: Any, **kwargs: Any) -> Any:
        if (
            isinstance(conversation, list)
            and conversation
            and all(isinstance(message, dict) and isinstance(message.get("content"), str) for message in conversation)
            and any(message.get("role") == "user" for message in conversation)
        ):
            self._wrench_mechanical_index.add_all(conversation)
            conversation, receipt = build_dynamic_prefill(
                conversation,
                model_prefill_budget=64_000,
                hot_token_budget=48_000,
                reference_index_budget=16_000,
                mechanical_index=self._wrench_mechanical_index,
            )
            self.last_wrench_prefill_receipt = receipt
        return super().apply_chat_template(conversation, *args, **kwargs)

    def wrench_lookup(self, reference_id: str) -> str:
        """Expand one reference card explicitly, outside the model attention pass."""

        for entry in self._wrench_mechanical_index._entries_by_digest.values():
            if entry["card"]["reference_id"] == reference_id:
                return entry["content"]
        raise KeyError(reference_id)

    def wrench_mechanical_route(self, prompt: str) -> dict[str, Any] | None:
        """Return a high-confidence proposal without a model call, if any."""

        return mechanical_route(prompt)
