from enum import Enum

from pydantic import BaseModel, Field


class ClientActionType(str, Enum):
    """Actions the frontend sends TO the backend"""

    GET_API_TOKEN = "get_api_token"


class ServerActionType(str, Enum):
    """Actions the backend sends TO the frontend UI"""

    GET_API_TOKEN = "get_api_token"


class ChatRequest(BaseModel):
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
    action_type: ClientActionType | None = None


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Natural-language answer to the user's question.")
    endpoints: list["EndpointSnippet"] = Field(
        default_factory=list, description="Extracted API endpoints"
    )
    action_type: ServerActionType | None = None


class EndpointSnippet(BaseModel):
    """A single API endpoint recommended by the assistant."""

    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    url: str = Field(..., description="Full endpoint URL")
    description: str = Field(..., description="What this endpoint does")
    curl_example: str = Field(..., description="Ready-to-use curl command")


class ChatMessage(BaseModel):
    role: str
    text: str
