"""Pydantic schemas for the chat API request / response cycle."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming user message."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's natural-language question about Crustdata APIs.",
        examples=["How do I search for job data?", "Show me how to enrich a company by domain"],
    )
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID for multi-turn context (future use).",
    )


class EndpointSnippet(BaseModel):
    """A single API endpoint recommended by the assistant."""

    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    url: str = Field(..., description="Full endpoint URL")
    description: str = Field(..., description="What this endpoint does")
    curl_example: str = Field(..., description="Ready-to-use curl command")


class ChatResponse(BaseModel):
    """The assistant's reply, including a natural-language explanation
    and any relevant endpoint details."""

    answer: str = Field(..., description="Natural-language answer to the user's question.")
    endpoints: list[EndpointSnippet] = Field(
        default_factory=list,
        description="Relevant API endpoints with curl examples.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Links to the official documentation pages used.",
    )


class HealthResponse(BaseModel):
    """Health-check payload."""

    status: str = "ok"
    version: str
