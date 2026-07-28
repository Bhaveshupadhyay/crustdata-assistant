"""Chat router — HTTP API layer for the Crustdata AI Assistant.

This module is intentionally thin: it validates the request, delegates to the
AssistantService, and serialises the response. No business logic here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.dependencies import get_assistant_service
from src.models.chat import ChatRequest, ChatResponse
from src.services.assistant_service import AssistantService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Ask the Crustdata assistant a question",
    description=(
        "Send a natural-language question about Crustdata APIs and receive "
        "a structured response with an explanation, relevant endpoints, "
        "and ready-to-use curl examples."
    ),
)
async def chat(
    request: ChatRequest,
    assistant: AssistantService = Depends(get_assistant_service),
) -> ChatResponse:
    """Main chat endpoint — the user asks a question, the assistant answers."""
    try:
        return await assistant.answer_question(
            request.message,
            conversation_id=request.conversation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Assistant error: {exc}") from exc


@router.get(
    "/endpoints",
    summary="List available Crustdata API endpoints",
    description=(
        "Returns a catalogue of all known Crustdata API endpoints, "
        "optionally filtered by category."
    ),
)
async def list_endpoints(
    category: str | None = Query(
        default=None,
        description="Filter by category: company, person, job, web, watcher, batch",
    ),
    assistant: AssistantService = Depends(get_assistant_service),
) -> list[dict]:
    """Catalogue endpoint — useful for debugging and discovery."""
    return await assistant.list_endpoints(category)
