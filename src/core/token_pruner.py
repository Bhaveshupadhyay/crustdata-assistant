"""Token estimation and pruning utilities to manage LLM context windows."""

from __future__ import annotations

from typing import Any


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a string.

    Uses the standard rule of thumb: 1 token ≈ 4 characters in English.
    """
    return len(text) // 4


def prune_history(
    history: list[dict[str, Any]],
    max_tokens: int = 6000,
) -> list[dict[str, Any]]:
    """Prunes chat history from the oldest messages until it fits within max_tokens.

    Always preserves the structure (alternating user/model) if possible.
    """
    total_tokens = 0
    pruned: list[dict[str, Any]] = []

    # Iterate backwards (from newest to oldest) to prioritize recent messages
    for msg in reversed(history):
        msg_tokens = estimate_tokens(msg.get("content", "")) + 10
        if total_tokens + msg_tokens > max_tokens:
            break
        pruned.insert(0, msg)
        total_tokens += msg_tokens

    return pruned
