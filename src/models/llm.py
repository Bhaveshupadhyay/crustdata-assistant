from typing import Any

from pydantic import BaseModel, Field

from src.schema.chat import EndpointSnippet, ServerActionType


class DocAgentResponse(BaseModel):
    """Structured response format expected from the Doc Agent."""

    explanation: str = Field(description="Markdown explanation answering the user's question.")
    endpoints: list[EndpointSnippet] = Field(
        description="List of relevant API endpoints.", default_factory=list
    )


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any]
    id: str | None = None
    thought_signature_hex: str | None = None


class LLMResponse(BaseModel):
    text: str = Field(description="Answer the question")
    action: ServerActionType | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
