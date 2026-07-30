"""Session repository — stores and retrieves chat history lists in Upstash Redis.

This handles the raw storage of multi-turn conversations.
"""

from __future__ import annotations

import json
from typing import Any
import os

from upstash_redis.asyncio import Redis


class SessionRepository:
    """Manages chat session history and user preferences in Redis."""

    # In-memory fallback if Redis is not configured
    _memory_store: dict[str, Any] = {}

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client
        self._ttl = 86400
        # Check if we should use memory fallback
        url = os.getenv("UPSTASH_REDIS_REST_URL", "")
        self._use_memory = "your-upstash" in url or "http" not in url

    def _get_key(self, conversation_id: str) -> str:
        return f"session:{conversation_id}:history"

    def _get_prefs_key(self, conversation_id: str) -> str:
        return f"session:{conversation_id}:preferences"

    async def get_history(self, conversation_id: str) -> list[dict[str, Any]]:
        """Retrieve the raw conversation history list."""
        key = self._get_key(conversation_id)
        if self._use_memory:
            data = self._memory_store.get(key)
        else:
            data = await self._redis.get(key)
            
        if not data:
            return []
            
        # Memory store keeps python objects directly
        if self._use_memory:
            return data
            
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return []

    async def save_history(self, conversation_id: str, history: list[dict[str, Any]]) -> None:
        """Overwrite the conversation history list in Redis."""
        key = self._get_key(conversation_id)
        if self._use_memory:
            self._memory_store[key] = history
        else:
            await self._redis.set(
                key,
                json.dumps(history, ensure_ascii=False),
                ex=self._ttl,
            )

    async def append_message(self, conversation_id: str, role: str, content: str) -> None:
        """Append a single message to the session history."""
        history = await self.get_history(conversation_id)
        history.append({"role": role, "content": content})
        await self.save_history(conversation_id, history)

    async def clear_history(self, conversation_id: str) -> None:
        """Delete the conversation history and preferences."""
        key = self._get_key(conversation_id)
        prefs_key = self._get_prefs_key(conversation_id)
        
        if self._use_memory:
            self._memory_store.pop(key, None)
            self._memory_store.pop(prefs_key, None)
        else:
            await self._redis.delete(key)
            await self._redis.delete(prefs_key)

    async def get_preferences(self, conversation_id: str) -> dict[str, Any]:
        """Retrieve user preference state from Redis."""
        key = self._get_prefs_key(conversation_id)
        
        if self._use_memory:
            data = self._memory_store.get(key)
        else:
            data = await self._redis.get(key)
            
        if not data:
            return {}
            
        if self._use_memory:
            return data
            
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return {}

    async def save_preferences(self, conversation_id: str, prefs: dict[str, Any]) -> None:
        """Save user preference state to Redis."""
        key = self._get_prefs_key(conversation_id)
        
        if self._use_memory:
            self._memory_store[key] = prefs
        else:
            await self._redis.set(
                key,
                json.dumps(prefs, ensure_ascii=False),
                ex=self._ttl,
            )
