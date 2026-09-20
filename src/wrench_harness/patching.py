"""Bounded structural prompting for review-only patch proposals."""

from __future__ import annotations

from typing import Any


def add_patch_schema_examples(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Add fixed patch examples only when the current request asks for one."""

    user_indexes = [
        index
        for index, message in enumerate(messages)
        if isinstance(message, dict)
        and message.get("role") == "user"
        and isinstance(message.get("content"), str)
    ]
    if not user_indexes:
        return messages
    last_user_index = user_indexes[-1]
    prompt = str(messages[last_user_index]["content"]).casefold()
    if not any(marker in prompt for marker in ("patch", "diff", "change")):
        return messages
    if any(message.get("role") == "assistant" for message in messages[last_user_index + 1 :]):
        return messages
    augmented = [dict(message) for message in messages]
    for message in augmented:
        if message.get("role") in {"system", "developer"}:
            message["content"] = str(message.get("content", "")) + (
                " For patch_draft, return the complete unified diff including --- and +++ file markers and an @@ hunk header."
            )
            break
    examples: list[dict[str, str]] = [
        {
            "role": "user",
            "content": "Draft a review-only change for README.md and do not apply it.",
        },
        {
            "role": "assistant",
            "content": (
                '{"schema":"wrench.proposal.v1","action":"patch_draft",'
                '"files":["README.md"],"review_only":true,"diff":"--- a/README.md\\n'
                '+++ b/README.md\\n@@ -1 +1 @@\\n-old\\n+new\\n"}'
            ),
        },
        {
            "role": "user",
            "content": "Draft a review-only change for GOAL.md and do not apply it.",
        },
        {
            "role": "assistant",
            "content": (
                '{"schema":"wrench.proposal.v1","action":"patch_draft",'
                '"files":["GOAL.md"],"review_only":true,"diff":"--- a/GOAL.md\\n'
                '+++ b/GOAL.md\\n@@ -1 +1 @@\\n-old\\n+new\\n"}'
            ),
        },
    ]
    return augmented[:last_user_index] + examples + augmented[last_user_index:]


def add_patch_retry_instruction(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Make one bounded corrective retry explicit after malformed patch text."""

    retried = [dict(message) for message in messages]
    for message in retried:
        if message.get("role") in {"system", "developer"}:
            message["content"] = str(message.get("content", "")) + (
                " The previous patch draft was malformed. Retry once and emit one complete JSON object only."
            )
            break
    return retried


def is_patch_prompt(prompt: Any) -> bool:
    return isinstance(prompt, str) and any(
        marker in prompt.casefold() for marker in ("patch", "diff", "change")
    )
