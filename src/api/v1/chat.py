from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.dependencies import get_assistant_service
from src.schema.chat import ChatRequest, ChatResponse
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
    return await assistant.answer_question(
        request.message,
        conversation_id=request.conversation_id,
    )