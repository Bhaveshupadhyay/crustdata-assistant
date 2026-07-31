"""Session repository for chat history and preferences with Redis caching."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import sessionmaker

from src.core.cache import cached, insert_redis_data
from src.models.session import ChatSession

logger = logging.getLogger(__name__)


class SessionRepository:
    """Manages chat session history and user preferences in Postgres with Redis caching."""

    def __init__(self, session_maker: sessionmaker) -> None:
        self._session_maker = session_maker

    @cached(namespace="session_history", key=["conversation_id"])
    async def get_history(self, conversation_id: str) -> list[dict[str, Any]]:
        """Retrieve the raw conversation history list from Postgres (cached)."""
        with self._session_maker() as session:
            db_session = (
                session.query(ChatSession).filter_by(conversation_id=conversation_id).first()
            )
            if db_session and db_session.history:
                return db_session.history
            return []

    async def save_history(self, conversation_id: str, history: list[dict[str, Any]]) -> None:
        """Overwrite the conversation history list in Postgres and invalidate cache."""
        with self._session_maker() as session:
            db_session = (
                session.query(ChatSession).filter_by(conversation_id=conversation_id).first()
            )
            if not db_session:
                db_session = ChatSession(conversation_id=conversation_id)
                session.add(db_session)
            db_session.history = history
            session.commit()

        # Update cache directly so the next read is instant
        await insert_redis_data(key=conversation_id, namespace="session_history", data=history)

    async def append_message(self, conversation_id: str, role: str, content: str) -> None:
        """Append a single message to the session history."""
        history = await self.get_history(conversation_id)
        history.append({"role": role, "content": content})
        await self.save_history(conversation_id, history)

    async def clear_history(self, conversation_id: str) -> None:
        """Delete the conversation history and preferences."""
        with self._session_maker() as session:
            db_session = (
                session.query(ChatSession).filter_by(conversation_id=conversation_id).first()
            )
            if db_session:
                session.delete(db_session)
                session.commit()

        # We should also invalidate cache but setting to empty clears it
        await insert_redis_data(key=conversation_id, namespace="session_history", data=[])
        await insert_redis_data(key=conversation_id, namespace="session_prefs", data={})

    @cached(namespace="session_prefs", key=["conversation_id"])
    async def get_preferences(self, conversation_id: str) -> dict[str, Any]:
        """Retrieve user preference state from Postgres (cached)."""
        with self._session_maker() as session:
            db_session = (
                session.query(ChatSession).filter_by(conversation_id=conversation_id).first()
            )
            if db_session and db_session.preferences:
                return db_session.preferences
            return {}

    async def save_preferences(self, conversation_id: str, prefs: dict[str, Any]) -> None:
        """Save user preference state to Postgres and invalidate cache."""
        with self._session_maker() as session:
            db_session = (
                session.query(ChatSession).filter_by(conversation_id=conversation_id).first()
            )
            if not db_session:
                db_session = ChatSession(conversation_id=conversation_id)
                session.add(db_session)
            db_session.preferences = prefs
            session.commit()

        # Update cache
        await insert_redis_data(key=conversation_id, namespace="session_prefs", data=prefs)
