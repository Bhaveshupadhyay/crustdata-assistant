"""Dependency Injection container for the Crustdata AI Assistant.

Wires together the data sources, repository, and services layer.
"""

from __future__ import annotations

from functools import lru_cache

from src.core.client import get_redis_client
from src.repositories.knowledge_repository import _ENDPOINTS, KnowledgeRepository
from src.repositories.session_repository import SessionRepository
from src.services.assistant_service import AssistantService
from src.services.llm_service import GeminiLlmService, LlmService

_db = _ENDPOINTS


@lru_cache(maxsize=1)
def get_llm_service() -> LlmService:
    """Dependency provider that returns the configured concrete LlmService instance."""
    return GeminiLlmService()


@lru_cache(maxsize=1)
def get_knowledge_repo() -> KnowledgeRepository:
    """Dependency provider that returns the cached KnowledgeRepository instance."""
    return KnowledgeRepository(db=_db)


@lru_cache(maxsize=1)
def get_session_repo() -> SessionRepository:
    """Dependency provider that returns the cached SessionRepository instance."""
    return SessionRepository(redis_client=get_redis_client())


@lru_cache(maxsize=1)
def get_assistant_service() -> AssistantService:
    """Dependency provider that returns the cached AssistantService instance."""
    return AssistantService(
        knowledge_repo=get_knowledge_repo(),
        llm_service=get_llm_service(),
        session_repo=get_session_repo(),
    )
