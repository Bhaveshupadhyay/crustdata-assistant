from __future__ import annotations

from functools import lru_cache

from src.core.client import get_postgres_client
from src.repositories.session_repository import SessionRepository
from src.services.assistant_service import AssistantService
from src.services.llm_service import GeminiLlmService, LlmService



@lru_cache(maxsize=1)
def get_llm_service() -> LlmService:
    """Dependency provider that returns the configured concrete LlmService instance."""
    return GeminiLlmService()

@lru_cache(maxsize=1)
def get_session_repo() -> SessionRepository:
    """Dependency provider that returns the cached SessionRepository instance."""
    return SessionRepository(session_maker=get_postgres_client())


@lru_cache(maxsize=1)
def get_assistant_service() -> AssistantService:
    """Dependency provider that returns the cached AssistantService instance."""
    return AssistantService(
        llm_service=get_llm_service(),
        session_repo=get_session_repo(),
    )
